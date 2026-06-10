## Context

全新项目，无历史代码。目标是一个后台自动回复机器人系统，核心诉求是：多 LLM 厂商可切换、机器人人格可自定义、多平台可扩展、Docker 一键部署。

约束：
- 单租户模式（一个部署实例 = 一个机器人）
- 持久化需求仅限于 Skill 配置，对话历史为内存级（重启即忘）
- 首期仅支持飞书平台
- Python 3.12+ 虚拟环境已初始化

## Goals / Non-Goals

**Goals:**
- 提供统一的 LLM 调用接口，支持通过环境变量切换提供商（OpenAI / Anthropic / DeepSeek 等）
- 用户可通过 Web UI 自定义机器人的人格、口吻、回复规则和知识库
- 飞书平台完整接入：URL 验证、消息接收、消息回复
- 滑动窗口对话记忆，让 LLM 能感知近期对话上下文
- Docker 一键部署，无额外依赖

**Non-Goals:**
- 不支持多租户（一个容器管理多个机器人）
- 不支持文件/图片/语音消息处理（仅文本）
- 不支持流式（SSE）输出（首版用非流式）
- 不实现用户认证和权限系统（管理后台无需登录）
- 不做群聊多 @ 管理（简单模式：机器人回复所有消息或仅 @ 消息）

## Decisions

### D1: 自建 LLM 适配层 vs 使用 litellm

**选择：自建轻量适配层**

理由：
- 实际需要的厂商数量有限（3-5 个），不需要 litellm 100+ 厂商的覆盖
- 自建适配层代码量小（每个适配器约 50-80 行），维护成本低
- 减少依赖（litellm 依赖重），加快 Docker 构建和启动速度
- 接口设计极简：`chat(messages, model, **kwargs) -> str`

结构：
```
adapters/llm/
├── base.py          # BaseLLMClient (抽象基类)
├── openai.py        # OpenAI 适配器
├── anthropic.py     # Anthropic 适配器
├── deepseek.py      # DeepSeek 适配器
└── factory.py       # LLMFactory: 读 LLM_PROVIDER env 自动装配
```

备选方案：litellm — 如果未来需要接入大量非主流厂商，可以后续替换适配层实现，接口不变。

### D2: 平台适配器模式

**选择：策略模式 + 统一消息模型**

所有消息平台实现 `BasePlatform` 抽象接口：

```python
class BasePlatform(ABC):
    async def verify(self, request) -> bool        # URL 验证
    async def parse_message(self, request) -> Message  # 解析消息
    async def send_message(self, message, reply) -> None  # 发送回复
```

统一消息模型隔离平台差异：
```
IncomingMessage:  platform, channel_id, user_id, content, message_type, raw
OutgoingMessage: content, reply_to
```

飞书适配器使用官方 `lark-oapi` SDK，处理飞书特有的 challenge 验证、消息解密和消息格式转换。未来新增平台只需新增一个 adapter 文件。

### D3: Skill 系统 = Markdown 文件 + 双模式编辑器

**选择：基于 Markdown 文件的 Skill 定义，Web UI 提供表单 ↔ Markdown 双模式**

Skill 本质上是一段注入到 LLM system prompt 的文本。底层存储为 Markdown 文件：

```markdown
# Skill: <名称>
## 角色
<描述>
## 口吻
<风格描述>
## 回复规则
1. <规则1>
2. <规则2>
## 知识库
- Q: <问题>
- A: <答案>
```

方案 A（表单模式）：解析 Markdown → 渲染为结构化表单 → 用户填表 → 序列化回 Markdown
方案 B（Markdown 模式）：直接编辑原始 Markdown

两种模式共享同一份底层存储。切换时实时渲染/解析。Markdown 解析采用轻量方式（正则匹配 `## ` 标题块），不做严格 AST。

备选方案：
- YAML/JSON 结构化存储：解析简单但丢失了自然语言的表达能力，不适合"让 LLM 直接读"的场景
- 纯表单：对高级用户不够灵活

### D4: SQLite 持久化仅用于 Skill 配置

**选择：SQLite 存储 Skill 元数据和内容**

数据库表设计：

```
skills:           id, name, content(markdown), is_active, created_at, updated_at
llm_config:       id, provider, model, api_key, base_url, updated_at
bot_config:       id, trigger_mode, max_reply_length, window_size, welcome_message, blacklist
platform_config:  id, platform_type, app_id, app_secret, token, encrypt_key, is_connected
```

为什么不存对话历史：对话历史用内存 `dict[str, deque]`，重启清空。对话历史只需要短期记忆，持久化意义不大，且引入清理策略复杂性。

### D5: Web UI — 零构建步骤的 SPA

**选择：原生 HTML + 少量 JS（或 Alpine.js）+ Tailwind CSS CDN**

理由：
- 不需要 npm/webpack/vite 等构建步骤
- FastAPI 直接 serve 静态文件，整体打包进 Docker
- 管理后台不是面向终端用户的产品，界面简洁可用即可

备选方案：React/Vue — 增加构建复杂度，且对管理后台来说过度设计。

### D6: 单租户，一个环境变量文件管所有配置

**选择：`.env` 文件 + Web UI 可编辑**

LLM 配置通过环境变量设定默认值，Web UI 可以覆盖并持久化到 SQLite。启动时优先级：Web UI 配置 > 环境变量 > 默认值。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| 飞书 SDK 版本升级导致不兼容 | 固定 lark-oapi 版本号，在 CI 中做集成测试 |
| LLM 厂商 API 变更 | 适配器层隔离，变更只影响单个 adapter 文件 |
| 单租户限制未来扩展 | 架构上预留租户字段（skill 可关联 bot_id），未来升级代价小 |
| 内存对话历史重启丢失 | 明确在产品中说明，用户可自行选择是否接受 |
| Markdown 解析不完美（方案 A↔B 转换有损） | 切换时提示用户可能丢失格式，建议用户选一个模式为主 |
| API Key 明文存储 | 至少做到 API Key 在 Web UI 中用 password 字段显示为 `••••`；生产环境建议用 Docker secrets |

## Open Questions

- 是否需要支持多个 Skill 并存并允许用户在飞书群中切换？（当前设计为单 Skill，后续扩展）
- Web UI 是否需要基础 HTTP 认证？（当前设计无认证，适合内网部署）
- 飞书消息的图片/文件类型是否需要在 v2 中支持？
