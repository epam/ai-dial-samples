# DIAL entity samples

DIAL Core sends requests to *entities*: models, applications, interceptors and
toolsets. An application or interceptor is a web service that you write; Core
calls it with the same API as a model. This folder holds three of them, in
Python. Docker Compose builds and runs each one.

| Sample | Entity type | What it does | Try it in Chat |
| --- | --- | --- | --- |
| [essay_assistant_app](essay_assistant_app/README.md) | Application | Writes short essays with a local model. The simplest sample: start here. | Select **Essay Assistant** |
| [agent_app_sample](agent_app_sample/README.md) | Application | An agent that searches the web and understands pictures | Sign in as `dial`, select **AI Agent Sample** |
| [pre_post_interceptor_sample](pre_post_interceptor_sample/README.md) | Interceptor | Adds a step before and after a model's answer | Sign in as `dial`, select **qwen2.5 + pre/post interceptor** |

All samples use the [DIAL SDK](https://github.com/epam/ai-dial-sdk); the
interceptor also uses the
[DIAL Interceptors SDK](https://github.com/epam/ai-dial-interceptors-sdk).

## How a sample is connected

Each sample needs two things, which are already in place:

1. **A service** in [`../docker-compose.yml`](../docker-compose.yml) that builds
   the sample's `Dockerfile` and runs it.
2. **An entity in Core** that tells Core the service's address and who may use
   it. It comes from
   [`core/config.json`](../../core/config.json)
   in the repository root, which `core-config-apply` copies into Core on the
   first start. You can see and change it in DIAL Admin.

| Sample | Entity in `config.json` | Address |
| --- | --- | --- |
| Essay Assistant | `applications.essay-assistant-app` | `http://essay-assistant-app:5026` |
| AI Agent Sample | `applications.agent-app-sample` | `http://agent-app-sample:5025` |
| Interceptor | `interceptors.pre-post-interceptor`, used by `models.ollama-qwen2.5-with-interceptor` | `http://pre-post-interceptor:5041` |

Applications call models back through Core, with the key that Core passes to
them in each request. That key carries the caller's permissions, so the samples
need no API key of their own, and each user reaches only the models that their
roles allow.

## Change a sample

Edit the code, then rebuild and restart it. Run this in the folder that you
started DIAL from, `1-dial-simple-setup` or `2-dial-advanced-setup`:

```sh
docker compose up --wait --build essay-assistant-app
```

The service names are `essay-assistant-app`, `agent-app-sample` and
`pre-post-interceptor`.

> [!WARNING]
> If you run the advanced setup, run this command in `2-dial-advanced-setup`.
> From `1-dial-simple-setup`, it can restart Core with the simple setup's
> settings.

## Run a sample on your computer, for debugging

You can run a sample outside Docker, for example in your IDE's debugger, while
the rest of DIAL keeps running in Docker. You need Python 3.12 or newer.

1. Stop its container, in the folder that you started DIAL from:

   ```sh
   docker compose stop essay-assistant-app
   ```

2. Start the sample on your computer, in the sample's folder:

   ```sh
   python -m venv .venv
   .venv/bin/pip install -r requirements.txt
   .venv/bin/python app.py
   ```

   It listens on the same port as in Docker and calls Core at
   `http://localhost:8059`.

3. Point Core at your computer. In DIAL Admin, open the sample's entity and
   replace the host name in its address with `host.docker.internal`, keeping
   the port:

   ```text
   http://essay-assistant-app:5026  ->  http://host.docker.internal:5026
   ```

   Change every address of the entity: Essay Assistant also has one in its
   configuration endpoint, which serves its conversation starters. Core uses
   the new addresses right away.

When you finish, change the address back and run `docker compose up --wait`.

## Add your own entity

1. Create a folder here in `snake_case`, with your code, `requirements.txt`
   and a `Dockerfile`. Copying the closest sample is the easiest start;
   `essay_assistant_app` is the smallest.
2. Add a service for it to `../docker-compose.yml`.
3. Start it: `docker compose up --wait --build`.
4. Tell Core about it, in one of two ways:
   - **In DIAL Admin** (easiest): create the application, model or
     interceptor, with your service's address.
   - **In `config.json`**: add an entry to
     `../../core/config.json`, next to the samples' entries,
     then [apply the file again](../README.md#apply-configjson-again). This
     also resets your Admin changes to the other entities of that file.
