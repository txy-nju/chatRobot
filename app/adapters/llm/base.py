from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """Abstract base class for all LLM provider adapters."""

    def __init__(self, model: str, api_key: str, base_url: str = ""):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def chat(self, messages: list[dict]) -> str:
        """Send messages to the LLM and return the response text.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.

        Returns:
            The LLM's response as a string.
        """
        ...
