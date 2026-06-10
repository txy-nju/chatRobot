import logging
import time

from app.database import get_db

logger = logging.getLogger(__name__)


class TokenManager:
    """Manage user OAuth tokens: store, load, refresh, check validity."""

    @staticmethod
    async def save(access_token: str, refresh_token: str, expires_at: float, open_id: str = ""):
        """Save tokens to the database. expires_at is an absolute Unix timestamp."""
        db = await get_db()
        try:
            await db.execute(
                """UPDATE user_token SET access_token = ?, refresh_token = ?,
                   expires_at = ?, open_id = ?, updated_at = datetime('now') WHERE id = 1""",
                (access_token, refresh_token, expires_at, open_id),
            )
            await db.commit()
            logger.info(f"User token saved, expires_at={expires_at}")
        finally:
            await db.close()

    @staticmethod
    async def load() -> dict | None:
        """Load the current token. Returns None if no valid token exists."""
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT access_token, refresh_token, expires_at, open_id FROM user_token WHERE id = 1"
            )
            row = await cursor.fetchone()
            if row and row["access_token"]:
                return {
                    "access_token": row["access_token"],
                    "refresh_token": row["refresh_token"],
                    "expires_at": row["expires_at"],
                    "open_id": row["open_id"],
                }
            return None
        finally:
            await db.close()

    @staticmethod
    async def is_authorized() -> bool:
        """Check if a valid (non-expired) token exists."""
        token = await TokenManager.load()
        if not token or not token["access_token"]:
            return False
        return token["expires_at"] > time.time() + 60  # 1 minute buffer

    @staticmethod
    async def clear():
        """Clear stored tokens."""
        db = await get_db()
        try:
            await db.execute(
                "UPDATE user_token SET access_token = '', refresh_token = '', update_at = datetime('now') WHERE id = 1"
            )
            await db.commit()
        finally:
            await db.close()
