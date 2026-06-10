import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_db
from app.services.skill_manager import SkillManager
from app.services.bot_engine import engine
from app.adapters.llm.factory import LLMFactory
from app.config import settings
from app.services.conversation import memory

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


# ── Request Models ──

class SkillCreate(BaseModel):
    name: str
    content: str = ""
    is_active: bool = False


class SkillUpdate(BaseModel):
    name: str | None = None
    content: str | None = None
    is_active: bool | None = None


class SkillParseRequest(BaseModel):
    content: str


class SkillSerializeRequest(BaseModel):
    name: str = ""
    role: str = ""
    tone: str = ""
    rules: list[str] = []
    faq: list[dict] = []


class LLMConfigUpdate(BaseModel):
    provider: str
    model: str
    api_key: str
    base_url: str = ""


class LLMTestRequest(BaseModel):
    message: str = "Hello, this is a test message."


class BotConfigUpdate(BaseModel):
    trigger_mode: str = "all"
    max_reply_length: int = 500
    window_size: int = 20
    response_delay: float = 0.0
    welcome_message: str = ""
    blacklist: str = ""


class PlatformConfigUpdate(BaseModel):
    app_id: str
    app_secret: str
    verification_token: str
    encrypt_key: str = ""


class ChatTestRequest(BaseModel):
    message: str


# ── Skill Endpoints ──

@router.get("/skills")
async def list_skills():
    """Get all skills."""
    skills = await SkillManager.get_all()
    return {"skills": skills}


@router.get("/skills/{skill_id}")
async def get_skill(skill_id: int):
    """Get a specific skill by ID."""
    skill = await SkillManager.get_by_id(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"skill": skill}


@router.post("/skills")
async def create_skill(data: SkillCreate):
    """Create a new skill."""
    skill_id = await SkillManager.create(
        name=data.name,
        content=data.content,
        is_active=data.is_active,
    )
    skill = await SkillManager.get_by_id(skill_id)
    return {"skill": skill}


@router.put("/skills/{skill_id}")
async def update_skill(skill_id: int, data: SkillUpdate):
    """Update an existing skill."""
    success = await SkillManager.update(
        skill_id=skill_id,
        name=data.name,
        content=data.content,
        is_active=data.is_active,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Skill not found or no changes")
    skill = await SkillManager.get_by_id(skill_id)
    return {"skill": skill}


@router.delete("/skills/{skill_id}")
async def delete_skill(skill_id: int):
    """Delete a skill."""
    success = await SkillManager.delete(skill_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete skill: not found or is the only active skill",
        )
    return {"ok": True}


# ── Markdown Parse / Serialize ──

@router.post("/skills/parse")
async def parse_skill_markdown(data: SkillParseRequest):
    """Parse Markdown content into structured skill fields."""
    parsed = SkillManager.parse_markdown(data.content)
    return {"parsed": parsed}


@router.post("/skills/serialize")
async def serialize_skill_fields(data: SkillSerializeRequest):
    """Serialize structured fields into Markdown content."""
    markdown = SkillManager.serialize_to_markdown(data.model_dump())
    return {"content": markdown}


# ── LLM Config Endpoints ──

@router.get("/config/llm")
async def get_llm_config():
    """Get the current LLM configuration from the database."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM llm_config WHERE id = 1")
        row = await cursor.fetchone()
        if row:
            return {"config": dict(row)}
        return {"config": {"provider": "openai", "model": "gpt-4o", "api_key": "", "base_url": ""}}
    finally:
        await db.close()


@router.put("/config/llm")
async def update_llm_config(data: LLMConfigUpdate):
    """Update the LLM configuration."""
    db = await get_db()
    try:
        await db.execute(
            """UPDATE llm_config SET provider = ?, model = ?, api_key = ?, base_url = ?,
               updated_at = datetime('now') WHERE id = 1""",
            (data.provider, data.model, data.api_key, data.base_url),
        )
        await db.commit()

        # Update runtime settings
        settings.LLM_PROVIDER = data.provider
        settings.LLM_MODEL = data.model
        engine.reload_llm_client()
    finally:
        await db.close()
    return {"ok": True}


@router.post("/config/llm/test")
async def test_llm_connection(data: LLMTestRequest):
    """Test the LLM connection with a simple message."""
    try:
        client = LLMFactory.create()
        reply = await client.chat([
            {"role": "user", "content": data.message}
        ])
        return {"ok": True, "reply": reply}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Bot Config Endpoints ──

@router.get("/config/bot")
async def get_bot_config():
    """Get the current bot behavior configuration."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM bot_config WHERE id = 1")
        row = await cursor.fetchone()
        if row:
            return {"config": dict(row)}
        return {"config": {}}
    finally:
        await db.close()


@router.put("/config/bot")
async def update_bot_config(data: BotConfigUpdate):
    """Update the bot behavior configuration."""
    db = await get_db()
    try:
        await db.execute(
            """UPDATE bot_config SET trigger_mode = ?, max_reply_length = ?,
               window_size = ?, response_delay = ?, welcome_message = ?, blacklist = ?,
               updated_at = datetime('now') WHERE id = 1""",
            (data.trigger_mode, data.max_reply_length, data.window_size,
             data.response_delay, data.welcome_message, data.blacklist),
        )
        await db.commit()

        # Update runtime settings
        settings.TRIGGER_MODE = data.trigger_mode
        settings.MAX_REPLY_LENGTH = data.max_reply_length
        settings.WINDOW_SIZE = data.window_size
        settings.WELCOME_MESSAGE = data.welcome_message
        settings.BLACKLIST = [w.strip() for w in data.blacklist.split(",") if w.strip()]
    finally:
        await db.close()
    return {"ok": True}


# ── Platform Config Endpoints ──

@router.get("/config/platform")
async def get_platform_config():
    """Get platform configurations."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM platform_config ORDER BY id")
        rows = await cursor.fetchall()
        configs = [dict(row) for row in rows]
        return {"configs": configs}
    finally:
        await db.close()


@router.put("/config/platform/{platform_type}")
async def update_platform_config(platform_type: str, data: PlatformConfigUpdate):
    """Update a platform configuration."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id FROM platform_config WHERE platform_type = ?",
            (platform_type,),
        )
        row = await cursor.fetchone()

        if row:
            await db.execute(
                """UPDATE platform_config SET app_id = ?, app_secret = ?,
                   verification_token = ?, encrypt_key = ?, updated_at = datetime('now')
                   WHERE platform_type = ?""",
                (data.app_id, data.app_secret, data.verification_token,
                 data.encrypt_key, platform_type),
            )
        else:
            await db.execute(
                """INSERT INTO platform_config
                   (platform_type, app_id, app_secret, verification_token, encrypt_key)
                   VALUES (?, ?, ?, ?, ?)""",
                (platform_type, data.app_id, data.app_secret,
                 data.verification_token, data.encrypt_key),
            )
        await db.commit()

        # Update runtime settings for Feishu
        if platform_type == "feishu":
            settings.FEISHU_APP_ID = data.app_id
            settings.FEISHU_APP_SECRET = data.app_secret
            settings.FEISHU_VERIFICATION_TOKEN = data.verification_token
            settings.FEISHU_ENCRYPT_KEY = data.encrypt_key
    finally:
        await db.close()
    return {"ok": True}


# ── Chat Test Endpoint ──

@router.post("/chat/test")
async def chat_test(data: ChatTestRequest):
    """Test chat: send a message and get the bot's reply (no platform delivery)."""
    from app.models.message import IncomingMessage

    message = IncomingMessage(
        platform="test",
        channel_id="test-channel",
        user_id="test-user",
        content=data.message,
    )

    reply = await engine.process_message(message)
    if reply is None:
        return {"ok": False, "error": "No reply generated"}

    return {
        "ok": True,
        "reply": reply.content,
        "length": len(reply.content),
    }


# ── Conversation Management ──

@router.delete("/conversation/{channel_id}")
async def clear_conversation(channel_id: str):
    """Clear conversation history for a channel."""
    memory.clear(channel_id)
    return {"ok": True}
