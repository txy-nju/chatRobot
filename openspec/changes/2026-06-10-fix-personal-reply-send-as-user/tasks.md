## 1. OAuth Scope 修正（P0：核心修复）

- [x] 1.1 修改 `app/api/oauth.py` `oauth_login` — scope 增加 `im:message.send_as_user` 和 `offline_access`
- [x] 1.2 更新 `openspec/specs/personal-reply/spec.md` — 授权场景的 scope 列表同步更新
- [x] 1.3 更新 `个人助理模式配置指南.md` — 权限表格增加 `im:message.send_as_user`，强调"以用户身份发消息"权限

## 2. Token 自动刷新（P1）

- [x] 2.1 在 `app/services/token_manager.py` 中新增 `refresh()` 静态方法 — 调用飞书 OIDC refresh 端点，更新数据库
- [x] 2.2 修改 `app/services/personal.py` `_poll_once()` — 轮询前调用 `TokenManager.refresh()` 检查并刷新 token（过期前 5 分钟触发）

## 3. Chat List & Message List 分页遍历（P2/P3）

- [x] 3.1 修改 `app/services/personal.py` `_poll_once()` — chat list 增加 `has_more`/`page_token` 循环遍历
- [x] 3.2 修改 `app/services/personal.py` `_poll_once()` — message list 增加 `has_more`/`page_token` 循环遍历，page_size 调整为 10

## 4. 验证

- [ ] 4.1 人工测试：重新 OAuth 授权 → 确认 scope 包含 `im:message.send_as_user` → 发送私信 → 确认 10 秒内收到以用户身份的回复
- [ ] 4.2 人工测试：将 token expires_at 改为 4 分钟后 → 触发轮询 → 确认 token 自动刷新
- [ ] 4.3 人工测试：创建 >50 个会话 → 确认 chat list 遍历所有页
