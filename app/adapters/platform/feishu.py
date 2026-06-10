import json
import logging

import lark_oapi as lark
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody

from app.adapters.platform.base import BasePlatform
from app.models.message import IncomingMessage, OutgoingMessage
from app.config import settings

logger = logging.getLogger(__name__)


class FeishuAdapter(BasePlatform):
    """Feishu (Lark) platform adapter using the official lark-oapi SDK."""

    def __init__(self):
        self.app_id = settings.FEISHU_APP_ID
        self.app_secret = settings.FEISHU_APP_SECRET

    def _get_client(self):
        return lark.Client.builder() \
            .app_id(self.app_id) \
            .app_secret(self.app_secret) \
            .build()

    async def verify(self, body: dict) -> dict | None:
        """Handle Feishu URL verification challenge."""
        if body.get("type") == "url_verification":
            token = body.get("token", "")
            challenge = body.get("challenge", "")
            # Verify the token matches
            expected_token = settings.FEISHU_VERIFICATION_TOKEN
            if expected_token and token != expected_token:
                logger.warning(f"Feishu verification token mismatch")
            return {"challenge": challenge}
        return None

    async def parse_message(self, body: dict) -> IncomingMessage | None:
        """Parse Feishu message event into IncomingMessage."""
        # Header contains event type info
        header = body.get("header", {})
        event_type = header.get("event_type", "")

        if event_type != "im.message.receive_v1":
            return None

        event = body.get("event", {})
        message = event.get("message", {})
        message_type = message.get("message_type", "")
        content_str = message.get("content", "{}")

        # Parse message content (it's a JSON string)
        try:
            content = json.loads(content_str)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Feishu message content JSON")
            return None

        # Extract text
        text = content.get("text", "")

        # Skip messages without text
        if not text:
            return None

        return IncomingMessage(
            platform="feishu",
            channel_id=message.get("chat_id", ""),
            user_id=event.get("sender", {}).get("sender_id", {}).get("open_id", ""),
            content=text,
            message_type=message_type,
            raw=body,
        )

    async def send_message(self, reply: OutgoingMessage) -> bool:
        """Send a text message to Feishu chat."""
        client = self._get_client()

        content = json.dumps({"text": reply.content})
        request = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(
                CreateMessageRequestBody.builder()
                .receive_id(reply.channel_id)
                .msg_type("text")
                .content(content)
                .build()
            ) \
            .build()

        try:
            response = client.im.v1.message.create(request)
            if response.success():
                logger.info(f"Feishu message sent to {reply.channel_id}")
                return True
            else:
                logger.error(f"Feishu message send failed: {response.msg}")
                return False
        except Exception as e:
            logger.error(f"Feishu message send error: {e}")
            return False
