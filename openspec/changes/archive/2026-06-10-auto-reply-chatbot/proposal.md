## Why

需要一个后台自动回复机器人，无需人工介入，收到消息后由 LLM 自动生成回复。现有的 LLM 聊天机器人方案要么绑定单一模型厂商，要么缺乏灵活的人格自定义能力，要么部署复杂。本项目提供一个支持多 LLM 厂商统一接入、用户可自定义机器人人格与回复逻辑、预留多平台扩展、且支持 Docker 一键部署的解决方案。

## What Changes

- 新增 LLM 供应商适配层：支持 OpenAI、Anthropic、DeepSeek 等多家模型厂商，通过环境变量自动装配，统一调用接口
- 新增平台适配层：抽象消息收发接口，首先实现飞书（Lark）平台接入
- 新增 Skill 人格系统：用户可自定义机器人的角色、口吻、回复规则和知识库，支持结构化表单编辑与 Markdown 自由编辑两种模式
- 新增 Web 管理后台：提供图形化界面管理 Skill 配置、LLM 配置、机器人行为和平台连接
- 新增 Bot 引擎核心：消息路由、滑动窗口对话记忆、LLM 调用编排
- 新增 Docker 部署方案：Dockerfile + docker-compose，一键启动

## Capabilities

### New Capabilities

- `llm-provider`: 多 LLM 供应商统一接口，支持通过环境变量自动装配（OpenAI / Anthropic / DeepSeek 等），提供统一的 chat 调用方式
- `platform-adapter`: 消息平台抽象层，定义统一的消息模型和适配器接口，首期实现飞书（Lark）适配器，预留其他平台扩展
- `skill-system`: 机器人人格自定义系统，用户可定义角色、口吻、回复规则和知识库 FAQ，支持表单编辑（A 模式）和 Markdown 编辑（B 模式），底层统一存储为 Markdown 文件，两种模式可互相转换
- `bot-engine`: 核心编排引擎，负责接收消息 → 加载 Skill → 组装对话上下文（滑动窗口）→ 调用 LLM → 发送回复的完整流程
- `admin-webui`: Web 管理后台界面，包含 Skill 编辑器（A/B 双模式）、LLM 配置面板、机器人行为配置、平台连接配置和对话测试区
- `docker-deployment`: Docker 容器化部署方案，包含 Dockerfile 和 docker-compose.yml，支持一键启动

### Modified Capabilities

<!-- 全新项目，无现有 capability 需要修改 -->

## Impact

- 全新项目，无现有代码受影响
- 技术栈：Python 3.12+、FastAPI、SQLite、飞书 Lark SDK
- 部署方式：Docker + docker-compose
