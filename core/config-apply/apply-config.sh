#!/bin/sh
# Copies DIAL Core entities (models, applications, interceptors, API keys, roles, ...) from
# JSON files into Core's storage through POST /v1/admin/apply, then exits.
#
# Each file is applied once and listed in STATE_FILE. Later starts skip it, so changes made
# afterwards in DIAL Admin or through Core's API are kept. A file holds either Core config
# sections (models, applications, ...), stored as <section>/platform/<name>, or a
# {"manifests": [...]} bundle, which is sent as it is.
#
# Env:
#   API_KEY       (required) key with the admin role (must match access.admin.rules). It must
#                 come from a file that Core reads itself: Core's storage is empty before the
#                 first apply.
#   CONFIG_FILES  (required) space-separated paths, relative to the working directory
#   CORE_URL      default http://core:8080
#   STATE_FILE    default core-data/core-config-apply.json   delete it to apply all files again
#   WAIT_TIMEOUT  default 120   seconds to wait for Core /health
#
# Exit codes: 0 applied or nothing left to apply, 1 any failure.
set -eu

CORE_URL="${CORE_URL:-http://core:8080}"
STATE_FILE="${STATE_FILE:-core-data/core-config-apply.json}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-120}"
: "${API_KEY:?API_KEY is required}"
: "${CONFIG_FILES:?CONFIG_FILES is required}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
BODY="$TMP/body.json"
MANIFESTS="$TMP/manifests.json"

# Config file sections -> manifest kinds, and the settings fields that form the `Settings` manifest.
JQ_LIB='
def kinds: {
    models: "Model", applications: "Application", toolsets: "ToolSet", interceptors: "Interceptor",
    translators: "Translator", roles: "Role", keys: "Key", routes: "Route"
};
def settings: ["globalInterceptors", "retriableErrorCodes", "rateLimitSchedule", "spendingLimits"];
'

log() { echo "[core-config-apply] $*"; }
die() { log "ERROR: $*" >&2; exit 1; }

wait_for_core() {
    log "waiting for Core at $CORE_URL (up to ${WAIT_TIMEOUT}s)"
    waited=0
    until [ "$(curl -s -o /dev/null -w '%{http_code}' "$CORE_URL/health" || true)" = "200" ]; do
        [ "$waited" -lt "$WAIT_TIMEOUT" ] || die "Core is not healthy after ${WAIT_TIMEOUT}s"
        sleep 2
        waited=$((waited + 2))
    done
}

# applied_at FILE -> prints when FILE was applied, empty if never
applied_at() {
    [ -f "$STATE_FILE" ] || return 0
    jq -r --arg file "$1" '.[$file].appliedAt // empty' "$STATE_FILE"
}

# record_applied FILE SHA256 -> adds FILE and the entities from the apply response in $BODY
record_applied() {
    [ -f "$STATE_FILE" ] || echo '{}' > "$STATE_FILE"
    jq --arg file "$1" --arg sha "$2" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --slurpfile response "$BODY" \
        '.[$file] = {appliedAt: $at, sha256: $sha, entities: [$response[0].results[].entityId]}' \
        "$STATE_FILE" > "$STATE_FILE.tmp"
    mv "$STATE_FILE.tmp" "$STATE_FILE"
}

# apply FILE -> POSTs FILE's entities to Core as manifests
apply() {
    jq "$JQ_LIB"'
        . as $file
        | if has("manifests") then . else {manifests: (
            [ keys_unsorted[] | select(kinds[.]) as $type
              | $file[$type] | keys_unsorted[] as $name
              | {kind: kinds[$type], name: "\($type)/platform/\($name)", spec: $file[$type][$name]}
              # A key in a config file is named by its secret; a stored key holds it in `key`.
              | if .kind == "Key" then .spec.key //= $name else . end ]
            + if any(settings[]; . as $field | $file | has($field)) then
                [{kind: "Settings", name: "settings/platform/global",
                  spec: ($file | with_entries(select(.key | IN(settings[]))))}]
              else [] end
        )} end' "$1" > "$MANIFESTS"

    log "$1: applying $(jq '.manifests | length' "$MANIFESTS") entities"
    code="$(curl -sS -o "$BODY" -w '%{http_code}' -X POST -H "API-KEY: $API_KEY" \
        -H 'Content-Type: application/json' --data-binary "@$MANIFESTS" "$CORE_URL/v1/admin/apply" || true)"
    case "$code" in
        200)
            log "$1: $(jq -c '{applied, failed}' "$BODY")"
            jq -r '.results[] | select(.status == "APPLIED_INVALID")
                | "  WARNING \(.entityId): stored, but refers to entities that Core does not have"' "$BODY"
            if [ "$(jq '.failed // 0' "$BODY")" -gt 0 ]; then
                jq -r '.results[] | select(.status == "FAILED") | "  FAILED \(.entityId): \(.error)"' "$BODY" >&2
                die "$1: some entities failed, see above; fix the file and start this service again"
            fi
            ;;
        422)
            failures="$(jq -r '.results[] | select(.status == "FAILED") | "  \(.entityId): \(.error)"' \
                "$BODY" 2>/dev/null || true)"
            if [ -n "$failures" ]; then echo "$failures" >&2; else cat "$BODY" >&2; echo >&2; fi
            die "$1: precheck failed, nothing was written"
            ;;
        000) die "cannot reach Core at $CORE_URL" ;;
        401) die "401, API key is unknown to Core" ;;
        403) die "403, API key has no admin access (check access.admin.rules and the key's role)" ;;
        *)
            cat "$BODY" >&2; echo >&2
            die "$1: unexpected HTTP status $code"
            ;;
    esac
}

core_ready=false
for file in $CONFIG_FILES; do
    [ -r "$file" ] || die "config file not found: $file"
    # Shows jq's parse error (with the line and column) for a broken file.
    err="$(jq -e 'type == "object"' "$file" 2>&1 >/dev/null)" || die "$file: ${err:-must hold a JSON object}"
    if jq -e 'has("manifests")' "$file" > /dev/null; then
        jq -e 'keys == ["manifests"] and (.manifests | type == "array")' "$file" > /dev/null \
            || die "$file: a manifest bundle must contain only a manifests array"
    else
        unsupported="$(jq -r "$JQ_LIB"'keys_unsorted - (kinds | keys) - settings | join(", ")' "$file")"
        [ -z "$unsupported" ] || die "$file: the apply API does not take $unsupported; put it in a file that Core reads"
    fi
    sha="$(sha256sum "$file" | cut -d' ' -f1)"

    at="$(applied_at "$file")"
    if [ -n "$at" ]; then
        log "$file: applied at $at, skipping"
        if [ "$(jq -r --arg file "$file" '.[$file].sha256' "$STATE_FILE")" != "$sha" ]; then
            log "$file: changed since then; Core keeps what was applied. To apply all files again, delete $STATE_FILE"
        fi
        continue
    fi

    $core_ready || { wait_for_core; core_ready=true; }
    apply "$file"
    record_applied "$file" "$sha"
done
log "done"
