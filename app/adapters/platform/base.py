from abc import ABC, abstractmethod

from app.models.message import IncomingMessage, OutgoingMessage


class BasePlatform(ABC):
    """Abstract base class for all messaging platform adapters."""

    @abstractmethod
    async def verify(self, body: dict) -> dict | None:
        """Handle platform URL verification challenge.

        Returns the verification response dict, or None if not a challenge.
        """
        ...

    @abstractmethod
    async def parse_message(self, body: dict) -> IncomingMessage | None:
        """Parse an incoming webhook payload into a unified IncomingMessage.

        Returns None if the payload should be ignored.
        """
        ...

    @abstractmethod
    async def send_message(self, reply: OutgoingMessage) -> bool:
        """Send a reply message back to the platform.

        Returns True if the send was successful.
        """
        ...
