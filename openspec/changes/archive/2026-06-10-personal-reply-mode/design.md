## Context

当前系统以 Bot 应用身份运行（App Access Token），只能接收发给 Bot 的消息。要实现"代理用户回复私信"，需要通过飞书 OAuth 获取 `user_access_token`，以用户身份读取消息列表并发送回复。

飞书 API 支持：
- `GET /im/v1/messages` 使用 `user_access_token` 读取用户所在会话的消息
- `POST /im/v1/messages` 使用 `user_access_token` 以用户身份发送消息
- `POST /open-apis/authen/v1/oidc/refresh_access_token` 刷新过期的 token

约束：
- 最小改动原则，复用现有 Bot Engine 管道（Skill → LLM → 回复）
- 单用户模式（一个部署实例代理一个用户）

## Goals / Non-Goals

**Goals:**
- 用户通过浏览器访问 `/api/oauth/login` 完成飞书 OAuth 授权
- 系统自动获取并存储 `user_access_token` 和 `refresh_token`
- 后台每 10 秒轮询用户消息，发现新消息后通过 Bot Engine 生成回复并以用户身份发送
- Token 过期前自动刷新

**Non-Goals:**
- 不支持多用户（一个实例代理一个用户）
- 不支持指定轮询特定会话（全自动监控所有会话）
- 不支持除飞书以外的其他平台

## Decisions

### D1: 轮询模式 — 全自动监控所有会话

**选择：轮询所有用户会话**

每 10 秒：
1. `GET /im/v1/chats` 获取用户会话列表
2. 对每个会话 `GET /im/v1/messages?page_size=5&sort_type=ByCreateTimeDesc`
3. 过滤出新消息（`create_time` > 上次轮询时间）
4. 每条新消息 → `BotEngine.process_message()` → `send_reply(user_token=...)`

备选方案：指定监控特定 chat_id。更精确但需要手动配置，后续可扩展。

### D2: Token 管理 — SQLite 单行存储

**选择：`user_token` 表，单行记录**

```sql
CREATE TABLE IF NOT EXISTS user_token (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at REAL NOT NULL,
    open_id TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

单行设计（只存一个用户），不需要考虑多租户。token 刷新失败时标记为过期，用户需重新授权。

### D3: 与 Bot 模式共存

Bot 模式（事件订阅）和个人模式（轮询）可以同时运行，互不干扰：
- Bot 模式：处理发给 Bot 的群聊/私聊消息，使用 App Token
- 个人模式：处理发给用户的私聊消息，使用 User Token
- 两个模式共享同一个 Bot Engine、Skill、LLM 配置

### D4: 消息去重 — 基于 message_id

处理过的消息 ID 存到内存 set（最多 1000 条），避免重复回复。重启后清空（可接受）。

### D5: OAuth 回调不需要公网 URL

用户手动访问 `http://localhost:8000/api/oauth/login` 触发授权，回调也是 localhost。如果部署在服务器上则用服务器地址。重定向 URL 在 `.env` 中配置。

### D6: Web UI — 个人助理状态页

在侧边栏新增「🧑 个人助理」导航，一个简洁的状态面板：
- 授权状态：已授权（显示 open_id + 过期时间）/ 未授权（显示授权按钮）
- 轮询状态：运行中 / 已停止
- 运行统计：上次轮询时间、监控会话数、今日回复数
- 授权按钮直接跳转 `/api/oauth/login`

与现有 Web UI 一致的技术选型（原生 HTML/CSS/JS），不改动其他页面。

## Risks / Trade-offs

| 风险 | 缓解 |
|------|------|
| user_access_token 过期（2h） | 每次轮询前检查过期时间，提前用 refresh_token 刷新 |
| refresh_token 过期（~30天） | 发现刷新失败时记录日志，用户下次访问 Web UI 时可看到状态 |
| API 频率限制 1000次/分钟 | 10秒轮询 + 30个会话 = 每分钟~180次请求，远低于上限 |
| 轮询延迟 10 秒 | 对异步聊天场景可接受，后续可调整为 5 秒 |
| 自己发的消息也会触发轮询 | 过滤 sender.open_id == 自己的 open_id，跳过 |

## Open Questions

- 是否需要区分"用户主动发送的消息"和"机器人代回复的消息"，避免对机器人回复再次轮询？当前方案通过在发送回复后更新 `last_poll_time` 来避免
