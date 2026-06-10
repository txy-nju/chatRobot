from openai import AsyncOpenAI

from app.adapters.llm.base import BaseLLMClient


class DeepSeekClient(BaseLLMClient):
    """DeepSeek adapter — DeepSeek API is OpenAI-compatible."""

    def __init__(self, model: str, api_key: str, base_url: str = "https://api.deepseek.com/v1"):
        super().__init__(model, api_key, base_url)
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat(self, messages: list[dict]) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content or ""
