import aiosqlite
from pathlib import Path

from app.config import settings

DB_PATH = Path(settings.DATABASE_PATH)


async def get_db() -> aiosqlite.Connection:
    """Get a database connection. Creates the data directory if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """Initialize the database schema on startup."""
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                is_active INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS llm_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                provider TEXT NOT NULL DEFAULT 'openai',
                model TEXT NOT NULL DEFAULT 'gpt-4o',
                api_key TEXT NOT NULL DEFAULT '',
                base_url TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS bot_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                trigger_mode TEXT NOT NULL DEFAULT 'all',
                max_reply_length INTEGER NOT NULL DEFAULT 500,
                window_size INTEGER NOT NULL DEFAULT 20,
                response_delay REAL NOT NULL DEFAULT 0.0,
                welcome_message TEXT NOT NULL DEFAULT '',
                blacklist TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS platform_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform_type TEXT NOT NULL DEFAULT 'feishu',
                app_id TEXT NOT NULL DEFAULT '',
                app_secret TEXT NOT NULL DEFAULT '',
                verification_token TEXT NOT NULL DEFAULT '',
                encrypt_key TEXT NOT NULL DEFAULT '',
                is_connected INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            -- Insert default config rows if they don't exist
            INSERT OR IGNORE INTO llm_config (id) VALUES (1);
            INSERT OR IGNORE INTO bot_config (id) VALUES (1);
        """)
        await db.commit()
    finally:
        await db.close()
