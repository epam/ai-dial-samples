# DIAL entity samples

DIAL Core sends requests to *entities*: models, applications, interceptors and
toolsets. This folder holds Python code for two of them. Docker Compose builds
and runs each one as a service of the advanced setup.

| Sample | Entity type | What it does | Try it in Chat |
| --- | --- | --- | --- |
| [agent_app_sample](agent_app_sample/README.md) | Application | An agent that searches the web and understands pictures | Select **AI Agent Sample** |
| [pre_post_interceptor_sample](pre_post_interceptor_sample/README.md) | Interceptor | Adds a step before and after a model's answer | Select **qwen2.5 + pre/post interceptor** |

Both samples use the [DIAL SDK](https://github.com/epam/ai-dial-sdk); the
interceptor also uses the
[DIAL Interceptors SDK](https://github.com/epam/ai-dial-interceptors-sdk).

## How a sample is connected

Each sample needs two things, which are already in place:

1. **A service** in `../docker-compose.yml` that builds the folder's
   `Dockerfile` and runs it.
2. **An entry** in [`core/2-dial-advanced-setup/config.json`](../../core/2-dial-advanced-setup/config.json)
   in the repository root, which tells Core the service's address:

   | Sample | Entry in `config.json` | Address |
   | --- | --- | --- |
   | Agent | `applications.agent-app-sample` | `http://agent-app-sample:5025` |
   | Interceptor | `interceptors.pre-post-interceptor`, used by `models.ollama-qwen2.5-with-interceptor` | `http://pre-post-interceptor:5041` |

## Change a sample

Edit the code, then rebuild and restart it from `2-dial-advanced-setup`:

```sh
docker compose up --wait --build agent-app-sample
```

## Run a sample on your computer, for debugging

You can run a sample outside Docker, for example in your IDE's debugger, while
the rest of DIAL keeps running in Docker. With Python 3.12 or newer, from the
sample's folder:

1. Stop its container:

   ```sh
   docker compose stop pre-post-interceptor
   ```

2. Start the sample on your computer:

   ```sh
   python -m venv .venv
   .venv/bin/pip install -r requirements.txt
   .venv/bin/python app.py
   ```

   It calls Core at `http://localhost:8059` (the `DIAL_URL` default).

3. Point Core at your computer. In `../../core/2-dial-advanced-setup/config.json`, replace the
   sample's host name with `host.docker.internal` and keep the port, for
   example:

   ```text
   http://pre-post-interceptor:5041/...  ->  http://host.docker.internal:5041/...
   ```

   Core applies the change within 3 seconds.

When you finish, change the address back and run `docker compose up --wait`.

## Add your own entity

1. Create a folder here in `snake_case`, with your code, `requirements.txt`
   and a `Dockerfile`. Copying the closest sample is the easiest start.
2. Add a service for it to `../docker-compose.yml`.
3. Add its entry to `../../core/2-dial-advanced-setup/config.json`.
4. Run `docker compose up --wait --build`.
