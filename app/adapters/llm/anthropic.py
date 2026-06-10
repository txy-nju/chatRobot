from anthropic import AsyncAnthropic

from app.adapters.llm.base import BaseLLMClient


class AnthropicClient(BaseLLMClient):
    """Anthropic adapter using the official anthropic SDK."""

    def __init__(self, model: str, api_key: str, base_url: str = ""):
        super().__init__(model, api_key, base_url)
        self.client = AsyncAnthropic(api_key=api_key)

    async def chat(self, messages: list[dict]) -> str:
        # Separate system message from conversation
        system_prompt = ""
        conversation = []

        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                conversation.append(msg)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt if system_prompt else None,
            messages=conversation,
        )
        # Anthropic returns a list of content blocks; extract text
        if response.content and len(response.content) > 0:
            return response.content[0].text
        return ""
