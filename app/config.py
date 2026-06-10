import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    # Anthropic
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # DeepSeek
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

    # Bot behavior
    TRIGGER_MODE: str = os.getenv("TRIGGER_MODE", "all")  # "all" or "mention"
    MAX_REPLY_LENGTH: int = int(os.getenv("MAX_REPLY_LENGTH", "500"))
    WINDOW_SIZE: int = int(os.getenv("WINDOW_SIZE", "20"))
    RESPONSE_DELAY: float = float(os.getenv("RESPONSE_DELAY", "0"))
    WELCOME_MESSAGE: str = os.getenv("WELCOME_MESSAGE", "")
    BLACKLIST: list[str] = [w.strip() for w in os.getenv("BLACKLIST", "").split(",") if w.strip()]

    # Feishu
    FEISHU_APP_ID: str = os.getenv("FEISHU_APP_ID", "")
    FEISHU_APP_SECRET: str = os.getenv("FEISHU_APP_SECRET", "")
    FEISHU_VERIFICATION_TOKEN: str = os.getenv("FEISHU_VERIFICATION_TOKEN", "")
    FEISHU_ENCRYPT_KEY: str = os.getenv("FEISHU_ENCRYPT_KEY", "")

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/chatrobot.db")

    @property
    def llm_api_key(self) -> str:
        """Get the API key for the current LLM provider."""
        key_map = {
            "openai": self.OPENAI_API_KEY,
            "anthropic": self.ANTHROPIC_API_KEY,
            "deepseek": self.DEEPSEEK_API_KEY,
        }
        return key_map.get(self.LLM_PROVIDER, "")

    @property
    def llm_base_url(self) -> str:
        """Get the base URL for the current LLM provider."""
        url_map = {
            "openai": self.OPENAI_BASE_URL,
            "deepseek": self.DEEPSEEK_BASE_URL,
        }
        return url_map.get(self.LLM_PROVIDER, "")


settings = Settings()
