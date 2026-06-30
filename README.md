# Warmy Agent Test

面向开发与测试团队的通用 Agent 自动化测试、安全评估与发布门禁平台。

首个落地场景是 AI 创作画布 Agent，后续通过插件扩展客服、RAG、浏览器、工作流、Coding 和语音 Agent。

## 当前状态

项目处于 M2 测试资产阶段，已完成 Agent、Dataset、TestCase、TestPlan 和 EnvironmentTemplate 的领域模型、API 和前端管理界面。

当前工作见：

- [当前任务](./docs/当前任务.md)
- [开发进度与变更记录](./docs/开发进度与变更记录.md)

## 核心文档

- [产品需求文档](./docs/Agent测试平台产品需求文档-PRD.md)
- [技术架构与开发规范](./docs/Agent测试平台技术架构与开发规范.md)
- [API 文档：身份与项目](./docs/api/identity-and-projects.md)
- [API 文档：测试资产](./docs/api/test-assets.md)
- [Codex 开发指南](./docs/Codex开发指南.md)
- [AI 开发协作规范](./AGENTS.md)

## 快速开始

### 一键启动（推荐）

```bash
./start.sh
```

自动检测依赖、安装缺失包、初始化 SQLite 并启动前后端：
- 前端：http://localhost:5175
- 后端：http://localhost:8181

### 手动启动

#### 前置条件

- Node.js 18+ 和 pnpm 9+
- Python 3.12+ 和 uv

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
uv run python scripts/ensure_local_env.py
export AGENTTEST_TEMPORAL_ADDRESS=localhost:7233
uv run uvicorn agenttest.main:app --app-dir apps/control-api/src --reload --port 8181
```

API 文档：`http://localhost:8181/docs`

本地初始化脚本会在 Git 忽略且权限为 `0600` 的 `.env` 中生成稳定的 `AGENTTEST_MODEL_CREDENTIAL_KEY`，并允许 localhost HTTP 使用会话 Cookie。非本地部署必须通过安全配置系统提供主密钥并启用 Secure Cookie；轮换主密钥前必须执行凭证重加密。

### 6. 启动 Model Runner

```bash
set -a
source .env
set +a
export AGENTTEST_TEMPORAL_ADDRESS=localhost:7233
uv run python -m agenttest_model_runner.main
```

Model Runner 不连接业务数据库，只从 Temporal 接收当前调用所需的加密快照。
如确需连接本机 Ollama 等私网模型，显式设置 `AGENTTEST_MODEL_ALLOW_PRIVATE_NETWORK=true`；默认关闭以防止 SSRF。
未配置或无法连接 Temporal/Model Runner 时，模型测试、Agent 对话和 Run 启动会返回明确的 `503`，不会创建模拟结果或假 Workflow。

### 7. 启动 API Runner

```bash
set -a
source .env
set +a
uv run python -m agenttest_api_runner.main
```

API Runner 消费 `agenttest-api-runner` 任务队列，执行真实 Agent HTTP 请求、浏览器采集和结果回传。它不连接业务数据库。

### 运行时配置说明

- 浏览器端开发环境默认访问 `http://localhost:8181`；生产构建未设置 `VITE_API_BASE_URL` 时使用当前站点同源 API，不会回退到访问者本机。
- 安全扫描调用已安装的 Promptfoo，可通过 `AGENTTEST_PROMPTFOO_BIN` 指定可执行文件。扫描目标必须由用户提交，默认拒绝本机和私网地址；仅在受控内网部署中显式设置 `AGENTTEST_SECURITY_SCAN_ALLOW_PRIVATE_NETWORK=true`。
- Compose 文件中的默认账号仅用于本地开发。非本地环境必须设置独立的数据库、对象存储、内部 API Token 和会话配置，禁止沿用仓库默认值。
- Agent 测试和模型评分只使用项目级模型配置及加密凭证；未配置可用模型时会明确失败，不生成模拟结果。

### 8. 启动前端

```bash
pnpm --filter @warmy/web dev --port 5175
```

前端地址：`http://localhost:5175`

### 9. 登录

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
