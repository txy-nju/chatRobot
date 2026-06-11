## Why

当前个人助理模式无法发现 P2P 私聊会话。`GET /im/v1/chats`（列表端点）明确不返回单聊——飞书官方文档声明"获取到的群列表中，不包含单聊（群模式为 p2p）"。但 `GET /im/v1/chats/search`（搜索端点）没有此限制，可返回当前身份所在的所有会话，包括 P2P。

## What Changes

- **修改** `app/services/personal.py` `_poll_once()`：用 `GET /im/v1/chats/search` 替换 `GET /im/v1/chats` 来发现会话，然后对每个 chat_id 调用 `GET /im/v1/chats/{chat_id}` 获取 `chat_mode`，仅对 `chat_mode == "p2p"` 的会话轮询消息并回复
- **修改** `openspec/specs/personal-reply/spec.md`：更新消息轮询需求的会话发现方式描述

## Capabilities

### Modified Capabilities

- `personal-reply`：消息轮询服务改用 search 端点发现 P2P 会话，增加 chat_mode 过滤步骤

## Impact

- 修改文件：`app/services/personal.py`、`openspec/specs/personal-reply/spec.md`
- 不改文件：OAuth、token_manager、bot_engine、feishu adapter、admin API、Web UI
- 每次轮询额外增加每个 chat 一次 get-chat 调用（最多 100 次/轮），仍在 1000次/分钟 频率限制内
- 如果 search 端点也不返回 P2P，需要回退到事件订阅方案
