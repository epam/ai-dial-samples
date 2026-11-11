# core-config-apply

A small service that copies DIAL Core entities (models, applications,
interceptors, API keys, roles and more) from JSON files into Core's storage,
then exits. Both setups run it on every `docker compose up`, but it applies
each file only once.

It does this through Core's API, `POST /v1/admin/apply`. After the first start,
the entities live in Core's storage like the ones you create in DIAL Admin:
change them there, and your changes are kept.

## What it does on each start

1. Waits until Core is healthy.
2. For each file in `CONFIG_FILES`, in order:
   - if `STATE_FILE` already lists the file, skips it. If the file has changed
     since, it says so in its log;
   - otherwise sends the file's entities to Core, then adds the file to
     `STATE_FILE` with the time, the file's SHA-256 and the IDs of the stored
     entities.

   Core checks all entities of a file before it stores any of them. If one is
   invalid, nothing from that file is stored, and the log names the entity and
   the reason.
3. Moves stored sample models that still point to the old adapter containers
   (`adapter-dial-openai`, `adapter-dial-bedrock`, `adapter-dial-vertexai`) to
   Model Provider, keeping their keys and other settings. This only matters for
   installations that stored models before Model Provider replaced the
   adapters; otherwise it changes nothing. The rules are in
   [`model-provider-migration.jq`](model-provider-migration.jq).

## Apply files again

From the folder of the setup you run:

```sh
rm ../core-data/core-config-apply.json
docker compose up --wait
```

This applies all files again and overwrites the changes you made in DIAL Admin
to their entities. Entities that you created in Admin stay. To apply only one
file again, delete just its entry from `core-data/core-config-apply.json`.

## File formats

A file can have one of two formats.

**A Core config file**, in the same format as Core's own configuration files.
Its sections `models`, `applications`, `interceptors`, `toolsets`, `translators`,
`roles`, `keys` and `routes` become entities named `<section>/platform/<name>`,
such as `models/platform/ollama-qwen2.5`. The settings `globalInterceptors`,
`retriableErrorCodes`, `rateLimitSchedule` and `spendingLimits` are applied
too. An example is
[`core/1-dial-simple-setup/config.json`](../core/1-dial-simple-setup/config.json).

As with Core's own files, each file is merged into the files before it:
objects merge and arrays are joined. A later file can add fields to an entity
of an earlier one.

**A manifest bundle**, `{"manifests": [...]}`, which is sent to Core as it is.
Use it for entities outside `platform`, such as the public Scheduler
application in
[`core/2-dial-advanced-setup/scheduler.json`](../core/2-dial-advanced-setup/scheduler.json).

## Settings

| Variable | Default | Meaning |
| --- | --- | --- |
| `API_KEY` | Required | A Core API key with the `admin` role. It must come from a file that Core reads itself, because Core's storage is empty before the first apply. The setups use `dial_admin_api_key` from [`core/1-dial-simple-setup/admin-key.json`](../core/1-dial-simple-setup/admin-key.json). |
| `CONFIG_FILES` | Required | Files to apply, separated by spaces, relative to `/dial` |
| `CORE_URL` | `http://core:8080` | Core's address |
| `STATE_FILE` | `core-data/core-config-apply.json` | The list of applied files |
| `WAIT_TIMEOUT` | `120` | Seconds to wait for Core to become healthy |

Docker Compose mounts the repository's `core/` and `core-data/` folders at
`/dial/core` and `/dial/core-data`. It rebuilds this image on every start, so
it always runs the script from your checkout.

## Tests

```sh
python3 -m unittest discover -s core-config-apply
```

The migration tests need only `jq`. The other tests create and delete entities
in a real Core, so they run only when `TEST_CORE_URL` points to a Core that you
can throw away, never a shared one:

```sh
TEST_CORE_URL=http://localhost:18059 python3 -m unittest discover -s core-config-apply
```
