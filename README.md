# Warmy Agent Test

面向开发与测试团队的通用 Agent 自动化测试、安全评估与发布门禁平台。

首个落地场景是 AI 创作画布 Agent，后续通过插件扩展客服、RAG、浏览器、工作流、Coding 和语音 Agent。

## 当前状态

项目处于 M1 平台基础阶段，已完成 Monorepo 工程基线、身份认证、用户管理、项目隔离和审计日志。

当前工作见：

- [当前任务](./docs/当前任务.md)
- [开发进度与变更记录](./docs/开发进度与变更记录.md)

## 核心文档

- [产品需求文档](./docs/Agent测试平台产品需求文档-PRD.md)
- [技术架构与开发规范](./docs/Agent测试平台技术架构与开发规范.md)
- [API 文档](./docs/api/identity-and-projects.md)
- [Codex 开发指南](./docs/Codex开发指南.md)
- [AI 开发协作规范](./AGENTS.md)

## 前置条件

- Docker（含 Compose 插件）
- Node.js 22+ 和 pnpm 10+（通过 corepack 启用）
- Python 3.12+ 和 uv

## 快速开始

### 1. 安装依赖

```bash
make bootstrap
```

### 2. 启动基础设施

```bash
cp infra/compose/.env.example infra/compose/.env
docker compose --env-file infra/compose/.env -f infra/compose/compose.yaml up -d
uv run python scripts/wait_for_services.py
```

### 3. 运行数据库迁移

```bash
uv run alembic -c apps/control-api/alembic.ini upgrade head
```

### 4. 初始化超级管理员

```bash
uv run agenttest-admin create-super-admin --email admin@example.com --name Admin
```

按提示输入初始密码（至少 12 个字符），密码不会被回显或记录。

### 5. 启动后端 API

```bash
uv run uvicorn agenttest.main:app --reload --port 8000
```

API 文档：`http://localhost:8000/docs`

### 6. 启动前端

```bash
pnpm --filter @warmy/web dev
```

前端地址：`http://localhost:3000`

### 7. 登录

使用步骤 4 创建的管理员账号登录。首次登录会提示修改密码（如已设置 `must_change_password`）。

## 验证

### 全量验证

```bash
make verify
```

包含：格式检查、Lint、类型检查、单元/集成/契约测试、前端构建、架构边界检查和 OpenAPI 漂移检查。

### OpenAPI 生成与漂移检查

```bash
make api-generate    # 生成 OpenAPI 规范和 TypeScript Client
make api-check       # 生成后检查是否有未提交的漂移
```

### 前端 E2E 测试

```bash
pnpm --filter @warmy/web exec playwright test
```

> E2E 测试需要后端 API 和前端开发服务器运行中。

### 停止基础设施

```bash
docker compose --env-file infra/compose/.env -f infra/compose/compose.yaml down
```

## 架构摘要

```text
Next.js Web 控制台
        ↓
FastAPI 模块化单体控制面
        ↓
Temporal 工作流
        ↓
API / Playwright / Browser Harness / Evaluation / Security Workers
```

业务数据使用 PostgreSQL，对象产物使用 MinIO/S3，Redis 仅用于缓存和短期协调。

## 使用 Codex 开发

从仓库根目录启动 Codex，让它先确认已读取项目指令：

```bash
codex --ask-for-approval never "请列出你加载的项目指令，并用不超过 8 行总结当前任务、允许修改范围、架构约束和验收方式。不要修改文件。"
```

更完整的开发、续接、评审和交接提示词见 [Codex 开发指南](./docs/Codex开发指南.md)。

## GitHub

仓库：<https://github.com/xiyao1203/warmy-agent-test>
# Warmy Agent Test

面向开发与测试团队的通用 Agent 自动化测试、安全评估与发布门禁平台。

首个落地场景是 AI 创作画布 Agent，后续通过插件扩展客服、RAG、浏览器、工作流、Coding 和语音 Agent。

## 当前状态

项目处于 M0 开发准备阶段，产品需求、技术架构和 AI 开发协作规范已经完成，应用代码尚未初始化。

当前工作见：

- [当前任务](./docs/当前任务.md)
- [开发进度与变更记录](./docs/开发进度与变更记录.md)

## 核心文档

- [产品需求文档](./docs/Agent测试平台产品需求文档-PRD.md)
- [技术架构与开发规范](./docs/Agent测试平台技术架构与开发规范.md)
- [Codex 开发指南](./docs/Codex开发指南.md)
- [AI 开发协作规范](./AGENTS.md)

## 使用 Codex 开发

从仓库根目录启动 Codex，让它先确认已读取项目指令：

```bash
codex --ask-for-approval never "请列出你加载的项目指令，并用不超过 8 行总结当前任务、允许修改范围、架构约束和验收方式。不要修改文件。"
```

开始开发时可以使用：

```text
请按 AGENTS.md 开始当前任务。
先读取 docs/当前任务.md、开发进度和相关需求/架构，
复述范围与验收方式后再执行。
完成后运行验证，更新当前任务和开发进度记录。
```

更完整的开发、续接、评审和交接提示词见 [Codex 开发指南](./docs/Codex开发指南.md)。

## 架构摘要

```text
Next.js Web 控制台
        ↓
FastAPI 模块化单体控制面
        ↓
Temporal 工作流
        ↓
API / Playwright / Browser Harness / Evaluation / Security Workers
```

业务数据使用 PostgreSQL，对象产物使用 MinIO/S3，Redis 仅用于缓存和短期协调。

## GitHub

仓库：<https://github.com/xiyao1203/warmy-agent-test>

