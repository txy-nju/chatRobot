import asyncio
import json
import logging
import time
from datetime import datetime

import httpx

from app.config import settings
from app.models.message import IncomingMessage
from app.services.bot_engine import engine
from app.services.token_manager import TokenManager

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
        print("=== PersonalAssistant started", flush=True)

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _poll_loop(self):
        """Main polling loop: every 10 seconds, check for new messages."""
        while self._running:
            try:
                await self._poll_once()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"=== POLL error: {e}", flush=True)

            await asyncio.sleep(10)

    async def _poll_once(self):
        if not await TokenManager.is_authorized():
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
                    params={"page_size": 50, "sort_type": "ByActiveTimeDesc"},
                )
                chats_data = resp.json()
            except Exception as e:
                print(f"=== POLL: fetch chats error: {e}", flush=True)
                return

            if chats_data.get("code") != 0:
                print(f"=== POLL: chat list error code={chats_data.get('code')} msg={chats_data.get('msg')}", flush=True)
                return

            chats = chats_data.get("data", {}).get("items", [])
            self._chat_count = len(chats)

            # 2. For each chat, check recent messages
            for chat in chats:
                chat_id = chat.get("chat_id", "")
                chat_name = chat.get("name", chat_id[:20])
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
                            "page_size": 5,
                        },
                    )
                    msg_data = msg_resp.json()
                except Exception as e:
                    print(f"=== POLL: fetch msgs error for {chat_name}: {e}", flush=True)
                    continue

                if msg_data.get("code") != 0:
                    print(f"=== POLL: msg fetch failed for {chat_name}: {msg_data.get('msg')}", flush=True)
                    continue

                messages = msg_data.get("data", {}).get("items", [])

                for msg in messages:
                    msg_id = msg.get("message_id", "")
                    msg_type = msg.get("msg_type", "")
                    sender = msg.get("sender", {})
                    sender_id = sender.get("id", "")
                    sender_type = sender.get("sender_type", "")

                    print(f"=== POLL: msg {msg_id[:16]} type={msg_type} sender={sender_id[:16] if sender_id else 'none'} chat={chat_name}", flush=True)

                    # Skip already processed
                    if msg_id in self._processed_ids:
                        continue

                    # Skip self-sent
                    if sender_type == "user" and sender_id == open_id:
                        self._processed_ids.add(msg_id)
                        continue

                    # Skip non-text
                    if msg_type != "text":
                        self._processed_ids.add(msg_id)
                        continue

                    # Extract text
                    body = msg.get("body", {})
                    content_str = body.get("content", "{}")
                    try:
                        content = json.loads(content_str)
                        text = content.get("text", "")
                    except json.JSONDecodeError:
                        text = ""

                    if not text:
                        self._processed_ids.add(msg_id)
                        continue

                    print(f"=== POLL: PROCESSING '{text[:60]}' from {sender_id[:20]}", flush=True)

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
                            print(f"=== POLL: REPLY '{reply.content[:60]}...'", flush=True)
                            await self._send_as_user(client, user_token, reply)
                            self._reply_count_today += 1
                        else:
                            print(f"=== POLL: process_message returned None", flush=True)
                    except Exception as e:
                        print(f"=== POLL: process error: {e}", flush=True)

                    # Mark processed
                    self._add_processed(msg_id)

        # Trim processed set
        if len(self._processed_ids) > self._max_processed:
            self._processed_ids = set(list(self._processed_ids)[-500:])

    def _add_processed(self, msg_id: str):
        self._processed_ids.add(msg_id)

    async def _send_as_user(self, client: httpx.AsyncClient, user_token: str, reply):
        """Send a message as the authorized user."""
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
            if data.get("code") == 0:
                print(f"=== POLL: reply sent to {reply.channel_id[:20]}", flush=True)
            else:
                print(f"=== POLL: reply send failed: {data.get('msg')}", flush=True)
        except Exception as e:
            print(f"=== POLL: reply send error: {e}", flush=True)


# Global instance
assistant = PersonalAssistant()
