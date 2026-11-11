# Essay Assistant

The smallest DIAL application in this repository. It takes the user's last
message, asks a model through DIAL Core for a short essay about it, and streams
the answer back.

In Chat, select **Essay Assistant** and click a conversation starter, or type
a topic.

## The code

[`app.py`](app.py) has two parts:

- `EssayAssistantApplication.chat_completion` handles each request. It
  creates a DIAL client with the caller's key (`request.api_key`), sends the
  system prompt and the user's last message to the model, and copies each
  chunk of the model's answer into the response.
- `EssayAssistantApplication.configuration` returns the conversation
  starters. Chat reads them from the application's configuration endpoint,
  which [`config.json`](../../../core/config.json) registers as
  `features.configurationEndpoint`.

`DIALApp` from the [DIAL SDK](https://github.com/epam/ai-dial-sdk) turns the
class into a web service that serves
`/openai/deployments/essay-assistant-app/chat/completions` and `/health` on
port 5026.

| Variable | Default | Meaning |
| --- | --- | --- |
| `DIAL_URL` | `http://localhost:8059` | Core's address. Docker Compose sets `http://core:8080`. |
| `DIAL_MODEL` | `ollama-qwen2.5` | The deployment ID of the model that writes the essays |

## Change it

After editing the code, rebuild it in the folder that you started DIAL from:

```sh
docker compose up --wait --build essay-assistant-app
```

To run it in your debugger instead, see
[Run a sample on your computer](../README.md#run-a-sample-on-your-computer-for-debugging).

Run the tests in this folder, with the dependencies from `requirements.txt`
installed:

```sh
python -m unittest discover -s tests
```
