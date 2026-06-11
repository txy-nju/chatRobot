## Context

`GET /im/v1/chats`（列表端点）明确不返回单聊（P2P）会话。`GET /im/v1/chats/search`（搜索端点）返回当前身份所在的所有会话，包括群聊和 P2P。但 search 端点响应中不包含 `chat_mode` 字段，无法直接区分会话类型。

解决方案：用 search 端点发现所有会话 → 对每个 chat_id 调用 get-chat 端点获取 `chat_mode` → 仅对 P2P 会话进行消息轮询和回复。

## Decisions

### D1: 用 search 端点 + get-chat 验证替换 chat list

**search 端点调用：**
```
GET /im/v1/chats/search?query=<搜索词>&page_size=100&page_token=...
```

`query` 参数必填（空字符串返回空结果）。策略：
1. 优先尝试用用户名/昵称作为 query，匹配用户所在的所有会话
2. 备选：用常见单字（如 "a"、"的"、"我"）做模糊匹配

**get-chat 验证：**
```
GET /im/v1/chats/{chat_id}
→ 响应包含 chat_mode: "group" | "p2p" | "topic"
→ 仅处理 chat_mode == "p2p" 的会话
```

### D2: 仅处理 P2P 会话

群聊已由 Bot 模式的事件订阅处理。个人助理模式聚焦于 P2P 私聊，避免重复回复。

### D3: 轮询流程

```
_poll_once():
  1. TokenManager.ensure_valid()     ← 已有（token 刷新）
  2. GET /im/v1/chats/search         ← 新（代替 /im/v1/chats）
     → 分页遍历所有结果
  3. for each chat:
       GET /im/v1/chats/{chat_id}    ← 新（获取 chat_mode）
       if chat_mode != "p2p": skip
       GET /im/v1/messages           ← 已有
       → 过滤、处理、以用户身份回复  ← 已有
```

## Risks / Trade-offs

| 风险 | 缓解 |
|------|------|
| search 端点可能也不返回 P2P | 添加清晰日志；回退方案：事件订阅 + 回复到 sender 的 open_id |
| query 参数搜索精度不确定 | 先测试常见字符；若结果太多可限制 page_size |
| 额外 get-chat 调用增加延迟 | 每 chat 一次 HTTP 请求，page_size=100 最多 100 次/轮，仍在 1000/min 限制内 |
| 用户名可能匹配到无关会话 | 通过 chat_mode 过滤确保只处理 P2P |
