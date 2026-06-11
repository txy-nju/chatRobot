import asyncio
import json
import logging
import time

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
        if not await TokenManager.is_authorized():
            return

        # Ensure token is valid — refresh proactively if near expiry
        if not await TokenManager.ensure_valid():
            logger.warning("Cannot ensure valid token, skipping poll cycle")
            return

        token_data = await TokenManager.load()
        if not token_data:
            return

        user_token = token_data["access_token"]
        open_id = token_data["open_id"]
        display_name = token_data.get("display_name", "")

        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json",
        }

        self._last_poll_time = time.time()

        async with httpx.AsyncClient(timeout=15) as client:
            # 1. Discover chats via search endpoint (includes P2P)
            search_results = await self._fetch_chats_via_search(client, headers, display_name)
            if search_results is None:
                return

            # 2. For each chat, verify chat_mode and only process P2P chats
            p2p_count = 0
            for chat in search_results:
                chat_id = chat.get("chat_id", "")
                if not chat_id:
                    continue

                # Verify chat_mode via get-chat endpoint
                chat_mode = await self._get_chat_mode(client, headers, chat_id)
                if chat_mode != "p2p":
                    continue
                p2p_count += 1

                # Process recent messages in this P2P chat
                await self._process_chat_messages(
                    client, headers, chat_id, open_id, user_token
                )

            self._chat_count = p2p_count

        # Trim processed set
        if len(self._processed_ids) > self._max_processed:
            self._processed_ids = set(list(self._processed_ids)[-500:])

    async def _fetch_chats_via_search(
        self, client: httpx.AsyncClient, headers: dict, query: str = ""
    ) -> list[dict] | None:
        """Fetch all visible chats via the search endpoint (includes P2P).

        Requires a non-empty query to return results. Uses the user's
        display name to find all chats they participate in.
        """
        if not query:
            logger.warning("Chat search skipped: no display name available for query")
            return None

        all_chats = []
        page_token = ""
        while True:
            try:
                params = {
                    "page_size": 100,
                    "query": query,
                }
                if page_token:
                    params["page_token"] = page_token
                resp = await client.get(
                    f"{FEISHU_BASE}/im/v1/chats/search",
                    headers=headers,
                    params=params,
                )
                chats_data = resp.json()
            except Exception as e:
                logger.error(f"Failed to search chats: {e}")
                return None

            code = chats_data.get("code", -1)
            if code != 0:
                logger.warning(
                    f"Chat search API error: code={code}, msg={chats_data.get('msg')}"
                )
                return None

            data_block = chats_data.get("data", {})
            items = data_block.get("items", [])
            all_chats.extend(items)
            logger.debug(
                f"Chat search page: {len(items)} results, has_more={data_block.get('has_more')}"
            )

            if not data_block.get("has_more"):
                break
            page_token = data_block.get("page_token", "")
            if not page_token:
                break

        logger.info(f"Chat search returned {len(all_chats)} total chats")
        return all_chats

    async def _get_chat_mode(
        self, client: httpx.AsyncClient, headers: dict, chat_id: str
    ) -> str:
        """Get the chat_mode for a given chat_id. Returns 'p2p', 'group', 'topic', or ''."""
        try:
            resp = await client.get(
                f"{FEISHU_BASE}/im/v1/chats/{chat_id}",
                headers=headers,
            )
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("chat_mode", "")
        except Exception as e:
            logger.error(f"Failed to get chat info for {chat_id[:20]}...: {e}")
        return ""

    async def _process_chat_messages(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        chat_id: str,
        open_id: str,
        user_token: str,
    ):
        """Fetch and process messages for a single P2P chat."""
        msg_page_token = ""
        while True:
            try:
                msg_params = {
                    "container_id_type": "chat",
                    "container_id": chat_id,
                    "sort_type": "ByCreateTimeDesc",
                    "page_size": 10,
                }
                if msg_page_token:
                    msg_params["page_token"] = msg_page_token
                msg_resp = await client.get(
                    f"{FEISHU_BASE}/im/v1/messages",
                    headers=headers,
                    params=msg_params,
                )
                msg_data = msg_resp.json()
            except Exception as e:
                logger.error(f"Failed to fetch messages for {chat_id[:20]}...: {e}")
                break

            if msg_data.get("code") != 0:
                break

            msg_data_block = msg_data.get("data", {})
            messages = msg_data_block.get("items", [])

            for msg in messages:
                msg_id = msg.get("message_id", "")
                msg_type = msg.get("msg_type", "")
                sender = msg.get("sender", {})
                sender_id = sender.get("id", "")
                sender_type = sender.get("sender_type", "")

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

                logger.info(f"Personal mode: processing '{text[:60]}' from {sender_id}")

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
                        await self._send_as_user(client, user_token, reply, sender_id)
                        self._reply_count_today += 1
                except Exception as e:
                    logger.error(f"Error processing personal message: {e}")

                self._processed_ids.add(msg_id)

            # Check message pagination
            if not msg_data_block.get("has_more"):
                break
            msg_page_token = msg_data_block.get("page_token", "")
            if not msg_page_token:
                break

    async def _send_as_user(
        self,
        client: httpx.AsyncClient,
        user_token: str,
        reply,
        sender_open_id: str = "",
    ):
        """Send a message as the authorized user.

        Uses receive_id_type='open_id' so the reply appears in the
        user-sender P2P chat, not in a bot chat.
        """
        content = json.dumps({"text": reply.content})
        receive_id = sender_open_id or reply.channel_id
        receive_id_type = "open_id" if sender_open_id else "chat_id"

        try:
            resp = await client.post(
                f"{FEISHU_BASE}/im/v1/messages",
                headers={
                    "Authorization": f"Bearer {user_token}",
                    "Content-Type": "application/json",
                },
                params={"receive_id_type": receive_id_type},
                json={
                    "receive_id": receive_id,
                    "msg_type": "text",
                    "content": content,
                },
            )
            data = resp.json()
            if data.get("code") != 0:
                logger.error(f"Reply send failed: code={data.get('code')}, msg={data.get('msg')}")
            else:
                logger.info(f"Personal reply sent to {receive_id_type}={receive_id}")
        except Exception as e:
            logger.error(f"Reply send error: {e}")


# Global instance
assistant = PersonalAssistant()
