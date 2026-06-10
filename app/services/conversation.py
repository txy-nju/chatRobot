from collections import deque

from app.config import settings


class ConversationMemory:
    """In-memory sliding window conversation store.

    Keyed by channel_id, each value is a deque of message dicts
    with 'role' and 'content' keys. Oldest messages are dropped
    when the window exceeds window_size.
    """

    def __init__(self):
        self._store: dict[str, deque[dict]] = {}

    @property
    def window_size(self) -> int:
        return settings.WINDOW_SIZE

    def get_history(self, channel_id: str) -> list[dict]:
        """Get the conversation history for a channel as a list of message dicts."""
        if channel_id not in self._store:
            self._store[channel_id] = deque(maxlen=self.window_size)
        return list(self._store[channel_id])

    def add_message(self, channel_id: str, role: str, content: str):
        """Add a message to the channel's conversation history."""
        if channel_id not in self._store:
            self._store[channel_id] = deque(maxlen=self.window_size)
        self._store[channel_id].append({"role": role, "content": content})

    def add_user_message(self, channel_id: str, content: str):
        """Add a user message to the history."""
        self.add_message(channel_id, "user", content)

    def add_assistant_message(self, channel_id: str, content: str):
        """Add an assistant (bot) reply to the history."""
        self.add_message(channel_id, "assistant", content)

    def clear(self, channel_id: str):
        """Clear conversation history for a channel."""
        if channel_id in self._store:
            del self._store[channel_id]

    def clear_all(self):
        """Clear all conversation histories."""
        self._store.clear()


# Global conversation memory instance
memory = ConversationMemory()
