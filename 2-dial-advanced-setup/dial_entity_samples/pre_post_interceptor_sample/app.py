import os

import uvicorn
from aidial_interceptors_sdk.chat_completion import interceptor_to_chat_completion
from aidial_interceptors_sdk.chat_completion.base import ChatCompletionInterceptor
from aidial_interceptors_sdk.utils._http_client import get_http_client
from aidial_sdk import DIALApp
from aidial_sdk.chat_completion import Status
from aidial_sdk.chat_completion.chunks import ContentStageChunk, FinishStageChunk, StartStageChunk
from typing_extensions import override


class PrePostInterceptorSample(ChatCompletionInterceptor):

    def send_stage(self, name: str, content: str) -> None:
        # A reserved index never collides with stages coming from the upstream model.
        stage_index = self.reserve_stage_index(0)
        self.send_chunk(StartStageChunk(0, stage_index, name))
        self.send_chunk(ContentStageChunk(0, stage_index, content))
        self.send_chunk(FinishStageChunk(0, stage_index, Status.COMPLETED))

    @override
    async def on_stream_start(self) -> None:
        self.send_stage("Greeting Stage", "Hi, from Greeting Stage👋")

    @override
    async def on_stream_end(self) -> None:
        self.send_stage("Goodbye Stage", "Goodbye, from Goodbye Stage👋")


async def client_factory():
    return get_http_client()


DIAL_URL = os.getenv("DIAL_URL", "http://localhost:8059")

pre_post_interceptor_app = interceptor_to_chat_completion(
    cls=PrePostInterceptorSample,
    dial_url=DIAL_URL,
    client_factory=client_factory,
)

app = DIALApp(
    dial_url=DIAL_URL,
    propagate_auth_headers=True,
    add_healthcheck=True,
)
app.add_chat_completion(deployment_name="pre-post-interceptor", impl=pre_post_interceptor_app)

if __name__ == "__main__":
    import sys

    if 'pydevd' in sys.modules:
        config = uvicorn.Config(app, port=5041, host="0.0.0.0", log_level="info")
        server = uvicorn.Server(config)
        import asyncio

        asyncio.run(server.serve())
    else:
        uvicorn.run(app, port=5041, host="0.0.0.0")
