## Context

飞书 `POST /im/v1/messages` 接口在使用 `user_access_token` 以用户身份发送消息时，要求同时持有 `im:message` 和 `im:message.send_as_user` 两个权限（见[官方文档](https://open.feishu.cn/document/server-docs/im-v1/message/create)）。当前 OAuth 授权 URL 未包含 `im:message.send_as_user`，导致 API 返回 `230027` 错误。

此外 `user_access_token` 有效期仅 2 小时，当前代码检测到过期后仅静默跳过，未调用 refresh_token 刷新。chat list 和 message list 接口均为分页接口，当前未处理 `has_more`/`page_token`。

## Decisions

### D1: OAuth scope 修正 — 增加 `im:message.send_as_user`

**当前 scope：**
```
im:message im:message.p2p_msg:get_as_user im:message.group_msg:get_as_user im:chat:readonly
```

**修正后 scope：**
```
im:message im:message.send_as_user im:message.p2p_msg:get_as_user im:message.group_msg:get_as_user im:chat:readonly
```

`offline_access` 经测试不需要——OIDC 端点（`/authen/v1/oidc/access_token`）默认返回 `refresh_token`。额外添加反而会触发 20027 权限不足错误。

> ⚠️ **用户侧操作**：需要先在飞书开发者后台 → 权限管理 → API 权限中搜索开通「以用户身份发送消息」权限，然后发布应用新版本。这是**用户身份敏感权限**，自建应用可能需要管理员审批。

### D2: Token 自动刷新 — 轮询前检查 + 提前刷新

**流程：**
```
_poll_once()
  ├─ is_authorized()
  │   ├─ token 存在且未过期 → 继续
  │   ├─ token 过期但 refresh_token 有效 → refresh() → 继续
  │   └─ refresh 也过期 → 记录 warn 日志，return
  └─ 正常轮询逻辑...
```

**刷新实现：**
- 调用 `POST /open-apis/authen/v1/oidc/refresh_access_token`
- 使用 `app_access_token` + `refresh_token`
- 成功后更新 `user_token` 表中的 access_token、refresh_token、expires_at
- 失败则标记为未授权，停止轮询

**提前量：** 在过期前 5 分钟触发刷新，避免在轮询中途 token 失效。

### D3: Chat list 分页遍历

飞书 `GET /im/v1/chats` 返回结构：
```json
{
  "data": {
    "items": [...],
    "has_more": true,
    "page_token": "xxx"
  }
}
```

遍历逻辑：
```
page_token = ""
do:
    GET /im/v1/chats?page_size=50&page_token={page_token}&sort_type=ByActiveTimeDesc
    处理 chats
    page_token = response.data.page_token
while response.data.has_more
```

代价：每多一页增加一次 HTTP 请求。以 100 个会话为例，2 次请求即可覆盖，仍在 10 秒轮询间隔内。

### D4: Message list 分页遍历（可选，P3 优先级）

对每个 chat 的 `GET /im/v1/messages` 同样增加 `has_more`/`page_token` 遍历。`page_size` 从 5 提高到 10，减少需要分页的概率。

## Risks / Trade-offs

| 风险 | 缓解 |
|------|------|
| 已授权用户需重新授权（新增 scope） | Web UI 个人助理页面会显示"未授权"，用户点击"重新授权"即可 |
| `send_as_user` 权限需要管理员审批 | 配置指南文档已说明此步骤；若无法审批则此模式仍不可用 |
| 分页增加 API 请求量 | Chat list 分页次数 = ceil(chat_count / 50)，远低于 1000次/分钟 限制 |
| refresh 调用可能失败（网络/令牌撤销） | 失败后记录 warn 日志，轮询静默停止，等待用户重新授权 |
