# 🤖 ChatRobot

后台自动回复机器人。收到消息后由 LLM 自动生成回复，无需人工介入。支持多 LLM 厂商切换、自定义机器人人格与回复逻辑、多平台扩展、Docker 一键部署。**群聊、私聊、代回复私信均可用。**

## 目录

- [功能特性](#功能特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
  - [环境要求](#环境要求)
  - [1. 克隆项目](#1-克隆项目)
  - [2. 配置环境变量](#2-配置环境变量)
  - [3. Docker 一键部署](#3-docker-一键部署)
  - [4. 本地开发运行](#4-本地开发运行)
- [配置说明](#配置说明)
  - [LLM 供应商配置](#llm-供应商配置)
  - [机器人行为配置](#机器人行为配置)
  - [飞书平台配置](#飞书平台配置)
  - [服务器 & 数据库配置](#服务器--数据库配置)
- [Web 管理后台](#web-管理后台)
  - [Skill 编辑器](#skill-编辑器)
  - [LLM 配置](#llm-配置)
  - [行为配置](#行为配置)
  - [平台接入](#平台接入)
  - [对话测试](#对话测试)
  - [个人助理](#个人助理)
- [Skill 编写指南](#skill-编写指南)
  - [Skill Markdown 格式](#skill-markdown-格式)
  - [示例：电商客服](#示例电商客服)
  - [表单模式 vs Markdown 模式](#表单模式-vs-markdown-模式)
- [个人助理模式（代回复私信）](#个人助理模式代回复私信)
- [飞书接入指南](#飞书接入指南)
- [API 接口文档](#api-接口文档)
  - [管理后台 API](#管理后台-api)
  - [飞书 Webhook](#飞书-webhook)
  - [健康检查](#健康检查)
- [项目结构](#项目结构)
- [扩展指南](#扩展指南)
  - [新增 LLM 供应商](#新增-llm-供应商)
  - [新增消息平台](#新增消息平台)

## 功能特性

- **多 LLM 供应商统一接口** — 支持 OpenAI、Anthropic、DeepSeek，通过环境变量自动装配，修改一个变量即可切换
- **自定义机器人人格** — 用户可定义机器人的角色、口吻、回复规则和知识库 FAQ，支持结构化表单和 Markdown 两种编辑模式
- **飞书平台接入** — 完整支持飞书事件订阅、消息接收和回复，群聊和私聊均可用
- **个人助理模式** — OAuth 授权后代理你的账号自动回复私信，他人给你发消息，机器人以你的身份回复
- **Web 管理后台** — 图形化界面管理 Skill、LLM、行为、平台和测试对话
- **滑动窗口对话记忆** — 可配置的记忆窗口，让 LLM 感知近期对话上下文
- **Docker 一键部署** — 一条命令启动，数据持久化到宿主机

## 系统架构

```
┌──────────────────────────────────────────────────────┐
│                  Docker Container                     │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │              FastAPI Application                  │ │
│  │                                                  │ │
│  │  Webhook ──▶ Platform Adapter ──▶ Bot Engine     │ │
│  │               (飞书/预留)          │              │ │
│  │                                    ▼              │ │
│  │                              ┌──────────┐        │ │
│  │                              │ LLM Client│        │ │
│  │                              │ (OpenAI / │        │ │
│  │                              │ Anthropic/│        │ │
│  │                              │ DeepSeek) │        │ │
│  │                              └──────────┘        │ │
│  │                                    ▲              │ │
│  │                              ┌──────────┐        │ │
│  │                              │  Skill    │        │ │
│  │                              │ Manager  │        │ │
│  │                              └──────────┘        │ │
│  │                                                  │ │
│  │  Web UI ◀── /admin API ◀── SQLite                │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Docker & Docker Compose（推荐）
- 或 Python 3.12+

### 1. 克隆项目

```bash
git clone <your-repo-url> chatrobot
cd chatrobot
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 LLM API Key 和飞书应用凭证（详见[配置说明](#配置说明)）。

### 3. Docker 一键部署

```bash
docker compose up -d
```

启动后访问：
- **Web 管理后台**: http://localhost:8000
- **飞书 Webhook URL**: http://your-server:8000/api/feishu/event
- **健康检查**: http://localhost:8000/api/health

### 4. 本地开发运行

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 配置说明

所有配置通过 `.env` 文件管理，也可以在 Web 管理后台修改（修改后即时生效并持久化到数据库）。

### LLM 供应商配置

| 变量 | 说明 | 示例 |
|------|------|------|
| `LLM_PROVIDER` | LLM 供应商 | `openai` / `anthropic` / `deepseek` |
| `LLM_MODEL` | 使用的模型 | `gpt-4o` / `claude-sonnet-4-6` / `deepseek-chat` |
| `OPENAI_API_KEY` | OpenAI API 密钥 | `sk-...` |
| `OPENAI_BASE_URL` | OpenAI API 地址（可选） | `https://api.openai.com/v1` |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | `sk-ant-...` |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | `sk-...` |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址（可选） | `https://api.deepseek.com/v1` |

**切换供应商示例：**

```bash
# 使用 OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-your-key

# 切换到 DeepSeek — 只改一行
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=sk-your-key
```

### 机器人行为配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TRIGGER_MODE` | 回复触发方式：`all` 所有消息 / `mention` 仅 @机器人 | `all` |
| `MAX_REPLY_LENGTH` | 回复最大字数 | `500` |
| `WINDOW_SIZE` | 对话记忆窗口（条） | `20` |
| `RESPONSE_DELAY` | 回复延迟（秒） | `0` |
| `WELCOME_MESSAGE` | 新成员欢迎语 | (空) |
| `BLACKLIST` | 黑名单词，逗号分隔 | (空) |

### 飞书平台配置

| 变量 | 说明 |
|------|------|
| `FEISHU_APP_ID` | 飞书应用 App ID |
| `FEISHU_APP_SECRET` | 飞书应用 App Secret |
| `FEISHU_VERIFICATION_TOKEN` | 事件订阅验证 Token |
| `FEISHU_ENCRYPT_KEY` | 消息加密 Key（可选） |

### OAuth 配置（个人助理模式）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `FEISHU_REDIRECT_URI` | OAuth 回调地址 | 自动检测（为空时使用请求来源地址） |

> 如果自动检测不正确（如反向代理场景），手动设置为 `http://你的域名/api/oauth/callback`

### 服务器 & 数据库配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `HOST` | 监听地址 | `0.0.0.0` |
| `PORT` | 监听端口 | `8000` |
| `DATABASE_PATH` | SQLite 数据库路径 | `data/chatrobot.db` |

## Web 管理后台

访问 `http://localhost:8000` 进入管理后台。左侧导航包含 5 个页面：

### Skill 编辑器

管理机器人的"人格"——决定 LLM 系统提示词的内容。

- **Skill 列表**：左侧展示所有 Skill，支持新建、切换、删除
- **活跃 Skill**：带绿点标记，只有一个活跃 Skill 会被用于回复生成
- **表单模式（A）**：通过结构化表单编辑角色名称、角色描述、口吻风格、回复规则、知识库 FAQ
- **Markdown 模式（B）**：直接编辑原始 Markdown 源码，完全自由
- **一键切换**：表单 ↔ Markdown 双向转换，所见即所得

### LLM 配置

配置 LLM 供应商和连接参数。

- 选择供应商（OpenAI / Anthropic / DeepSeek）
- 输入模型名称、API Key 和 Base URL
- **测试连接**：发送一条测试消息验证凭证是否有效

### 行为配置

调整机器人回复行为的各项参数。

- **触发方式**：所有消息 / 仅 @机器人
- **回复长度**：拖拽滑块设置最大字数
- **记忆窗口**：设置保留多少条历史消息
- **响应延迟**：模拟打字效果
- **欢迎语**：新成员进群自动发送
- **黑名单**：包含黑名单词的消息将被忽略

### 平台接入

管理飞书等消息平台的连接。

- 填入飞书 App ID、App Secret、验证 Token
- 显示 Webhook URL，一键复制
- 连接状态指示器

### 对话测试

在部署前测试机器人的回复效果。

- 用当前 Skill 和 LLM 配置发送测试消息
- 实时显示机器人的回复
- 展示回复字数和响应延迟
- 支持清空测试对话历史

### 个人助理

查看和管理"代回复私信"功能的状态。

- **授权状态**：显示是否已授权飞书账号，Token 到期时间
- **一键授权**：点击按钮跳转飞书授权页面，30 秒完成
- **轮询状态**：显示后台轮询运行状态、上次检查时间
- **运行统计**：监控的会话数量和今日回复条数
- **重新授权**：Token 过期后一键重新授权

## Skill 编写指南

Skill 是注入到 LLM 系统提示词中的 Markdown 文本，定义了机器人的行为方式。

### Skill Markdown 格式

```markdown
# Skill: <技能名称>

## 角色
<描述机器人的身份和职责>

## 口吻
<描述回复的语气和风格>

## 回复规则
1. <规则1>
2. <规则2>
...

## 知识库
- Q: <常见问题1>
- A: <标准回答1>
- Q: <常见问题2>
- A: <标准回答2>
```

### 示例：电商客服

```markdown
# Skill: 小明科技客服

## 角色
你是小明科技有限公司的官方客服机器人。你代表公司形象，负责解答用户关于产品的疑问、处理售后问题。

## 口吻
亲切、耐心、专业。始终使用"您"称呼用户。适当使用 emoji 让对话更友好。遇到投诉时先表达理解和歉意。

## 回复规则
1. 回复控制在 200 字以内，简明扼要
2. 如果用户情绪激动，先安抚再解决问题
3. 不知道的事情不要编造，主动引导用户联系人工客服
4. 用户提到退货时，引导其查看退货政策
5. 回答中包含操作步骤时，使用编号列表

## 知识库
- Q: 退货政策
- A: 支持 7 天无理由退货。商品需保持原包装完整，不影响二次销售。退货运费由买家承担，质量问题除外。
- Q: 发货时间
- A: 下单后 24 小时内发货（工作日）。默认使用顺丰快递，全国 2-3 天送达。
- Q: 联系方式
- A: 客服热线 400-xxx-xxxx（工作日 9:00-18:00），或发送邮件至 support@xiaomingtech.com。
- Q: 如何修改订单
- A: 未发货的订单可在「我的订单」页面自行修改地址或取消。已发货的订单需联系人工客服处理。
```

### 表单模式 vs Markdown 模式

| 特性 | 表单模式 (A) | Markdown 模式 (B) |
|------|:-----------:|:-----------------:|
| 上手难度 | 低，填表即可 | 需要了解 Markdown 语法 |
| 灵活性 | 受限于表单字段 | 完全自由 |
| 适合人群 | 普通用户 | 高级用户 |
| 自定义程度 | 中 | 高 |
| 双向转换 | ✅ 可切换到 B | ⚠️ 可切换到 A（复杂格式可能丢失） |

**建议**：新手用表单模式熟悉结构，熟练后切换到 Markdown 模式获得完全控制权。

## 个人助理模式（代回复私信）

个人助理模式让机器人代理**你的个人飞书账号**自动回复私信。与 Bot 模式的区别：

| | Bot 模式 | 个人助理模式 |
|------|----------|-------------|
| 身份 | 独立机器人应用 | 你本人的飞书账号 |
| 回复对象 | 发给机器人的消息 | 发给**你**的私信 |
| 授权方式 | 飞书事件订阅 | OAuth 用户授权 |
| 消息获取 | 事件推送（实时） | 定时轮询（10秒） |

两种模式可以**同时运行**，共享同一套 Skill 和 LLM 配置。

### 前提条件

1. 已完成 Bot 模式的基本配置（App ID、App Secret）
2. 在飞书开放平台后台，为应用开启以下**权限**：
   - `im:message` — 获取与发送单聊、群组消息
   - `im:message.p2p_msg:get_as_user` — 以用户身份获取单聊消息
3. 应用需至少设置为"**仅应用创建者可用**"（不需要全企业发布）
4. 服务器需有公网 IP 或域名（OAuth 回调需要飞书能访问）

### 操作步骤

#### 1. 打开个人助理页面

访问管理后台 → 左侧导航栏点击「🧑 个人助理」

#### 2. 点击授权

```
┌─────────────────────────────────────────┐
│  授权状态                                │
│  ● 未授权                               │
│  授权后机器人将自动回复你的飞书私信。      │
│  [🔑 前往授权]                           │
└─────────────────────────────────────────┘
```

点击「前往授权」，浏览器跳转到飞书：

```
┌───────────────────────────────────────────┐
│         飞书授权页面                        │
│                                           │
│  ChatRobot 想要访问你的消息                 │
│  是否同意？                                │
│                                           │
│  [取消]              [同意]                │
└───────────────────────────────────────────┘
```

#### 3. 点"同意"

页面自动跳回管理后台，显示"✅ 授权成功"。

#### 4. 开始使用

```
┌─────────────────────────────────────────┐
│  个人助理                                │
│                                         │
│  授权状态                                │
│  ✅ 已授权                               │
│  授权用户: ou_xxxxxx                     │
│  Token 到期: 2026-06-10 14:00           │
│  [🔄 重新授权]                           │
│                                         │
│  轮询状态                                │
│  ● 运行中                                │
│  上次轮询: 14:05:32                      │
│  监控会话: 5 个                          │
│  今日回复: 12 条                         │
└─────────────────────────────────────────┘
```

此后任何人给你的飞书发私信，机器人会在 10 秒内自动以你的身份回复。

### 完整示例

```
李四（同事）→ 张三（你，飞书私聊）:
"张三，项目文档在哪？"              [14:05:30]

ChatRobot 轮询发现新消息            [14:05:34]
  → 加载 Skill（"张三工作分身"）
  → 调 LLM 生成回复
  → 以张三身份发送

李四收到回复（发送者显示"张三"）：     [14:05:35]
"在这：https://wiki.company.com/projects/doc
搞不定了随时找我 🤙"
```

### Token 管理

| 事项 | 说明 |
|------|------|
| access_token 有效期 | 2 小时 |
| 自动刷新 | 系统在过期前自动用 refresh_token 续期 |
| refresh_token 有效期 | 约 30 天 |
| 过期处理 | poll 自动停止，Web UI 显示"未授权"，点击重新授权即可 |
| 重新授权 | 和首次授权完全相同，30 秒完成 |

### 常见问题

**Q: 怎么区分 Bot 回复和个人助理回复？**
A: 它们用不同的 conversation 记忆。Bot 的对话记忆在 Bot 和自己之间，个人助理的对话记忆在你的私聊中。

**Q: 我的飞书回复会被当作我自己的消息再次轮询到吗？**
A: 不会。系统会过滤掉你自己发送的消息（通过 open_id 匹配）。

**Q: 需要企业管理员审批吗？**
A: 测试阶段"仅应用创建者可用"不需要。如果要全企业使用，`im:message.p2p_msg:get_as_user` 权限可能需要管理员审批。

**Q: 别人能看到是机器人发的吗？**
A: 看不到。消息发送者显示为你的真实账号，和你在飞书里手动发送完全一样。

## 飞书接入指南

### 1. 创建飞书应用

1. 登录 [飞书开放平台](https://open.feishu.cn/)
2. 创建企业自建应用
3. 获取 **App ID** 和 **App Secret**

### 2. 配置机器人权限

在应用的「权限管理」页面添加以下权限：

- `im:message` — 获取消息
- `im:message:send_as_bot` — 以机器人身份发送消息
- `im:chat` — 获取群聊信息

### 3. 配置事件订阅

1. 在应用的「事件订阅」页面，填入 Webhook URL：

```
https://your-domain.com/api/feishu/event
```

2. 订阅事件：`im.message.receive_v1`（接收消息）
3. 飞书会向你的服务器发送 Challenge 验证请求，ChatRobot 会自动处理
4. 获取 **Verification Token**，填入 `.env` 文件

### 4. 发布应用

1. 在「版本管理与发布」页面创建新版本
2. 配置可用范围（选择可见人员或部门）
3. 提交审核并发布

### 5. 在飞书中使用

机器人同时支持**群聊**和**私聊**，两种场景使用相同的消息事件和回复接口，无需额外配置：

**群聊：**
1. 将机器人添加到群聊中
2. 根据配置的触发方式：
   - `all` 模式：所有消息都会收到回复
   - `mention` 模式：需要 @机器人 才会回复

**私聊（单聊）：**
1. 在飞书中搜索你的机器人名称，直接打开对话
2. 发送消息即可收到自动回复（私聊中 `TRIGGER_MODE` 配置不适用，所有消息均会回复）
3. 私聊和群聊的对话上下文天然隔离，互不影响

## API 接口文档

### 管理后台 API

所有接口前缀：`/api/admin`

#### Skill 管理

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/admin/skills` | 获取所有 Skill 列表 |
| `GET` | `/admin/skills/{id}` | 获取指定 Skill |
| `POST` | `/admin/skills` | 创建新 Skill |
| `PUT` | `/admin/skills/{id}` | 更新 Skill |
| `DELETE` | `/admin/skills/{id}` | 删除 Skill |
| `POST` | `/admin/skills/parse` | 解析 Markdown 为结构化字段 |
| `POST` | `/admin/skills/serialize` | 将结构化字段序列化为 Markdown |

#### LLM 配置

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/admin/config/llm` | 获取 LLM 配置 |
| `PUT` | `/admin/config/llm` | 更新 LLM 配置 |
| `POST` | `/admin/config/llm/test` | 测试 LLM 连接 |

#### 机器人行为配置

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/admin/config/bot` | 获取行为配置 |
| `PUT` | `/admin/config/bot` | 更新行为配置 |

#### 平台配置

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/admin/config/platform` | 获取所有平台配置 |
| `PUT` | `/admin/config/platform/{type}` | 更新指定平台配置 |

#### 对话测试

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/admin/chat/test` | 发送测试消息并获取回复 |
| `DELETE` | `/admin/conversation/{channel_id}` | 清空指定会话历史 |

### 飞书 Webhook

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/feishu/event` | 飞书事件订阅端点 |

### OAuth 授权

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/oauth/login` | 重定向到飞书 OAuth 授权页面 |
| `GET` | `/api/oauth/callback` | OAuth 回调，用 code 换取 user_access_token |

### 个人助理状态

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/admin/personal/status` | 获取授权状态、轮询状态、运行统计 |

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查，返回 `{"status": "ok"}` |

## 项目结构

```
chatrobot/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 应用入口
│   ├── config.py                # 环境变量配置
│   ├── database.py              # SQLite 数据库初始化
│   ├── api/
│   │   ├── feishu.py            # 飞书 Webhook 路由
│   │   ├── admin.py             # 管理后台 API
│   │   └── oauth.py             # OAuth 授权路由
│   ├── services/
│   │   ├── bot_engine.py        # 核心编排引擎
│   │   ├── conversation.py      # 滑动窗口对话记忆
│   │   ├── skill_manager.py     # Skill CRUD + Markdown 解析
│   │   ├── personal.py          # 个人助理轮询服务
│   │   └── token_manager.py     # OAuth Token 管理
│   ├── adapters/
│   │   ├── llm/
│   │   │   ├── base.py          # LLM 抽象基类
│   │   │   ├── openai.py        # OpenAI 适配器
│   │   │   ├── anthropic.py     # Anthropic 适配器
│   │   │   ├── deepseek.py      # DeepSeek 适配器
│   │   │   └── factory.py       # LLM 工厂
│   │   └── platform/
│   │       ├── base.py          # 平台抽象基类
│   │       └── feishu.py        # 飞书适配器
│   ├── models/
│   │   ├── skill.py             # Skill 数据模型
│   │   ├── config.py            # 配置数据模型
│   │   └── message.py           # 统一消息模型
│   └── web/
│       ├── index.html           # 管理后台 HTML
│       ├── style.css            # 样式
│       └── app.js               # SPA 逻辑
├── skills/
│   └── default.md               # 默认 Skill 模板
├── data/                        # SQLite 数据目录（运行时生成）
├── .env.example                 # 配置模板
├── Dockerfile                   # Docker 构建文件
├── docker-compose.yml           # Docker 编排文件
├── .dockerignore
└── requirements.txt
```

## 扩展指南

### 新增 LLM 供应商

1. 创建适配器文件 `app/adapters/llm/newprovider.py`：

```python
from openai import AsyncOpenAI  # 如果 API 兼容 OpenAI
from app.adapters.llm.base import BaseLLMClient

class NewProviderClient(BaseLLMClient):
    def __init__(self, model, api_key, base_url):
        super().__init__(model, api_key, base_url)
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat(self, messages):
        response = await self.client.chat.completions.create(
            model=self.model, messages=messages
        )
        return response.choices[0].message.content or ""
```

2. 在 `app/adapters/llm/factory.py` 中注册：

```python
from app.adapters.llm.newprovider import NewProviderClient

SUPPORTED_PROVIDERS = {
    "openai": OpenAIClient,
    "anthropic": AnthropicClient,
    "deepseek": DeepSeekClient,
    "newprovider": NewProviderClient,  # 新增
}
```

3. 在 `app/config.py` 和 `.env.example` 中添加对应的 API Key 配置。

### 新增消息平台

1. 创建适配器文件 `app/adapters/platform/discord.py`：

```python
from app.adapters.platform.base import BasePlatform
from app.models.message import IncomingMessage, OutgoingMessage

class DiscordAdapter(BasePlatform):
    async def verify(self, body):
        # 处理 Discord 验证
        ...

    async def parse_message(self, body):
        # 解析 Discord 消息为 IncomingMessage
        ...

    async def send_message(self, reply):
        # 发送消息到 Discord
        ...
```

2. 在 `app/services/bot_engine.py` 中注册：

```python
from app.adapters.platform.discord import DiscordAdapter

self._platforms = {
    "feishu": FeishuAdapter(),
    "discord": DiscordAdapter(),  # 新增
}
```

3. 添加对应的 API 路由处理新平台的 Webhook。
