from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Skill:
    id: int | None = None
    name: str = ""
    content: str = ""
    is_active: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
