import logging
import time

import httpx

from app.database import get_db
from app.config import settings

logger = logging.getLogger(__name__)

FEISHU_APP_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
FEISHU_REFRESH_URL = "https://open.feishu.cn/open-apis/authen/v1/oidc/refresh_access_token"

# Refresh when token is within 5 minutes of expiry
REFRESH_BEFORE_SECONDS = 300


class TokenManager:
    """Manage user OAuth tokens: store, load, refresh, check validity."""

    @staticmethod
    async def get_app_access_token() -> str:
        """Get app_access_token using App ID and App Secret."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    FEISHU_APP_TOKEN_URL,
                    json={
                        "app_id": settings.FEISHU_APP_ID,
                        "app_secret": settings.FEISHU_APP_SECRET,
                    },
                    headers={"Content-Type": "application/json"},
                )
                data = resp.json()
                code = data.get("code", -1)
                if code != 0:
                    logger.error(f"Failed to get app_access_token: {data.get('msg')}")
                    return ""
                return data.get("app_access_token", "")
        except Exception as e:
            logger.error(f"Failed to get app_access_token: {e}")
            return ""

    @staticmethod
    async def save(access_token: str, refresh_token: str, expires_at: float,
                   open_id: str = "", display_name: str = ""):
        """Save tokens to the database.

        expires_at: if < 100000, treated as relative seconds from now.
                     if >= 100000, treated as an absolute Unix timestamp.
        """
        if expires_at < 100000:
            expires_at = time.time() + expires_at
        db = await get_db()
        try:
            await db.execute(
                """UPDATE user_token SET access_token = ?, refresh_token = ?,
                   expires_at = ?, open_id = ?, display_name = ?,
                   updated_at = datetime('now') WHERE id = 1""",
                (access_token, refresh_token, expires_at, open_id, display_name),
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
                "SELECT access_token, refresh_token, expires_at, open_id, display_name "
                "FROM user_token WHERE id = 1"
            )
            row = await cursor.fetchone()
            if row and row["access_token"]:
                return {
                    "access_token": row["access_token"],
                    "refresh_token": row["refresh_token"],
                    "expires_at": row["expires_at"],
                    "open_id": row["open_id"],
                    "display_name": row["display_name"] or "",
                }
            return None
        finally:
            await db.close()

    @staticmethod
    async def is_authorized() -> bool:
        """Check if a valid (non-expired, with buffer) token exists."""
        token = await TokenManager.load()
        if not token or not token["access_token"]:
            return False
        return token["expires_at"] > time.time() + 60  # 1 minute buffer

    @staticmethod
    async def is_near_expiry() -> bool:
        """Check if the token is within the refresh-before window (5 minutes)."""
        token = await TokenManager.load()
        if not token or not token["access_token"]:
            return False
        return token["expires_at"] <= time.time() + REFRESH_BEFORE_SECONDS

    @staticmethod
    async def refresh() -> bool:
        """Refresh the user_access_token using the stored refresh_token.

        Returns True if refresh succeeded, False otherwise.
        """
        token = await TokenManager.load()
        if not token or not token["refresh_token"]:
            logger.warning("Token refresh skipped: no refresh_token available")
            await TokenManager.clear()
            return False

        app_token = await TokenManager.get_app_access_token()
        if not app_token:
            logger.error("Token refresh failed: could not get app_access_token")
            return False

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    FEISHU_REFRESH_URL,
                    json={
                        "grant_type": "refresh_token",
                        "refresh_token": token["refresh_token"],
                    },
                    headers={
                        "Authorization": f"Bearer {app_token}",
                        "Content-Type": "application/json",
                    },
                )
                body = resp.json()

            code = body.get("code", -1)
            if code != 0:
                logger.error(f"Token refresh API error: code={code}, msg={body.get('msg')}")
                await TokenManager.clear()
                return False

            inner = body.get("data", {})
            new_access_token = inner.get("access_token", "")
            new_refresh_token = inner.get("refresh_token", "")
            expires_at = inner.get("expires_in", 0)

            if not new_access_token:
                logger.error("Token refresh returned empty access_token")
                await TokenManager.clear()
                return False

            # expires_in from this endpoint is an absolute Unix timestamp
            await TokenManager.save(
                access_token=new_access_token,
                refresh_token=new_refresh_token or token["refresh_token"],
                expires_at=expires_at,
                open_id=token.get("open_id", ""),
                display_name=token.get("display_name", ""),
            )
            logger.info("User token refreshed successfully")
            return True

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return False

    @staticmethod
    async def ensure_valid() -> bool:
        """Ensure a valid token exists. Refresh if near expiry. Returns True if ready to poll."""
        if not await TokenManager.is_authorized():
            logger.info("Token expired or missing, attempting refresh")
            return await TokenManager.refresh()

        if await TokenManager.is_near_expiry():
            logger.info("Token near expiry, refreshing proactively")
            refreshed = await TokenManager.refresh()
            return refreshed or await TokenManager.is_authorized()

        return True

    @staticmethod
    async def clear():
        """Clear stored tokens."""
        db = await get_db()
        try:
            await db.execute(
                "UPDATE user_token SET access_token = '', refresh_token = '', "
                "expires_at = 0, updated_at = datetime('now') WHERE id = 1"
            )
            await db.commit()
            logger.info("User token cleared")
        finally:
            await db.close()
