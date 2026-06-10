## 1. Database & Config

- [x] 1.1 Add `user_token` table to `app/database.py` — single-row table with access_token, refresh_token, expires_at, open_id
- [x] 1.2 Add OAuth config to `app/config.py` — `FEISHU_REDIRECT_URI`

## 2. Token Manager

- [x] 2.1 Create `app/services/token_manager.py` — store/load/refresh tokens, check expiry, mark invalid

## 3. OAuth Routes

- [x] 3.1 Create `app/api/oauth.py` — `GET /api/oauth/login` (redirect to Feishu authorize page), `GET /api/oauth/callback` (exchange code for token, persist via TokenManager)

## 4. Personal Assistant Service

- [x] 4.1 Create `app/services/personal.py` — `PersonalAssistant` class with `start()`/`stop()` lifecycle
- [x] 4.2 Implement polling loop: fetch user chats → check each chat for new messages → filter self-sent + duplicates → process via BotEngine → reply as user
- [x] 4.3 Implement message dedup with in-memory set (max 1000 message_ids)

## 5. Modify Bot Engine & Platform Adapter

- [x] 5.1 Modify `app/services/bot_engine.py`: `send_reply()` to accept optional `user_token` parameter
- [x] 5.2 Modify `app/adapters/platform/feishu.py`: `send_message()` to accept optional `user_token` and use it for API calls

## 6. Wire Everything Together

- [x] 6.1 Modify `app/main.py` — register OAuth routes, start background polling on startup, stop on shutdown

## 7. Admin API & Web UI

- [x] 7.1 Add `GET /api/admin/personal/status` endpoint — return auth status, token expiry, polling status, last poll time, chat count, today reply count
- [x] 7.2 Update `app/web/index.html` — add "🧑 个人助理" nav item in sidebar
- [x] 7.3 Update `app/web/app.js` — add `personal` page route, render auth status panel, polling status panel, stats panel, fetch state from `/api/admin/personal/status`
- [x] 7.4 Update `app/web/style.css` — minimal new styles for status badges and stat cards (reuse existing patterns)

## 8. Manual Test

- [x] 8.1 Verify OAuth flow: visit /api/oauth/login → authorize → token stored in DB
- [x] 8.2 Verify polling: send a message to the authorized user → bot auto-replies within 10 seconds
- [x] 8.3 Verify token refresh: wait for token near-expiry → check auto-refresh
- [x] 8.4 Verify Web UI: personal assistant page shows correct auth status, polling status, and stats
