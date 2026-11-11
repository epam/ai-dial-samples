import os
import uvicorn
from aidial_sdk import DIALApp
from aidial_client import AsyncDial
from aidial_sdk.chat_completion import Button, ChatCompletion, FormMetaclass, Request, Response
from aidial_sdk.deployment.configuration import ConfigurationRequest
from pydantic.v1 import BaseModel, Field

SYSTEM_PROMPT = """You are an essay-focused assistant. Respond to every request by writing a **short essay** of up to 100 tokens.

**Structure:**
- Clear introduction with thesis
- Body paragraphs with supporting points
- Concise conclusion

**Rules:**
- Always write in essay format regardless of topic
- Keep responses analytical and structured
- Use formal, academic tone
- Include specific examples when relevant
- Maintain logical flow between paragraphs
"""


class EssayConfiguration(BaseModel, metaclass=FormMetaclass):
    starter: int | None = Field(
        default=None,
        description="Conversation starters",
        buttons=[
            Button(
                const=1,
                title="About elephant in space",
                populateText="Generate me one about elephant in space",
            ),
            Button(
                const=2,
                title="About dog that can sing",
                populateText="Generate essay about dog that can sing",
            ),
        ],
    )


class EssayAssistantApplication(ChatCompletion):

    def __init__(self, model: str):
        self.model = model

    async def chat_completion(self, request: Request, response: Response) -> None:
        # Call Core with the caller's own key, so the caller's access rules apply.
        client: AsyncDial = AsyncDial(
            base_url=os.getenv("DIAL_URL", "http://localhost:8059"),
            api_key=request.api_key,
            api_version="2025-01-01-preview"
        )

        with response.create_single_choice() as choice:
            chunks = await client.chat.completions.create(
                deployment_name=self.model,
                stream=True,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": request.messages[-1].content
                    }
                ],
            )

            async for chunk in chunks:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        choice.append_content(delta.content)

    async def configuration(self, request: ConfigurationRequest) -> dict:
        return EssayConfiguration.schema()

app: DIALApp = DIALApp(add_healthcheck=True)

model_name = os.getenv("DIAL_MODEL", "ollama-qwen2.5")

app.add_chat_completion(deployment_name="essay-assistant-app", impl=EssayAssistantApplication(model_name))

if __name__ == "__main__":
    uvicorn.run(app, port=5026, host="0.0.0.0")
