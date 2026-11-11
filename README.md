<h1 align="center">DIAL Platform Samples</h1>

<p align="center">
  <a href="https://dialx.ai/">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://dialx.ai/logo/dialx_logo.svg">
      <img src="https://dialx.ai/logo/dialx_logo_light.svg" alt="DIALX">
    </picture>
  </a>
</p>

<p align="center">
  <a href="https://dialx.ai/"><img src="https://img.shields.io/static/v1?label=Official%20website&message=dialx.ai&color=7799FF&style=flat-square&logo=data%3Aimage%2Fpng%3Bbase64%2CiVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd%2BUAAAAAXNSR0IArs4c6QAAAERlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAA6ABAAMAAAABAAEAAKACAAQAAAABAAAAHKADAAQAAAABAAAAHAAAAABkvfSiAAAD2UlEQVRIDa1WS2tkRRQ%2Bp6ruo2N3a4hmEVHHQRjILKKM%2FoAsXYiKxE0Wgi4HxF8g8xNcOC4cBQdmM%2BNGHWYxmEVQQ0CDr0WIGKILk%2FiAISHpdPe99fCcurdud%2BchMbkF1XWqbtX56juvaoSTmluJ4tWJb5t5%2FGxrx0CrI6C1j8XoZWFbB7jW7sjl5j7ebx%2FgD1dvPbx%2BkrqwroJwZPznyQSg0wbnjnwqFwSCmBYimlZSvgUu37v58t5Kqytu6axz5%2FXFyf3jDorjFofWTkTjPc5ZMCYDbfoAiK1IprMxpB9P5I8sfjPTnR3SU4klQ4dzd2AEfGFvQ3ZGl6pDxwkMntseZFZAExpXEhD3fnqm%2B%2FbMeuOj4f0ecO5u7wnb1y8ACMMf0YF7fm18bOmp3Yf%2Bw6TDekbkjIDHXNxIXXx9Y0r%2FfXFLfRE2eFaik6dKu7bS2vfIulaiRZOAR1iHQ6cZDWggH8fK4nvbTfdYOOMVSuOcssIqK32XGhz3sOmsYwY5MRVPS6nfDDo8YAwJSCsPdfp0bkggSABp5Pxv4FIG9YAsROS9eKjzvI6mwTLIpccjuMT6PGCS8S1Gu7B1wAHBWUgBY40wzRqLtKA0kkiz0oQULCDpCy%2FV0VgPEbjAujwglRQAIwmgQGTAiOb1QXpNkwxTABJDTfoZiBuPdZm00Fio5d%2BKoSIf2iFADqA6G%2FmSaAUfksA1ZoQhA5YX4I3nbRbhD9bhGQIHDSkPDwMDy5qiFCkyNAGhFf7pqnyIUlQmFQQYGVtLlArKvAzsg9SInwcMSeIgwZIVA1L61NJiujaZ8%2BsGwBYrrIKGfViZlMBCpWHsszY2Z052U8J%2BgBB5VUWl6dPrRYChc9WpIy3GUEGG5vbkrloIlx4ETTxgyGAMep4obWACB6B%2FbDSid4hp5aDKpJbLernMURrR%2FCylTRKrVMbQd%2FlXTpk3Lq9HfwV2PFavhSQAZhbYnTotkO6PApRMIJZjZBS33XO9d2UUvfjcWuP3YTCWq7TwFiwpMWjMDzDpckqCU0RZ0d24wlP6cAqh5FpLpxz00dmucea73JrPpel%2B9srSo5uHgcLcA5L76J8XF9Ny2QBO7Mj%2Bq8vj72cK07RXvJVJT%2FBFIM4R%2BElLe0K3jOqqGL7fmlJfXr028FUAODwOgqYybrGFg%2Bal5favxNYB3YUt4BvJlFfo6A%2BLQcgSB6uvfQiriKEwho3HjwOTsoUCw3KviYpg5akHoceb3GXJuh3tYDPL4Jf5T3AHbpQHTjF4QFJiQoQePkMvCNJfbE1pu5sg%2FNk1sDXdgQeXP0Uy6v9v%2FwLX%2BXJesfXLGQAAAABJRU5ErkJggg%3D%3D" alt="Official website: dialx.ai"></a>
  <a href="https://discord.gg/ukzj9U9tEe"><img src="https://img.shields.io/static/v1?label=DIALX%20Community%20on&message=Discord&color=blue&logo=Discord&style=flat-square" alt="DIALX Community on Discord"></a>
</p>



Run [AI DIAL](https://dialx.ai) on your own computer with one command.

DIAL is a platform that puts many AI models and AI applications behind one
chat window and one API. These samples start everything with Docker, including
small open-source models, so you need **no API keys and no cloud account**.

## Pick a setup

| | [1-dial-simple-setup](1-dial-simple-setup/README.md) | [2-dial-advanced-setup](2-dial-advanced-setup/README.md) |
| --- | --- | --- |
| For | Your first look at DIAL | Exploring everything DIAL can do |
| You get | Chat, Admin and Core, local models, and three sample applications you can change | Everything from setup 1, plus Quick Apps, Scheduler, Evaluation and Analytics |
| Disk space | About 13 GB | About 20 GB |
| Memory for Docker | 16 GB (8 GB without the picture model) | 16 GB |

Start with setup 1. Setup 2 builds on top of it, so you can switch to it later
without losing anything.

## Start in 3 steps

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   and start it. In its **Settings → Resources**, give it 16 GB of memory.
2. In a terminal, run:

   ```sh
   cd 1-dial-simple-setup
   docker compose up --wait
   ```

   On a Mac with Apple Silicon (M1 or newer), run
   `echo DIAL_PLATFORM=linux/amd64 >> .env` after `cd 1-dial-simple-setup` and
   before `docker compose up`. DIAL Chat and Admin have no ARM build yet, so
   this tells Docker to run them through emulation. Windows, Linux and Intel Macs
   need nothing.

   The command finishes when DIAL is ready. The first time, it downloads
   everything it needs, which takes a while.
3. Open <http://localhost:8055> and sign in as `dial`, password `dial`.

Say hello to the **qwen2.5** model. 🎉

To manage models and applications, open DIAL Admin at <http://localhost:8056>
and sign in as `dial-admin`, password `dial`.

To stop DIAL, run `docker compose down` in the same folder. Your chats are kept
for the next start.

## What is in this repository

```text
ai-dial-samples/
├── 1-dial-simple-setup/       Step 1: Chat + Admin + Core + local models
│   ├── docker-compose.yml     Which services run
│   ├── keycloak/              Users and passwords for signing in
│   └── dial_entity_samples/   Sample applications and an interceptor, in Python
├── 2-dial-advanced-setup/     Step 2: everything from step 1, plus more services
│   ├── docker-compose.yml     The extra services; includes step 1
│   └── simple-setup-overrides.yml   What step 2 changes in step 1's services
├── core/                      DIAL Core configuration, used by both setups
│   ├── config.json            Every model, application, interceptor, API key and role
│   └── config-apply/          Copies config.json into Core on the first start
├── core-data/                 Core's storage: chats, files, models, apps (created on first start)
└── logs/                      Core's request logs (created on first start)
```

`core-data/` and `logs/` stay on your computer; Git ignores them.

## How DIAL Core gets its models and applications

DIAL Core is the gateway in the middle: Chat, Admin and the sample
applications all talk to it. Core keeps its models, applications, interceptors,
API keys and roles in its storage, in `core-data/`. DIAL Admin views and edits
that same storage.

[`core/config.json`](core/config.json) fills the storage on the first start:

```mermaid
flowchart LR
    files["core/config.json<br/>models, applications,<br/>interceptors, keys, roles"]
    apply["core-config-apply"]
    storage[("Core's storage<br/>core-data/")]
    admin["DIAL Admin"]

    files --> apply -->|first start only| storage
    admin <-->|view and change| storage
```

1. On the first `docker compose up` of either setup, the `core-config-apply`
   service sends every entity in `core/config.json` to Core, then stops. It
   adds all of them, including the ones that only setup 2 uses.
2. It lists the files it applied in `core-data/core-config-apply.json`, and
   skips them on every later start.
3. From then on, **change models and applications in DIAL Admin**. Your changes
   are kept across restarts.

So editing `core/config.json` after the first start changes nothing by itself.
To apply your edits, run this in the setup's folder:

```sh
rm ../core-data/core-config-apply.json
docker compose up --wait
```

This applies the file again and overwrites the changes you made in Admin to the
entities in it. Entities that you created in Admin stay.

For every file in `core/`, see [core/README.md](core/README.md).

## How the two setups fit together

Setup 2 does not copy setup 1. Its `docker-compose.yml`
[includes](https://docs.docker.com/compose/how-tos/multiple-compose-files/include/)
setup 1's `docker-compose.yml`, adds services next to it, and changes a few of
setup 1's services in `simple-setup-overrides.yml`.

Both setups use the Docker Compose project name `dial`. Starting setup 2
upgrades a running setup 1 in place and keeps its downloaded models, users and
chats. Setup 2 adds services, but no models or applications: setup 1 has
already put all of them into Core.

## Updating from an earlier version of these samples

Earlier versions ran a separate adapter container for each model provider, and
DIAL Core read `config.json` directly. After `git pull`, run this in the
folder of the setup you use:

```sh
docker compose up --wait --build --remove-orphans
```

- `--remove-orphans` removes containers that the setup no longer uses, such as
  the old adapters and InfluxDB.
- `core-config-apply` copies the models and applications into Core's storage
  on this start. Your chats are kept.
- If your `.env` came from an older `.env.example`, delete its `*_VERSION`
  lines: some of those images were renamed or replaced.

## Learn more

- [DIAL documentation](https://docs.dialx.ai)
- [DIAL on GitHub](https://github.com/epam/ai-dial)
- [Contributing](CONTRIBUTING.md)
