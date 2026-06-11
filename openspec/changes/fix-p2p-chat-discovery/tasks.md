## 1. Replace chat list with chat search + verification

- [x] 1.1 修改 `app/services/personal.py` `_poll_once()` — 将 `GET /im/v1/chats` 替换为 `GET /im/v1/chats/search`，分页遍历
- [x] 1.2 在消息轮询循环中加入 `GET /im/v1/chats/{chat_id}` 调用，获取 `chat_mode`，仅处理 `chat_mode == "p2p"` 的会话
- [x] 1.3 将回复发送改为 `receive_id_type: "open_id"` + `receive_id: <sender_open_id>`，使回复出现在用户-发送者的 P2P 聊天中

## 2. Update spec

- [x] 2.1 更新 `openspec/specs/personal-reply/spec.md` — 同步会话发现方式的描述（search + chat_mode 过滤 + open_id 回复）

## 3. Clean up diagnostic prints

- [x] 3.1 移除 `app/services/personal.py` 和 `app/main.py` 中的调试 `print()` 语句，恢复为 `logger.info/warning/error`；在 `main.py` 中配置 `logging.basicConfig()` 确保应用日志输出到 Docker stdout

## 4. Verify

- [ ] 4.1 重建 Docker 并启动
- [ ] 4.2 从备用账号向用户发送私信 → 确认 P2P 聊天出现在 search 结果中
- [ ] 4.3 确认 10 秒内收到以用户身份发送的自动回复
- [ ] 4.4 确认回复出现在用户-发送者的 P2P 聊天中（非机器人聊天）
