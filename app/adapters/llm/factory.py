from app.adapters.llm.base import BaseLLMClient
from app.adapters.llm.openai import OpenAIClient
from app.adapters.llm.anthropic import AnthropicClient
from app.adapters.llm.deepseek import DeepSeekClient
from app.config import settings


SUPPORTED_PROVIDERS = {
    "openai": OpenAIClient,
    "anthropic": AnthropicClient,
    "deepseek": DeepSeekClient,
}


class LLMFactory:
    """Factory that reads environment variables and auto-assembles the LLM client."""

    @staticmethod
    def create() -> BaseLLMClient:
        provider = settings.LLM_PROVIDER.lower()
        model = settings.LLM_MODEL
        api_key = settings.llm_api_key
        base_url = settings.llm_base_url

        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported LLM provider: '{provider}'. "
                f"Supported providers: {', '.join(SUPPORTED_PROVIDERS.keys())}"
            )

        if not api_key:
            env_key = f"{provider.upper()}_API_KEY"
            raise ValueError(
                f"API key not found for provider '{provider}'. "
                f"Set the {env_key} environment variable."
            )

        client_class = SUPPORTED_PROVIDERS[provider]
        return client_class(model=model, api_key=api_key, base_url=base_url)
