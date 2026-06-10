## 1. Project Setup

- [x] 1.1 Create project directory structure (`app/`, `app/api/`, `app/services/`, `app/adapters/llm/`, `app/adapters/platform/`, `app/models/`, `app/web/`, `skills/`)
- [x] 1.2 Create `requirements.txt` with dependencies: fastapi, uvicorn, lark-oapi, openai, anthropic, python-dotenv, aiosqlite
- [x] 1.3 Create `app/config.py` — load environment variables via `python-dotenv`, define `Settings` class with all config fields
- [x] 1.4 Create `.env.example` with all required and optional environment variables documented
- [x] 1.5 Create `app/main.py` — FastAPI app entry point with static file serving for Web UI

## 2. LLM Provider Adapter Layer

- [x] 2.1 Create `app/adapters/llm/base.py` — `BaseLLMClient` abstract class with `async chat(messages: list[dict]) -> str` interface
- [x] 2.2 Create `app/adapters/llm/openai.py` — OpenAI adapter implementing `BaseLLMClient`
- [x] 2.3 Create `app/adapters/llm/anthropic.py` — Anthropic adapter implementing `BaseLLMClient`
- [x] 2.4 Create `app/adapters/llm/deepseek.py` — DeepSeek adapter (OpenAI-compatible) implementing `BaseLLMClient`
- [x] 2.5 Create `app/adapters/llm/factory.py` — `LLMFactory` that reads `LLM_PROVIDER` env var and returns the correct adapter instance

## 3. Data Models & Database

- [x] 3.1 Create `app/models/skill.py` — Skill data model (id, name, content, is_active, timestamps)
- [x] 3.2 Create `app/models/config.py` — LLM config, bot config, platform config data models
- [x] 3.3 Create `app/database.py` — SQLite initialization with `aiosqlite`, table creation, migration on startup

## 4. Skill System

- [x] 4.1 Create `app/services/skill_manager.py` — Skill CRUD operations (create, read, update, delete, list, set_active)
- [x] 4.2 Implement Markdown parsing (extract sections: 角色, 口吻, 回复规则, 知识库 from raw markdown)
- [x] 4.3 Implement Markdown serialization (form fields → valid markdown output)
- [x] 4.4 Create default skill markdown file at `skills/default.md`

## 5. Platform Adapter Layer

- [x] 5.1 Create `app/adapters/platform/base.py` — `BasePlatform` abstract class with `verify()`, `parse_message()`, `send_message()` interface
- [x] 5.2 Create `app/models/message.py` — `IncomingMessage` and `OutgoingMessage` data classes
- [x] 5.3 Create `app/adapters/platform/feishu.py` — Feishu adapter using `lark-oapi` SDK: URL challenge verification, message parsing, message sending

## 6. Bot Engine Core

- [x] 6.1 Create `app/services/conversation.py` — In-memory sliding window conversation memory (`dict[str, deque]`, configurable window size)
- [x] 6.2 Create `app/services/bot_engine.py` — Core pipeline: receive message → load skill → build prompt → call LLM → send reply

## 7. API Routes

- [x] 7.1 Create `app/api/feishu.py` — Feishu webhook endpoint (`POST /api/feishu/event`): URL verification + message event handling
- [x] 7.2 Create `app/api/admin.py` — Admin API endpoints: Skill CRUD, LLM config get/set/test, bot config get/set, platform config get/set
- [x] 7.3 Create `GET /api/health` — Health check endpoint returning `{"status": "ok"}`

## 8. Web Admin UI

- [x] 8.1 Create `app/web/index.html` — Main HTML structure with sidebar navigation and content panel
- [x] 8.2 Create `app/web/style.css` — Styling for the admin UI (clean, functional, responsive)
- [x] 8.3 Create `app/web/app.js` — Single-page app logic: page routing, API calls, form handling
- [x] 8.4 Implement Skill editor page — Skill list sidebar, form mode (fields: name, description, tone, rules, FAQ), Markdown mode (raw textarea), mode toggle switch, save button
- [x] 8.5 Implement LLM config page — Provider dropdown, model dropdown (dynamic), API key input (masked), base URL input, test connection button
- [x] 8.6 Implement Bot behavior page — Trigger mode toggle, max length slider, window size input, welcome message, blacklist editor
- [x] 8.7 Implement Platform config page — Feishu config form with App ID/Secret/Token, webhook URL display with copy button, connection status indicator
- [x] 8.8 Implement Chat test console — Message input, send button, conversation display area with user/bot bubbles, clear button, metadata display (latency, word count)

## 9. Docker Deployment

- [x] 9.1 Create `Dockerfile` — Multi-stage or single-stage build with Python 3.12, dependency install, app copy, uvicorn start command
- [x] 9.2 Create `docker-compose.yml` — Service definition with port mapping (8000), env file, SQLite volume mount
- [x] 9.3 Create `.dockerignore` — Exclude .venv, .git, __pycache__, .idea, etc.

## 10. Testing & Polish

- [x] 10.1 Manually test LLM adapters with real API keys for each provider
- [x] 10.2 Manually test Feishu webhook flow with a Feishu test app
- [x] 10.3 Manually test Web UI: create/edit/delete skills, switch modes, change config, test chat console
- [x] 10.4 Verify Docker build and startup, confirm Web UI and API are accessible
- [x] 10.5 Verify skill data persists across Docker container restarts
