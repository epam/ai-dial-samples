# Quick Apps Frontend

A static single-page React app for the QuickApp2 settings editor, built with Vite and served by
[chat-api](https://github.com/epam/ai-dial-chat)'s own server — this app has no server-side code
of its own. Designed to be embedded as an `<iframe>` inside `ai-dial-chat` and communicate with
the host via `postMessage`.

## Development

```bash
npm install
npm start
```

`npm start` starts the Vite dev server on `http://localhost:4600` and proxies `/api/*` to a
QuickApps chat-api BFF running locally on `http://localhost:5001` (see `vite.config.ts`). Start that
backend with `npm run start:api:dev` (runs chat-api from a local checkout — see
[Running chat-api from a local checkout](#running-chat-api-from-a-local-checkout)), then `npm start`
in another terminal for a live-reloading frontend against a real backend.

## Commands

| Command                 | Description                                                                                            |
| ----------------------- | ------------------------------------------------------------------------------------------------------ |
| `npm start`             | Start the Vite dev server (hot-reloading frontend only — see above for the backend)                    |
| `npm run start:api:dev` | Run chat-api from a local checkout instead of a Docker image (see below)                               |
| `npm run build`         | Type-check and build                                                                                   |
| `npm run preview`       | Preview the production build locally                                                                   |
| `npm run lint`          | Run ESLint                                                                                             |
| `npm test`              | Run the test suite with coverage (fails below the 70% threshold — see [Test coverage](#test-coverage)) |
| `npm run test:watch`    | Run the test suite in watch mode, without coverage                                                     |
| `npm run typecheck`     | Type-check only (no build)                                                                             |
| `npm run format`        | Format the repo with Prettier                                                                          |
| `npm run format:check`  | Check formatting without writing changes                                                               |
| `npm run docker:run`    | Rebuild `dist/` and run it mounted into the published chat-api image (see below)                       |

## Docker

The root `Dockerfile` builds this app's static assets and layers them onto a published chat-api
image (`CHAT_API_IMAGE` build arg — see the Dockerfile for the exact tag to pin). It isn't wired to
an npm script; build and run it directly when you need the deployable image. The deployment default
is port `5000`:

```bash
docker build --platform=linux/amd64 -t quickapps-frontend .   # image is amd64-only
docker run --rm -p 5000:5000 --env-file .env -e PORT=5000 quickapps-frontend
```

For faster local iteration, `npm run docker:run` (see `scripts/docker-run-dist.mjs`) skips the
full image build: it rebuilds `dist/`, pulls the published `ai-dial-chat-bff` image (default
`ghcr.io/epam/ai-dial-chat-bff:development`, override with
`CHAT_API_IMAGE=ghcr.io/epam/ai-dial-chat-bff:<tag> npm run docker:run`), and mounts `dist/` straight
into it, reading env from `.env.docker` (copy `.env.template` to `.env.docker` and fill in values —
see [Configuration](#configuration)). The runner explicitly overrides the BFF to `PORT=5001` and
publishes it on `http://localhost:5001`; the Vite dev server remains on `http://localhost:4600`.

## Test coverage

`npm test` runs the full suite through `@vitest/coverage-v8` across every file under
`src/**/*.{ts,tsx}` (see `vitest.config.ts`) and fails the build if coverage drops — so it doubles
as the CI gate. The thresholds aren't 70% yet: they're pinned to the real current baseline (well
below that — see `docs/TECH_DEBT.md`'s "Test coverage" item for the latest numbers and what's
still untested) with `autoUpdate: true`, so they ratchet up automatically as tests are added and
only fail the build on an actual regression, not on the size of the remaining gap to 70%. Use
`npm run test:watch` for a fast watch-mode loop without the coverage overhead while writing tests.

## Running chat-api from a local checkout

If you have your own local checkout of [ai-dial-chat](https://github.com/epam/ai-dial-chat) and
want to work on this app and chat-api together (both live-reloading — this app via `npm start`,
chat-api via its own watch mode), `npm run start:api:dev` (see
`scripts/run-chat-api-local.mjs`) runs chat-api's `npm run start:api` directly from that checkout
instead of pulling and running a Docker image.

It reads this repo's own `.env.local` (create one if you don't have it — it's gitignored) for:

- `CHAT_API_LOCAL_DIR` — absolute path to your local ai-dial-chat checkout, e.g.
  `CHAT_API_LOCAL_DIR=/c/projects/dial/ai-dial-chat`.
- Every other variable chat-api itself needs at runtime (`PORT`, `DIAL_CORE_URL`, `AUTH_*`, ...,
  same set `.env.template` documents for the deployment path) — these are passed straight through as
  chat-api's own env. The launcher forces the QuickApps BFF to `PORT=5001`, keeping it separate from
  a Chat API instance running on its default port.

Then, in separate terminals:

```bash
npm run start:api:dev   # QuickApps BFF from your local checkout, on 5001
npm start                # this app, on 4600, proxying /api/* to it
```

## Configuration

The Docker image built from this repo (see [Docker](#docker)) is chat-api's own server with this
app's static build layered on top — this app has no server-side code or build-time env vars of its
own, but the **running container** still needs chat-api's own runtime configuration to actually
work, same as any other chat-api deployment. Copy `.env.template` to `.env` (or `.env.docker`/
`.env.local`, depending on how you're running it — see above) and fill in values.

The tables below cover the variables this app's deployment actually relies on; for the full list
of everything chat-api itself accepts, see
[chat-api's own README](https://github.com/epam/ai-dial-chat/blob/development/apps/chat-api/README.md#environment-variables).

### Server

| Variable     | Required | Default | Description                                                                                                                                                                                 |
| ------------ | :------: | :-----: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PORT`       |    No    | `5000`  | Default port for the deployable QuickApps BFF. Local Vite, local-checkout, and local-Docker workflows explicitly override it to `5001`; the Vite development server remains on port `4600`. |
| `API_PREFIX` |    No    |  `api`  | Path prefix for the API and health-check routes.                                                                                                                                            |

### DIAL core

| Variable        | Required | Description                                                     |
| --------------- | :------: | --------------------------------------------------------------- |
| `DIAL_CORE_URL` |   Yes    | Base URL of the DIAL Core API, e.g. `https://core.example.com`. |

### Auth: session

| Variable                       | Required | Description                                                                                                                                                                          |
| ------------------------------ | :------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `AUTH_SESSION_SECRET`          |   Yes    | 64 hex characters, used to sign/encrypt the session cookie. Generate with e.g. `openssl rand -hex 32`.                                                                               |
| `AUTH_SESSION_PREV_SECRET`     |    No    | Previous session secret, for zero-downtime rotation — sessions signed with either secret are accepted while both are set.                                                            |
| `AUTH_CALLBACK_BASE_URL`       |   Yes    | This app's own origin, e.g. `https://quickapps.example.com`. The popup sign-in's `callbackUrl` must be on this origin.                                                               |
| `CORS_ORIGIN`                  |   Yes    | Origin(s) allowed to call this app's API cross-origin. Usually the same value as `AUTH_CALLBACK_BASE_URL`.                                                                           |
| `AUTH_SESSION_COOKIE_NAME`     |    No    | Default `__Host-quickapps.sess`. Renamed away from chat's own `chat.*` cookie names so the two apps' sessions never collide when served from related origins.                        |
| `AUTH_TRANSACTION_COOKIE_NAME` |    No    | Default `__Host-quickapps.tx`. Short-lived cookie used only during the OAuth/OIDC handshake itself.                                                                                  |
| `AUTH_LEGACY_COOKIE_NAMES`     |    No    | Comma-separated cookie names to actively expire — set this when renaming `AUTH_SESSION_COOKIE_NAME`/`AUTH_TRANSACTION_COOKIE_NAME` on an existing deployment, otherwise leave unset. |

#### Known issue: `HTTP ERROR 431` clicking Login, after an old deployment on the same host

`431 Request Header Fields Too Large` on the sign-in redirect (or any request) means the browser
is sending more cookie data for this origin than the server's header-size limit allows. It shows
up when this app (or a build of it) has previously run on the same host under a different cookie
setup — most commonly, a next-auth-based deployment that used `chat.*`/`next-auth.*` cookie names
on `localhost:4600` (or the same production host) before this app's chat-api-based auth (with its
own `AUTH_SESSION_COOKIE_NAME`/`AUTH_TRANSACTION_COOKIE_NAME`) took over — the browser keeps
sending both the old and new cookies on every request, and their combined size eventually exceeds
the limit.

**Local dev fix:** clear cookies for `localhost:4600` (or whatever host you're testing) in the
browser, then retry.

**Production:** there's no way to auto-clear this from server code, because the request is
rejected for being oversized _before_ the server parses it far enough to run any
cookie-clearing logic — the fix has to happen on the next request, not the failing one. Two
things reduce the risk instead:

- Set `AUTH_LEGACY_COOKIE_NAMES` to the exact old cookie names being retired on that host so
  chat-api actively expires them on the first request that _does_ get through, rather than
  letting them accumulate indefinitely.
- Give the reverse proxy/load balancer in front of chat-api some header-size headroom above the
  default (e.g. nginx's `large_client_header_buffers`, or Node's own
  `--max-http-header-size`) as a safety margin — this doesn't fix stale cookies, but it buys
  enough room for the `AUTH_LEGACY_COOKIE_NAMES` expiry above to actually get a chance to run
  before the header set grows large enough to trip the limit again.

If a user hits this in production and neither mitigation is in place yet, the only recovery is
the same one as local dev: clear cookies for that host manually.

### Auth: identity provider

At least one OAuth/OIDC provider must be configured (Keycloak, Azure AD, Google, Auth0, Okta,
Cognito, GitLab). The variable names are per-provider and differ slightly (e.g. Keycloak's
`_HOST`/`_SECRET` vs. Azure AD's `_TENANT_ID`/`_CLIENT_SECRET`); `AUTH_KEYCLOAK_*` below is one
concrete example — see chat-api's own documentation for every supported provider's exact
variable names.

| Variable                  | Required | Description                                                                                                                                                                                                                |
| ------------------------- | :------: | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AUTH_KEYCLOAK_HOST`      |    †     | Keycloak realm base URL, e.g. `https://keycloak.example.com/realms/dial`.                                                                                                                                                  |
| `AUTH_KEYCLOAK_CLIENT_ID` |    †     | OAuth client id registered for this app in that realm.                                                                                                                                                                     |
| `AUTH_KEYCLOAK_SECRET`    |    †     | That client's secret. **Never commit a real value** — this is the one variable in this table you should treat as sensitive and set out-of-band (e.g. `docker run -e`, a secrets manager), not in a checked-in `.env` file. |

† Required if Keycloak is the (or one of the) configured provider(s); substitute the equivalent
provider-specific variables otherwise. Register `${AUTH_CALLBACK_BASE_URL}/api/v1/auth/callback/<provider>`
as that client's redirect URI.

### Themes

| Variable            | Required | Default | Description                                                                                                     |
| ------------------- | :------: | ------- | --------------------------------------------------------------------------------------------------------------- |
| `THEMES_CONFIG_URL` |    No    | —       | Base URL for DIAL themes; chat-api appends `/config.json` itself. Falls back to CSS variable defaults if unset. |

### Iframe embedding

| Variable                 | Required | Default | Description                                                                                                                                                                        |
| ------------------------ | :------: | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ALLOWED_IFRAME_ORIGINS` |    No    | none    | Comma-separated list of origins allowed to embed this app in an `<iframe>` (CSP `frame-ancestors`), e.g. `http://localhost:3000,http://localhost:3102`. Set to the exact admin/chat origin(s) in production. |
| `OVERLAY_ENABLED`        |    No    | unset   | Leave unset unless the session cookie needs `SameSite=None` for a specific embedding scenario — turning it on is chat's own overlay-runtime flag, not a QuickApps-specific toggle. |

### Content Security Policy

| Variable                  | Required | Default       | Description                                                                                                                                                             |
| ------------------------- | :------: | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CSP_MODE`                |    No    | `report-only` | Set to `enforce` only after confirming `report-only` produces no violation reports for this deployment — see [Content Security Policy](#content-security-policy) below. |
| `ALLOWED_CONNECT_ORIGINS` |    No    | none          | Additional origins the page may `fetch`/`XHR` to, beyond its own. Leave empty — this app only ever calls its own origin.                                                |

### Default model

| Variable             | Required | Description                                                                                                                               |
| -------------------- | :------: | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `DEFAULT_DEPLOYMENT` |    No    | Deployment id pre-selected in the form when no model is stored in the app config. Returned to the client as `config.defaultDeploymentId`. |

If `DEFAULT_DEPLOYMENT` is not set, or names a deployment the user can't see, the editor pre-selects the first model that supports tools. If there is none, the model stays empty and the form asks the user to pick one.

### QuickApps-specific settings

These don't map onto a native chat-api concept, so they travel inside `CUSTOM_CLIENT_VARIABLES`
— a single JSON object, passed through untouched to the client via `GET /api/v1/client-config`
(`src/utils/dial-client.ts`'s `fetchAppSettings`), which reads them into `AppSettings`
(`src/types/dial-entities.ts`). See the `app-configuration` spec for what each key controls:

| Key                      | Required | Description                                                                                                                                                                                                                                                    |
| ------------------------ | :------: | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `allowedOrigin`          |    No    | Origin(s) allowed to send/receive `postMessage` events with the editor iframe: one origin, a comma-separated list, or a JSON array. Set to the exact `ai-dial-chat`/admin origins in production; `*` (or unset) accepts any origin — unsafe outside local dev. |
| `dialAdminHost`          |    No    | Origin of the admin host this app is embedded in. Default target for `@epam/ai-dial-chat-visualizer-connector`.                                                                                                                                                |
| `dialChatHost`           |    No    | Origin of the `ai-dial-chat` host. Used instead of `dialAdminHost` when the app detects it's embedded directly inside chat (`document.location.ancestorOrigins[0]` matches this value).                                                                        |
| `codeInterpreterEnabled` |    No    | Boolean. Offers the Code interpreter setting (read as `isCodeInterpreterEnabled`); off when unset.                                                                                                                                                             |
| `webFetchEnabled`        |    No    | Boolean. Offers the Web fetch setting (read as `isWebFetchEnabled`); off when unset.                                                                                                                                                                           |
| `addAttachmentEnabled`   |    No    | Boolean. Offers the Add attachment setting (read as `isAddAttachmentEnabled`); off when unset.                                                                                                                                                                 |

`allowedOrigin` is read as `allowedOrigins`. A flag set to anything but the boolean `true` (for
example the string `"true"`) counts as off, as does every flag when the client-config request
fails.

Example: `CUSTOM_CLIENT_VARIABLES={"allowedOrigin":"https://chat.example.com,https://admin.example.com","dialAdminHost":"https://admin.example.com","codeInterpreterEnabled":true}`

The application (visualizer) name is not configured here: the host passes it per load as the
`applicationName` query parameter of the entry URL (see the `host-integration` spec). One
deployment can therefore serve several applications.

### OpenTelemetry

Disabled by default (`OTEL_SDK_DISABLED=true`). To enable, set it to `false` plus the standard
[OpenTelemetry SDK environment variables](https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/)
(`OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_PROTOCOL`,
`OTEL_METRICS_EXPORTER`, …) — see `.env.template` for the ones this deployment is most likely
to need.

## Authentication

Auth is handled entirely by chat-api itself — this app's own frontend code calls chat-api's
`/api/v1/auth/*` endpoints same-origin (`credentials: 'include'`, CSRF token from the `/me`
response echoed back on non-GET calls) and has no auth logic of its own. The **runtime
environment** still needs the "Auth: session" and "Auth: identity provider" variables above,
since that's chat-api's own auth configuration running inside the same container this app's
build is shipped in.

## API layer

Every DIAL entity call (applications, deployments, toolsets, skills, files, user config, themes,
client config) goes through the typed `@epam/ai-dial-chat-api-client` package against chat-api's
`/api/v1/*` REST surface — this app has no server-side proxy of its own. `src/utils/chat-api-client.ts`
holds one shared `Configuration` (CSRF + credentials via `src/utils/chat-api-fetch.ts`, plus a 401
loop-breaker) that every typed API instance is built from.

## Content Security Policy

CSP is enforced by chat-api's own server (Helmet), not by this app. This app's build carries a
`__DIAL_CSP_NONCE__` placeholder on its built `<script>`/`<link rel="stylesheet">` tags (see
`vite.config.ts`) for chat-api's nonce-based `CSP_MODE=enforce` policy, and bundles Monaco locally
(`src/monaco-setup.ts`) instead of loading it from a CDN, since `script-src` has no CDN allowance.
The same placeholder goes on a `<meta property="csp-nonce">` tag, which the ag-grid copy bundled in
ui-kit reads (via the `dial-trusted-style-nonce` build plugin) to put the nonce on the `<style>` tags
it injects. An image built before that plugin shows blocked ag-grid styles under `enforce`: rebuild
and redeploy it.

## postMessage protocol

The editor page (at `/`) communicates with its host via `postMessage`. Both sides validate
`event.origin` against `allowedOrigin` (see [Configuration](#configuration)).

In Dev mode the messages can be sent via console, e.g.

```
document.querySelector('iframe').contentWindow.postMessage({ type: 'TRIGGER_SAVE' }, '*')
```

**Host → iframe**

| Message type        | Payload                                                                                                                                         | Description                                                                                                                                                                                                                                                                                                                   |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `TRIGGER_SAVE`      | `{ general?: { name: string; description?: string; iconUrl?: string; topics?: string[]; display_version?: string; locales?; primaryLocale? } }` | Triggers a manual save. `general` carries the host's current General-step fields for an existing app so they're merged into this single save instead of a separate host-side write (`display_version` is saved as the app's `version`; see `application_editing`); omitted for Preview or for an app created in this session. |
| `TRIGGER_AUTO_SAVE` | `{ ignoreDirty?: boolean }`                                                                                                                     | Triggers an auto-save                                                                                                                                                                                                                                                                                                         |
| `RESET`             | —                                                                                                                                               | Remounts the form with the values loaded when the editor opened; it does not refetch the app                                                                                                                                                                                                                                  |

In addition to host-triggered `TRIGGER_AUTO_SAVE` messages, the editor auto-saves itself on a 30-second interval while mounted, once the app has been saved at least once, and only when the form is dirty — no host action is required. Auto-saves (host-triggered or not) are skipped until that first save, and an invalid form is not saved; the `application_editing` spec lists when a save is skipped.

**Iframe → host**

| Message type         | Payload                                 | Description                                                                                                                        |
| -------------------- | --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `READY`              | —                                       | Editor mounted (sent before the application has loaded)                                                                            |
| `DIRTY_STATE`        | `{ isDirty: boolean }`                  | Form dirty state changed                                                                                                           |
| `SAVE_SUCCESS`       | `{ updatedApp }`, `hasChanges: boolean` | Manual save completed; `hasChanges` compares the saved values with those loaded when the editor opened (see `application_editing`) |
| `SAVE_ERROR`         | `{ error: string }`                     | Save failed                                                                                                                        |
| `AUTO_SAVE_COMPLETE` | —                                       | Auto-save completed successfully                                                                                                   |
| `HEIGHT_CHANGE`      | `{ height: number }`                    | Editor height changed (for iframe resize)                                                                                          |

## Application credentials in the Chat host

When embedded by a Chat host advertising `applicationCredentials=true` in the iframe URL,
an attached agent's details popup loads that application's external services, because
deployment lists omit `external_services`. When the agent needs authentication, the popup
shows an Application credentials action under its header; if loading the metadata fails, the
action stays available so the host can show its retry form. Activating it closes the popup and
sends `{ type: 'REQUEST_APPLICATION_CREDENTIALS', appId }` to every configured allowed origin.
The host opens its shared Catalog credential forms, including API keys, OAuth and DIAL-native
offline consent. No credentials are passed to this editor or saved in the Quick app
configuration, and the editor's form state is untouched. Older hosts do not advertise the
query parameter, so the action is hidden there. See the `application_credentials` spec.
