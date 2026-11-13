# DIAL Core configuration

Everything that configures DIAL Core, for both setups. Docker Compose mounts
this folder into the `core` container at `/opt/config`.

| File | What it is | Who reads it |
| --- | --- | --- |
| [`config.json`](config.json) | Every model, application, interceptor, API key and role, except the Scheduler's | `core-config-apply`, on the first start |
| [`scheduler.json`](scheduler.json) | The Scheduler application and its API key. Only the advanced setup uses it, because only that setup runs Scheduler. | `core-config-apply`, on the first start of the advanced setup |
| [`admin-key.json`](admin-key.json) | The admin API key `dial_admin_api_key` | Core |
| [`quick-apps-schemas.json`](quick-apps-schemas.json) | The Quick Apps application type. Only the advanced setup uses it, because it needs Quick Apps Backend. | Core |
| [`settings.json`](settings.json) | Core's server settings | Core |
| [`gflog.xml`](gflog.xml) | Where Core writes its logs: `../logs` | Core |
| [`config-apply/`](config-apply/) | The `core-config-apply` service | Docker Compose builds it |

## How models and applications get into Core

Core keeps its models, applications, interceptors, API keys and roles in its
storage, in `../core-data`. DIAL Admin views and changes that storage.

On the first start of either setup, the `core-config-apply` service fills it:

1. It waits until Core is healthy.
2. It sends every entity of `config.json` to Core's API, `POST /v1/admin/apply`.
   In the advanced setup, it then does the same for `scheduler.json`.
3. It lists the applied files in `../core-data/core-config-apply.json`, with the
   time, each file's SHA-256 and the IDs of the stored entities, then stops.

On every later start, it skips the files that are listed. If you have changed a
file since, its log says so. That is why changes made in DIAL Admin are kept
across restarts.

When you upgrade a running simple setup to the advanced one, `config.json` is
already listed, so only `scheduler.json` is applied. `config.json` also has the
Evaluation API key, which does nothing until the advanced setup starts
Evaluation.

Core checks all entities of a file before it stores any of them. If one is
invalid, nothing from that file is stored, and `docker compose logs core-config-apply`
names the entity and the reason.

## Apply the files again

After the first start, the easiest way to change an entity is DIAL Admin. To
apply your edits to `config.json` or `scheduler.json` instead, run this in the
folder of the setup you use:

```sh
rm ../core-data/core-config-apply.json
docker compose up --wait
```

This overwrites the changes you made in DIAL Admin to the entities in these
files. Entities that you created in Admin stay. To apply only one of the files
again, delete just its entry from `core-data/core-config-apply.json`.

## File formats

`config.json` uses the format of Core's own configuration files. Its sections
`models`, `applications`, `interceptors`, `toolsets`, `translators`, `roles`,
`keys` and `routes` become entities named `<section>/platform/<name>`, such as
`models/platform/ollama-qwen2.5`. The settings `globalInterceptors`,
`retriableErrorCodes`, `rateLimitSchedule` and `spendingLimits` are applied
too.

`scheduler.json` is a list of manifests, `{"manifests": [...]}`, which
`core-config-apply` sends to Core as it is. This format can name entities
outside `platform`: the Scheduler application must be public,
`applications/public/dial_scheduler`.

## core-config-apply settings

Docker Compose sets these in [`../1-dial-simple-setup/docker-compose.yml`](../1-dial-simple-setup/docker-compose.yml).
The advanced setup adds `scheduler.json` to `CONFIG_FILES` in
[`../2-dial-advanced-setup/simple-setup-overrides.yml`](../2-dial-advanced-setup/simple-setup-overrides.yml).

| Variable | Default | Meaning |
| --- | --- | --- |
| `API_KEY` | Required | A Core API key with the `admin` role. It must come from a file that Core reads itself, because Core's storage is empty before the first apply: `dial_admin_api_key` from `admin-key.json`. |
| `CONFIG_FILES` | Required | Files to apply, in order, separated by spaces |
| `CORE_URL` | `http://core:8080` | Core's address |
| `STATE_FILE` | `core-data/core-config-apply.json` | The list of applied files |
| `WAIT_TIMEOUT` | `120` | Seconds to wait for Core to become healthy |

Docker Compose mounts the repository's `core/` and `core-data/` folders at
`/dial/core` and `/dial/core-data`, and rebuilds the service's small image on
every start, so it always runs the script from your checkout.
