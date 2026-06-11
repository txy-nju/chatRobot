import logging

from app.adapters.llm.factory import LLMFactory
from app.adapters.platform.feishu import FeishuAdapter
from app.models.message import IncomingMessage, OutgoingMessage
from app.services.conversation import memory
from app.services.skill_manager import SkillManager
from app.config import settings

logger = logging.getLogger(__name__)


class BotEngine:
    """Core pipeline: receive message → load skill → build prompt → call LLM → send reply."""

    def __init__(self):
        self._llm_client = None
        self._platforms = {
            "feishu": FeishuAdapter(),
        }

    @property
    def llm_client(self):
        """Lazy-load the LLM client from factory."""
        if self._llm_client is None:
            self._llm_client = LLMFactory.create()
        return self._llm_client

    def reload_llm_client(self):
        """Force reload the LLM client (e.g., after config change)."""
        self._llm_client = None

    async def process_message(self, message: IncomingMessage) -> OutgoingMessage | None:
        """Process an incoming message through the full pipeline.

        Returns an OutgoingMessage to send, or None if the message should be ignored.
        """
        # Check blacklist
        blacklist = [w for w in settings.BLACKLIST if w]
        if any(word in message.content for word in blacklist):
            logger.info(f"Message from {message.user_id} ignored (blacklist match)")
            return None

        # Build messages for LLM
        llm_messages = []

        # 1. System prompt from active skill
        skill = await SkillManager.get_active()
        if skill and skill["content"]:
            llm_messages.append({"role": "system", "content": skill["content"]})
        else:
            llm_messages.append({
                "role": "system",
                "content": "你是一个友好的 AI 助手。请简洁、准确地回答用户的问题。"
            })

        # 2. Conversation history (sliding window)
        history = memory.get_history(message.channel_id)
        llm_messages.extend(history)

        # 3. Current user message
        llm_messages.append({"role": "user", "content": message.content})

        # Call LLM
        try:
            reply_text = await self.llm_client.chat(llm_messages)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

        if not reply_text:
            return None

        # Truncate if needed
        if len(reply_text) > settings.MAX_REPLY_LENGTH:
            reply_text = reply_text[:settings.MAX_REPLY_LENGTH]

        # Update conversation memory
        memory.add_user_message(message.channel_id, message.content)
        memory.add_assistant_message(message.channel_id, reply_text)

        # Build reply
        reply = OutgoingMessage(
            content=reply_text,
            channel_id=message.channel_id,
            platform=message.platform,
            reply_to=message,
        )

        return reply

    async def send_reply(self, reply: OutgoingMessage) -> bool:
        """Send a reply as the bot through the appropriate platform adapter."""
        platform = self._platforms.get(reply.platform)
        if platform is None:
            logger.error(f"No platform adapter for: {reply.platform}")
            return False

        return await platform.send_message(reply)

    def get_platform(self, name: str):
        """Get a platform adapter by name."""
        return self._platforms.get(name)


# Global bot engine instance
engine = BotEngine()
