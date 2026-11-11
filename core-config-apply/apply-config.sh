#!/bin/sh
# Applies DIAL Core config files (models, applications, keys, roles, ...) to Core's storage
# through POST /v1/admin/apply, once per file, and lists every applied file in STATE_FILE.
#
# CONFIG_FILES accepts config objects or /v1/admin/apply manifest bundles, applied in order.
# A file that STATE_FILE already lists is skipped, so
# changes made later through Core's API or DIAL Admin are kept. As with Core's own
# `aidial.config.files`, each file deep-merges into the previous ones (arrays concatenate):
# a file may extend an entity of an earlier file, which is then applied with the merged result.
#
# Env:
#   API_KEY       (required) key with the admin role (must match access.admin.rules). It must
#                 come from Core's file config: Core's storage is empty before the first apply.
#   CONFIG_FILES  (required) space-separated paths, relative to the working directory
#   CORE_URL      default http://core:8080
#   STATE_FILE    default core-data/core-config-apply.json   delete it to apply all files again
#   WAIT_TIMEOUT  default 120   seconds to wait for Core /health
#
# Stored sample models also migrate standalone adapter URLs to Model Provider.
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
MERGED="$TMP/merged.json"
echo '{}' > "$MERGED"

# Config file sections -> manifest kinds, the settings fields that form the `Settings` manifest,
# and the merge Core uses for its config files.
JQ_LIB='
def kinds: {
    models: "Model", applications: "Application", toolsets: "ToolSet", interceptors: "Interceptor",
    translators: "Translator", roles: "Role", keys: "Key", routes: "Route"
};
def settings: ["globalInterceptors", "retriableErrorCodes", "rateLimitSchedule", "spendingLimits"];
def merge($a; $b):
    if ($a | type) == "object" and ($b | type) == "object" then
        reduce ($b | keys_unsorted[]) as $k ($a; .[$k] = merge($a[$k]; $b[$k]))
    elif ($a | type) == "array" and ($b | type) == "array" then $a + $b
    else $b end;
'

log() { echo "[core-config-apply] $*"; }
die() { log "ERROR: $*" >&2; exit 1; }

# request METHOD URL [curl args...] -> prints HTTP status, response body goes to $BODY
request() {
    method="$1"; url="$2"; shift 2
    : > "$BODY"
    curl -sS -o "$BODY" -w '%{http_code}' -X "$method" -H "API-KEY: $API_KEY" "$@" "$url" || true
}

# Fails on 401/403/other with a hint, so a bad key is reported as such.
check_status() {
    case "$1" in
        000) die "$2: cannot reach Core at $CORE_URL" ;;
        401) die "$2: 401, API key is unknown to Core" ;;
        403) die "$2: 403, API key has no admin access (check access.admin.rules and the key's roles)" ;;
        *) die "$2: unexpected HTTP status $1" ;;
    esac
}

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

# apply FILE -> POSTs the manifests of FILE's entities, with their specs from the merged config
apply() {
    jq -s "$JQ_LIB"'
        .[0] as $merged | .[1] as $file
        | if $file | has("manifests") then $file else {manifests: (
            [ $file | keys_unsorted[] | select(kinds[.]) as $type
              | $file[$type] | keys_unsorted[] as $name
              | {kind: kinds[$type], name: "\($type)/platform/\($name)", spec: $merged[$type][$name]}
              # A key in a config file is named by its secret; a stored key holds it in `key`.
              | if .kind == "Key" then .spec.key //= $name else . end ]
            + if any(settings[]; . as $field | $file | has($field)) then
                [{kind: "Settings", name: "settings/platform/global",
                  spec: ($merged | with_entries(select(.key | IN(settings[]))))}]
              else [] end
        )} end' "$MERGED" "$1" > "$TMP/manifests.json"

    # Core stores such routes without an error, then never serves them (a BEARER upstream
    # without a key) or answers 500 (neither `response` nor `upstreams`).
    problems="$(jq -r '.manifests[] | select(.kind == "Route") | .name as $name | .spec
        | (select(.response == null and ((.upstreams // []) | length) == 0)
            | "  \($name): needs `response` or `upstreams`"),
          ((.upstreams // []) | to_entries[]
            | select((.value.authType // "API_KEY" | tostring | ascii_upcase) != "API_KEY"
                and (.value.key // "") == "")
            | "  \($name): upstreams[\(.key)] has authType \(.value.authType) but no key")
        ' "$TMP/manifests.json")"
    [ -z "$problems" ] || { echo "$problems" >&2; die "$1: invalid routes, nothing was written"; }

    log "$1: applying $(jq '.manifests | length' "$TMP/manifests.json") entities"
    code="$(request POST "$CORE_URL/v1/admin/apply" -H 'Content-Type: application/json' \
        --data-binary "@$TMP/manifests.json")"
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
        *)
            cat "$BODY" >&2; echo >&2
            check_status "$code" "POST /v1/admin/apply"
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

    jq -s "$JQ_LIB"'merge(.[0]; .[1])' "$MERGED" "$file" > "$TMP/next.json"
    mv "$TMP/next.json" "$MERGED"
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

# Files already applied above stay untouched; migrate only their stored model URLs.
# shortcut: only models declared in the sample files are migrated, update Admin-only models manually.
$core_ready || wait_for_core
jq -r '(.models // {}) | keys[] | @uri' "$MERGED" > "$TMP/model-names"
while IFS= read -r name; do
    url="$CORE_URL/v1/models/platform/$name"
    code="$(request GET "$CORE_URL/v1/metadata/models/platform/$name")"
    [ "$code" != 404 ] || continue
    [ "$code" = 200 ] || check_status "$code" "model metadata $name"
    etag="$(jq -er '.etag | select(type == "string" and length > 0)' "$BODY")" \
        || die "model $name: metadata has no etag"
    # Core omits secrets on GET and preserves them on the conditional PUT below.
    code="$(request GET "$url")"
    [ "$code" = 200 ] || check_status "$code" "read model $name"
    jq -f /usr/local/share/model-provider-migration.jq "$BODY" > "$TMP/model.json"
    # Compare JSON values, not formatting; a migrated model needs no further writes.
    jq -e -s '.[0] == .[1]' "$BODY" "$TMP/model.json" > /dev/null && continue
    # Core adds status on GET but rejects this computed field on PUT.
    jq 'del(.status)' "$TMP/model.json" > "$TMP/model-write.json"
    code="$(request PUT "$url" -H "If-Match: $etag" -H 'Content-Type: application/json' \
        --data-binary "@$TMP/model-write.json")"
    [ "$code" = 200 ] || check_status "$code" "migrate model $name (concurrent edit: retry startup)"
    log "model $name: migrated adapter URLs to model-provider"
done < "$TMP/model-names"
log "done"
