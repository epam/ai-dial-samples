# Pre/post interceptor sample

An interceptor sits between a caller and a model. DIAL Core sends it the
request; the interceptor can change the request, call the model, and change
the answer. This one adds a **Greeting Stage** before the model's answer and
a **Goodbye Stage** after it.

In Chat, select **qwen2.5 + pre/post interceptor** and send any message. The
answer shows "Executed 2 steps"; open it to see both stages.

## How it is connected

[`core/1-dial-simple-setup/config.json`](../../../core/1-dial-simple-setup/config.json)
in the repository root registers the interceptor and a model that uses it:

```json
"interceptors": {
  "pre-post-interceptor": {
    "interfaces": {
      "openaiChatCompletions": {
        "mode": "passthrough",
        "base_url": "http://pre-post-interceptor:5041"
      }
    }
  }
},
"models": {
  "ollama-qwen2.5-with-interceptor": {
    "interceptors": ["pre-post-interceptor"]
  }
}
```

`core-config-apply` copies them into Core on the first start. After that,
change them in DIAL Admin.

For a request to that model, Core calls the interceptor first. The interceptor
calls Core again, and Core continues to the model. The interceptor forwards
the caller's credentials, so it needs no API key of its own.

To intercept another deployment, add `"interceptors": ["pre-post-interceptor"]`
to it. To intercept every chat request, list it in `globalInterceptors`
instead; see the [Core documentation](../../../readmes/dial-core-README.md#dynamic-settings).

## The code

`app.py` subclasses `ChatCompletionInterceptor` from the
[DIAL Interceptors SDK](https://github.com/epam/ai-dial-interceptors-sdk):

- `on_stream_start` runs before the first chunk of the model's answer;
- `on_stream_end` runs after the last one.

Each sends a stage, with a stage index reserved through
`reserve_stage_index` so it never collides with stages coming from the model.
The SDK has more hooks, for example to change the request or each chunk of the
answer.

| Variable | Default | Meaning |
| --- | --- | --- |
| `DIAL_URL` | `http://localhost:8059` | Core URL. Docker Compose sets `http://core:8080`. |

The service listens on port 5041 inside Docker and is not published on your
computer. `GET /health` returns `{"status": "ok"}`.

To run it outside Docker for debugging, see
[Run a sample on your computer](../README.md#run-a-sample-on-your-computer-for-debugging).
