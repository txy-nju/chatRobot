import logging

from fastapi import APIRouter, Request, HTTPException

from app.services.bot_engine import engine
from app.adapters.platform.feishu import FeishuAdapter

router = APIRouter(tags=["feishu"])
logger = logging.getLogger(__name__)

feishu = FeishuAdapter()


@router.post("/feishu/event")
async def feishu_event(request: Request):
    """Feishu event subscription webhook endpoint.

    Handles:
    1. URL verification (challenge)
    2. Message events (auto-reply)
    """
    body = await request.json()
    logger.info(f"Feishu event received: {body.get('header', {}).get('event_type', 'unknown')}")

    # 1. Handle URL verification
    challenge_resp = await feishu.verify(body)
    if challenge_resp is not None:
        return challenge_resp

    # 2. Parse incoming message
    message = await feishu.parse_message(body)
    if message is None:
        return {"code": 0, "msg": "ignored"}

    # 3. Check trigger mode
    from app.config import settings
    if settings.TRIGGER_MODE == "mention":
        # Check if bot is @mentioned (simple check: message contains @)
        if "@" not in message.content:
            return {"code": 0, "msg": "not mentioned"}

    # 4. Process through bot engine
    reply = await engine.process_message(message)
    if reply is None:
        return {"code": 0, "msg": "no reply generated"}

    # 5. Send reply
    await engine.send_reply(reply)

    return {"code": 0, "msg": "ok"}
