## Why

当前 Bot 只能以独立应用身份回复发给自己的消息。需要支持用户 OAuth 授权后，机器人代理用户账号自动回复私信，实现"代你回复"的个人助理模式。

## What Changes

- 新增飞书 OAuth 用户授权流程：用户访问授权链接完成飞书授权，服务器获取并存储 `user_access_token` 和 `refresh_token`
- 新增个人消息轮询服务：后台定时（默认10秒）轮询用户的消息列表，检查新消息并自动回复
- 新增 `user_token` 数据库表：存储 token、过期时间等
- 新增 Web UI「个人助理」页面：显示授权状态、轮询状态、今日回复数，支持一键授权/重新授权
- **修改** `bot_engine.py`：`send_reply` 支持以用户身份发送消息
- **修改** `app/main.py`：注册 OAuth 路由，启动后台轮询任务
- **修改** `app/config.py`：新增 OAuth 回调地址配置项
- **修改** `app/database.py`：新增 `user_token` 表

## Capabilities

### New Capabilities

- `personal-reply`: 个人助理回复模式。包含飞书 OAuth 授权（获取 user_access_token）、Token 管理（存储与自动刷新）、消息轮询（定时检查新消息并以用户身份自动回复）

### Modified Capabilities

- `admin-webui`: 新增「个人助理」导航页面，展示 OAuth 授权状态、轮询状态、运行统计，提供授权/重新授权入口

## Impact

- 新增文件：`app/services/personal.py`、`app/services/token_manager.py`、`app/api/oauth.py`
- 修改文件：`app/main.py`、`app/config.py`、`app/database.py`、`app/services/bot_engine.py`、`app/adapters/platform/feishu.py`、`app/web/index.html`、`app/web/style.css`、`app/web/app.js`
- 不改文件：LLM 适配器层、Skill 系统、对话记忆、平台适配器基础接口
