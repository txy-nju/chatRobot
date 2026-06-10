from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LLMConfig:
    id: int | None = None
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: str = ""
    base_url: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BotConfig:
    id: int | None = None
    trigger_mode: str = "all"  # "all" or "mention"
    max_reply_length: int = 500
    window_size: int = 20
    response_delay: float = 0.0
    welcome_message: str = ""
    blacklist: str = ""  # comma-separated keywords
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PlatformConfig:
    id: int | None = None
    platform_type: str = "feishu"
    app_id: str = ""
    app_secret: str = ""
    verification_token: str = ""
    encrypt_key: str = ""
    is_connected: bool = False
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
