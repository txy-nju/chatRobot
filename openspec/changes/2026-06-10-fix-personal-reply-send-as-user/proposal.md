## Why

当前个人助理模式无法以用户名义自动回复私信。根本原因是 OAuth 授权时缺少 `im:message.send_as_user` scope，导致飞书 API（`POST /im/v1/messages` + `user_access_token`）返回错误码 230027 拒绝发送。此外 token 自动刷新未实现、chat list 缺少分页遍历等问题也影响长期稳定运行。

## What Changes

- **修复** `app/api/oauth.py`：OAuth scope 增加 `im:message.send_as_user` 和 `offline_access`
- **新增** `app/services/token_manager.py`：实现 `refresh()` 方法，用 refresh_token 刷新 access_token
- **修改** `app/services/personal.py`：轮询前先检查并刷新 token，chat list 增加分页遍历（has_more / page_token），message list 增加分页遍历
- **修改** `openspec/specs/personal-reply/spec.md`：scope 描述同步更新

## Capabilities

### Modified Capabilities

- `personal-reply`：修复 OAuth scope 缺失、新增 token 自动刷新、新增 API 分页遍历

## Impact

- 修改文件：`app/api/oauth.py`、`app/services/personal.py`、`app/services/token_manager.py`
- 不改文件：bot_engine、Feishu adapter、config、database、admin API、Web UI
- 已授权用户需**重新授权**（因为需要新的 scope），旧 token 将因缺少 `im:message.send_as_user` 而无法发送消息
