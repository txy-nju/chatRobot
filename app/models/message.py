from dataclasses import dataclass, field


@dataclass
class IncomingMessage:
    platform: str
    channel_id: str
    user_id: str
    content: str
    message_type: str = "text"
    raw: dict = field(default_factory=dict)


@dataclass
class OutgoingMessage:
    content: str
    channel_id: str
    platform: str = ""
    reply_to: IncomingMessage | None = None
