# Agent app sample

DIAL deployment `agent-app-sample` answers chat requests, searches DuckDuckGo
through a local Python tool (no MCP or search API key), and analyzes PNG/JPEG
pictures with LLaVA. Conversation history is preserved. Pictures are first
converted into observations by the vision deployment; the chat model then uses
those observations and can search the web to compose its answer. This sample
analyzes pictures; it does not generate or edit them.

Both setups build and start it. After changing the code, rebuild it in the
folder that you started DIAL from:

```sh
docker compose up --wait --build agent-app-sample
docker compose logs -f agent-app-sample
```

Select **AI Agent Sample** in Chat. The app uses these environment variables:

| Variable | Default | Meaning |
| --- | --- | --- |
| `DIAL_URL` | `http://localhost:8059` | Core URL; Compose sets `http://core:8080` |
| `AGENT_MODEL` | `ollama-qwen2.5` | Core chat deployment; must support function tools |
| `VISION_MODEL` | `ollama-llava-vision` | Core vision deployment; uses LLaVA in this stack |
| `MODEL_TIMEOUT_SECONDS` | `300` | Timeout for each model or DIAL file call; allows CPU model loading |
| `AGENT_APP_PORT` | `8065` | Host port published by Compose; the app listens on 5025 |
| `WEB_SEARCH_URL` | `https://html.duckduckgo.com/html` | Search endpoint; override locally for simulation |

Set `AGENT_MODEL` and `VISION_MODEL` in the `.env` of the folder that you
started DIAL from, then run `docker compose up --wait`. These are **Core
deployment IDs**, not Ollama model names. To change the Ollama model behind a
deployment, see
[Change a model](../../README.md#change-a-model). A larger model that supports
tools makes better search decisions than the small default, Qwen 0.5B. To use a
cloud model, [set it up](../../README.md#use-cloud-models) first.

The app forwards the incoming DIAL API key for model and DIAL file requests.
It does not need a separate configured API key. No prompts or keys are logged.
DuckDuckGo HTML search can return a bot challenge; tool results report failure
or empty results so the model can explain the limitation.

## HTTP contract

`POST /openai/deployments/agent-app-sample/chat/completions` accepts the DIAL
chat-completion message format and an `api-key` header. It supports both
`stream: false` (a completion JSON response) and `stream: true` (SSE deltas,
including DIAL stages for picture analysis and search). `GET /health` is the
app health endpoint. The application implements its own `web_search` tool;
callers do not supply tool definitions.

```sh
curl --fail http://localhost:8059/openai/deployments/agent-app-sample/chat/completions \
  -H 'api-key: dial_api_key' -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Search the web for DIAL SDK documentation and cite the sources."}],"stream":true}'
```

Pictures may be OpenAI `image_url` content parts (base64 data URLs or DIAL file
URLs) or DIAL
`custom_content.attachments`. A DIAL attachment can contain a `files/...` URL
or raw base64 in `data`, with `type: image/png` or `image/jpeg`. The app downloads
DIAL files with the caller's key and sends data URLs to the vision model.
External image URLs are rejected: upload the picture to DIAL or use a data URL.
Inline/downloaded images are limited to 10 MiB each, with at most four images
across conversation history. Unsupported attachments and invalid data URLs
produce request errors. Model failures produce a gateway error (or an SSE error
if streaming has begun). Search has a 20-second timeout and 30 requests/minute
per app process; the agent allows four tool rounds, up to four searches each.

Example message using a file uploaded through Chat:

```json
{
  "messages": [{
    "role": "user",
    "content": "What is in this picture?",
    "custom_content": {
      "attachments": [{"type": "image/png", "url": "files/<bucket>/picture.png"}]
    }
  }]
}
```

## Local development

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

To have Core call this local copy instead of the container, see
[Run a sample on your computer](../README.md#run-a-sample-on-your-computer-for-debugging).
Live checks require working Core model deployments and network access to
DuckDuckGo.
