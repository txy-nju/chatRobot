import logging
import urllib.parse

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse

from app.config import settings
from app.services.token_manager import TokenManager

router = APIRouter(tags=["oauth"])
logger = logging.getLogger(__name__)

FEISHU_AUTH_URL = "https://open.feishu.cn/open-apis/authen/v1/authorize"
FEISHU_TOKEN_URL = "https://open.feishu.cn/open-apis/authen/v1/oidc/access_token"
FEISHU_APP_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"


async def _get_app_access_token() -> str:
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
            return data.get("app_access_token", "")
    except Exception as e:
        logger.error(f"Failed to get app_access_token: {e}")
        return ""


def _redirect_uri(request: Request) -> str:
    """Get the OAuth redirect URI from config, or auto-detect."""
    if settings.FEISHU_REDIRECT_URI:
        return settings.FEISHU_REDIRECT_URI
    return f"{request.base_url.scheme}://{request.base_url.netloc}/api/oauth/callback"


@router.get("/oauth/login")
async def oauth_login(request: Request):
    """Redirect user to Feishu OAuth authorization page."""
    redirect_uri = _redirect_uri(request)

    params = {
        "app_id": settings.FEISHU_APP_ID,
        "redirect_uri": redirect_uri,
        "scope": "im:message im:message.p2p_msg:get_as_user",
        "state": "feishu_oauth",
    }
    auth_url = f"{FEISHU_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=auth_url)


@router.get("/oauth/callback")
async def oauth_callback(code: str = "", state: str = "", error: str = ""):
    """Handle OAuth callback from Feishu. Exchange code for tokens.

    API response format (OIDC endpoint):
    {
        "code": 0,                    // error code at TOP level
        "msg": "success",
        "data": {
            "access_token": "eyJ...", // JWT-format token
            "refresh_token": "ur-...",
            "expires_in": 1781234567, // absolute Unix timestamp, NOT seconds!
            "token_type": "Bearer",
            "scope": "..."
        }
    }
    Note: open_id is NOT in this response; obtain separately via /authen/v1/user_info.
    """
    if error:
        logger.error(f"OAuth error: {error}")
        return HTMLResponse(
            f"<h2>授权失败</h2><p>飞书返回错误: {error}</p><p><a href='/'>返回管理后台</a></p>"
        )

    if not code:
        return HTMLResponse(
            "<h2>授权失败</h2><p>未收到授权码。</p><p><a href='/api/oauth/login'>重新授权</a></p>"
        )

    # Step 1: Get app access token
    app_token = await _get_app_access_token()
    if not app_token:
        return HTMLResponse(
            "<h2>授权失败</h2><p>无法获取应用凭证，请检查 App ID 和 App Secret 配置。</p>"
            "<p><a href='/api/oauth/login'>重试</a></p>"
        )

    try:
        # Step 2: Exchange authorization code for user tokens
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                FEISHU_TOKEN_URL,
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                },
                headers={
                    "Authorization": f"Bearer {app_token}",
                    "Content-Type": "application/json",
                },
            )
            body = resp.json()

        # Error check at TOP level (code is outside data)
        code_val = body.get("code", -1)
        if code_val != 0:
            logger.error(f"Token exchange failed: code={code_val}, msg={body.get('msg')}")
            return HTMLResponse(
                f"<h2>授权失败</h2><p>换取 token 失败 ({body.get('msg', '未知错误')})</p>"
                f"<p><a href='/api/oauth/login'>重新授权</a></p>"
            )

        # Tokens are nested inside data
        inner = body.get("data", {})
        access_token = inner.get("access_token", "")
        refresh_token = inner.get("refresh_token", "")

        # expires_in from this endpoint is an absolute Unix timestamp (seconds)
        # NOT a relative duration. Use it directly as expires_at.
        expires_at = inner.get("expires_in", 0)

        if not access_token:
            logger.error(f"Token exchange returned empty access_token: {list(inner.keys())}")
            return HTMLResponse(
                f"<h2>授权失败</h2><p>接口返回了空的 access_token</p>"
                f"<p><a href='/api/oauth/login'>重试</a></p>"
            )

        # Step 3: Get user info for open_id
        open_id = ""
        try:
            user_resp = await client.get(
                "https://open.feishu.cn/open-apis/authen/v1/user_info",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_data = user_resp.json()
            if user_data.get("code") == 0:
                open_id = user_data.get("data", {}).get("open_id", "")
        except Exception as e:
            logger.warning(f"Failed to get user_info: {e}")

        # Step 4: Store tokens
        await TokenManager.save(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            open_id=open_id,
        )

        return HTMLResponse(
            "<h2>✅ 授权成功！</h2>"
            f"<p>已成功授权，机器人将自动回复你的私信。</p>"
            f"<p>Open ID: {open_id}</p>"
            f"<p><a href='/'>返回管理后台</a></p>"
        )

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return HTMLResponse(
            f"<h2>授权失败</h2><p>网络错误: {str(e)}</p>"
            f"<p><a href='/api/oauth/login'>重试</a></p>"
        )
