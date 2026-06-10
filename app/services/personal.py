import asyncio
import logging
import time
from datetime import datetime

import httpx

from app.config import settings
from app.models.message import IncomingMessage
from app.services.bot_engine import engine
from app.services.token_manager import TokenManager
from app.services.skill_manager import SkillManager
from app.services.conversation import memory

logger = logging.getLogger(__name__)

FEISHU_BASE = "https://open.feishu.cn/open-apis"


class PersonalAssistant:
    """Polls user messages and auto-replies as the user via OAuth token."""

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_poll_time = 0.0
        self._processed_ids: set[str] = set()
        self._max_processed = 1000
        self._chat_count = 0
        self._reply_count_today = 0
        self._today_date = datetime.now().date()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def status(self) -> dict:
        return {
            "running": self._running,
            "last_poll_time": self._last_poll_time,
            "chat_count": self._chat_count,
            "reply_count_today": self._reply_count_today,
        }

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("PersonalAssistant started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("PersonalAssistant stopped")

    async def _poll_loop(self):
        """Main polling loop: every 10 seconds, check for new messages."""
        while self._running:
            try:
                await self._poll_once()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Poll error: {e}")

            await asyncio.sleep(10)

    async def _poll_once(self):
        print(f"=== POLL: tick, chats will be checked", flush=True)
        # Check authorization
        if not await TokenManager.is_authorized():
            print(f"=== POLL: not authorized, skipping", flush=True)
            return

        token_data = await TokenManager.load()
        if not token_data:
            return

        user_token = token_data["access_token"]
        open_id = token_data["open_id"]

        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json",
        }

        self._last_poll_time = time.time()

        # 1. Get user's chat list
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(
                    f"{FEISHU_BASE}/im/v1/chats",
                    headers=headers,
                    params={"page_size": 50},
                )
                chats_data = resp.json()
            except Exception as e:
                logger.error(f"Failed to fetch chats: {e}")
                return

            if chats_data.get("code") != 0:
                logger.warning(f"Chat list API error: {chats_data.get('msg')}")
                return

            chats = chats_data.get("data", {}).get("items", [])
            self._chat_count = len(chats)
            print(f"=== POLL: found {len(chats)} chats", flush=True)

            # 2. For each chat, check recent messages
            for chat in chats:
                chat_id = chat.get("chat_id", "")
                if not chat_id:
                    continue

                try:
                    msg_resp = await client.get(
                        f"{FEISHU_BASE}/im/v1/messages",
                        headers=headers,
                        params={
                            "container_id_type": "chat",
                            "container_id": chat_id,
                            "sort_type": "ByCreateTimeDesc",
                            "page_size": 3,
                        },
                    )
                    msg_data = msg_resp.json()
                except Exception as e:
                    logger.error(f"Failed to fetch messages for {chat_id}: {e}")
                    continue

                if msg_data.get("code") != 0:
                    print(f"=== POLL: msg fetch failed for {chat_id[:12]}... code={msg_data.get('code')} msg={msg_data.get('msg')}", flush=True)
                    continue

                messages = msg_data.get("data", {}).get("items", [])
                if messages:
                    print(f"=== POLL: chat {chat_id[:12]}... has {len(messages)} recent msgs", flush=True)

                for msg in messages:
                    msg_id = msg.get("message_id", "")
                    msg_type = msg.get("msg_type", "")
                    create_time_str = msg.get("create_time", "")
                    sender = msg.get("sender", {})
                    sender_id = sender.get("id", "")
                    sender_type = sender.get("sender_type", "")

                    # Diagnostic
                    skip_reason = ""
                    if msg_id in self._processed_ids:
                        skip_reason = "already_processed"
                    elif sender_type == "user" and sender_id == open_id:
                        skip_reason = f"self_sent(sender={sender_id})"
                    elif msg_type != "text":
                        skip_reason = f"non_text({msg_type})"
                    if skip_reason:
                        print(f"=== POLL: SKIP msg {msg_id[:8]}... reason={skip_reason}", flush=True)

                    # Skip already processed
                    if msg_id in self._processed_ids:
                        continue

                    # Skip self-sent messages
                    if sender_type == "user" and sender_id == open_id:
                        self._processed_ids.add(msg_id)
                        continue

                    # Skip non-text messages
                    if msg_type != "text":
                        self._processed_ids.add(msg_id)
                        continue

                    # Extract text content
                    body = msg.get("body", {})
                    content_str = body.get("content", "{}")
                    import json
                    try:
                        content = json.loads(content_str)
                        text = content.get("text", "")
                    except json.JSONDecodeError:
                        text = ""

                    if not text:
                        self._processed_ids.add(msg_id)
                        continue

                    print(f"=== PERSONAL MODE: processing message from {sender_id} in {chat_id}: {text[:50]}...", flush=True)

                    # Process through bot engine
                    incoming = IncomingMessage(
                        platform="feishu",
                        channel_id=chat_id,
                        user_id=sender_id,
                        content=text,
                        message_type="text",
                        raw=msg,
                    )

                    try:
                        reply = await engine.process_message(incoming)
                        if reply and reply.content:
                            print(f"=== PERSONAL MODE: reply generated ({len(reply.content)} chars), sending...", flush=True)
                            await self._send_as_user(client, user_token, reply)
                            self._reply_count_today += 1
                        else:
                            print(f"=== PERSONAL MODE: process_message returned None or empty", flush=True)
                    except Exception as e:
                        print(f"=== PERSONAL MODE: error={e}", flush=True)
                        logger.error(f"Error processing personal message: {e}")

                    # Mark as processed
                    self._add_processed(msg_id)

        # Trim processed set
        if len(self._processed_ids) > self._max_processed:
            self._processed_ids = set(list(self._processed_ids)[-500:])

    def _add_processed(self, msg_id: str):
        self._processed_ids.add(msg_id)

    async def _send_as_user(self, client: httpx.AsyncClient, user_token: str, reply):
        """Send a message as the authorized user."""
        import json
        content = json.dumps({"text": reply.content})
        try:
            resp = await client.post(
                f"{FEISHU_BASE}/im/v1/messages",
                headers={
                    "Authorization": f"Bearer {user_token}",
                    "Content-Type": "application/json",
                },
                params={"receive_id_type": "chat_id"},
                json={
                    "receive_id": reply.channel_id,
                    "msg_type": "text",
                    "content": content,
                },
            )
            data = resp.json()
            if data.get("code") != 0:
                logger.error(f"Failed to send personal reply: {data.get('msg')}")
            else:
                logger.info(f"Personal reply sent to {reply.channel_id}")
        except Exception as e:
            logger.error(f"Send error: {e}")


# Global instance
assistant = PersonalAssistant()
