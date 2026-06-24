# Agent 测试平台 MVP Implementation Roadmap

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 以可运行、可验证的增量方式交付通用 Agent 自动化测试与安全评估平台 MVP。

**Architecture:** 控制面采用 Next.js + FastAPI 模块化单体，长任务由 Temporal 编排，API、浏览器、评测和安全能力通过独立 Worker 执行。PostgreSQL 保存业务事实，MinIO/S3 保存大型产物，插件 SDK 隔离画布及其他 Agent 的领域能力。

**Tech Stack:** Next.js、React、TypeScript、FastAPI、Python、SQLAlchemy、Alembic、PostgreSQL、Temporal、Redis、MinIO、Playwright、Browser Harness、DeepEval、Promptfoo、OpenTelemetry。

---

## 1. 交付原则

- 每个里程碑必须产生可运行的软件，不以“目录已创建”作为业务里程碑完成。
- 每个阶段只引入当前阶段需要的第三方框架。
- 引入框架时重新核对官方最新稳定版、许可证和迁移说明，并锁定版本。
- 复杂能力先实现通用契约和 Fake Adapter，再接入真实第三方框架。
- 每个里程碑完成后更新 `docs/当前任务.md` 和 `docs/开发进度与变更记录.md`。
- 每个里程碑通过验收后再开始下一个阶段。

---

## 2. 里程碑总览

| 阶段 | 目标 | 主要交付物 | 前置依赖 |
|---|---|---|---|
| M0 工程基线 | 建立可开发、可测试、可构建的 Monorepo | Web/API 脚手架、Compose、CI、OpenAPI Client、局部 AGENTS | 无 |
| M1 身份与项目 | 完成登录、超级管理员用户管理和项目隔离 | Session、用户 CRUD、项目成员、审计、基础平台 UI | M0 |
| M2 测试资产 | 管理 Agent、版本、数据集、用例和测试计划 | 不可变版本、导入导出、结构化计划、基础对话草稿 | M1 |
| M3 API 测试闭环 | 运行通用 HTTP Agent 测试并生成结果 | Temporal、API Runner、Trace、断言、报告、SSE | M2 |
| M4 画布 Agent | 验证画布结构和图片产物 | Canvas 插件、环境模板、节点断言、多模态评分 | M3 |
| M5 浏览器测试 | 覆盖真实 Web 端到端路径 | Playwright、Browser Harness Beta、截图录像、候选用例 | M4 |
| M6 安全与发布 | 形成安全扫描、人工审核和发布门禁 | Promptfoo、Policy Engine、审核、版本对比、CI 门禁 | M5 |

---

## 3. M0：工程基线

### 范围

- pnpm 与 uv Monorepo。
- Next.js Web 和 FastAPI Control API。
- PostgreSQL、Redis、Temporal、MinIO 的本地 Compose。
- 统一格式化、Lint、类型检查和测试命令。
- OpenAPI 生成 TypeScript Client。
- GitHub Actions 基础质量门禁。
- `apps/web`、`apps/control-api`、`workers`、`plugins` 局部 `AGENTS.md`。
- ADR-001 至 ADR-008 初始文件。

### 退出标准

- 新环境执行一条 Bootstrap 命令即可安装依赖。
- Web 和 API 可启动，`GET /api/v1/health` 返回成功。
- PostgreSQL、Redis、Temporal、MinIO 健康。
- 前后端测试、类型检查和 Build 在 CI 通过。
- OpenAPI Client 可以重复生成且工作区无未提交差异。

### 详细计划

见 `docs/superpowers/plans/2026-06-25-m1-platform-foundation.md` 的 Task 1–7。

---

## 4. M1：身份、用户、项目与权限

### 范围

- 服务端 Session Cookie。
- Argon2id 密码。
- 初始化首个超级管理员 CLI。
- 超级管理员用户 CRUD、密码重置、启用和禁用。
- 防止删除或禁用最后一个超级管理员。
- 项目 CRUD 和项目成员分配。
- 系统角色与项目成员双层权限。
- 登录、用户管理、项目切换和无权限页面。
- 登录、用户、角色和成员变更审计。

### 退出标准

- 未登录用户无法访问平台页面。
- 超级管理员可以管理用户和项目成员。
- 普通用户不能访问用户管理 API 或页面。
- 非项目成员无法通过列表、详情和直接 ID 访问项目数据。
- 用户禁用或密码重置后现有 Session 失效。
- 身份、权限、迁移和关键 E2E 测试通过。

### 详细计划

见 `docs/superpowers/plans/2026-06-25-m1-platform-foundation.md` 的 Task 8–15。

---

## 5. M2：Agent 与测试资产

### 范围

- Agent 和 AgentVersion。
- Dataset、DatasetVersion、TestCase 和 TestCaseVersion。
- JSON、JSONL、CSV 导入导出。
- TestPlan 和 TestPlanVersion。
- 空白环境和预置环境模板。
- 个人草稿与项目发布。
- 通用 HTTP Agent 配置 Schema。
- 对话式测试 Agent 生成结构化计划草稿，不直接运行任务。

### 数据不变量

- 所有项目资源必须包含 `project_id`。
- 已发布版本不可修改。
- Run 只能引用明确版本，不能引用“最新”。
- 项目凭证仅保存加密值和掩码。

### 退出标准

- 开发或测试角色可创建 Agent、数据集和测试计划。
- 只读角色只能查看。
- 数据集发布后编辑会生成新版本。
- 导入错误逐行报告，不产生部分不可解释状态。
- 非项目成员无法访问测试资产。

### 后续详细计划

执行 M1 验收后创建：

```text
docs/superpowers/plans/YYYY-MM-DD-m2-test-assets.md
```

---

## 6. M3：通用 HTTP Agent 测试闭环

### 范围

- Temporal Server 与 Python SDK。
- Run、RunCase 状态机。
- Generic HTTP Agent 插件。
- API Runner。
- 同步、异步轮询和流式响应基础支持。
- 规则断言。
- Trace 和工具调用规范化。
- SSE 进度。
- JSON、JUnit XML 和 HTML 报告。
- 100 条用例批量执行。

### 关键工作流

```text
CreateRun
→ ValidateConfiguration
→ PrepareEnvironment
→ ExecuteAgent
→ CollectTrace
→ EvaluateAssertions
→ AggregateRun
→ BuildReport
→ CleanupEnvironment
```

### 退出标准

- 同一 `Idempotency-Key` 不产生重复 Run。
- 100 条 Fake Agent 用例可以批量完成。
- 取消 Run 会停止后续执行并清理环境。
- `FAILED`、`ERROR` 和 `CANCELLED` 明确区分。
- Worker 不直接连接业务数据库。
- Workflow Replay、重试、超时和取消测试通过。

### 后续详细计划

执行 M2 验收后创建：

```text
docs/superpowers/plans/YYYY-MM-DD-m3-api-runner.md
```

---

## 7. M4：画布 Agent 插件与多模态评测

### 范围

- Canvas AgentAdapter、EnvironmentAdapter 和 ArtifactAdapter。
- 空白画布和模板画布。
- 画布 JSON、节点、连线和执行状态采集。
- 节点、属性、连接、孤立节点和执行顺序断言。
- DeepEval 适配层。
- 图片 Prompt 一致性、参考图相似度和商品一致性。
- 低置信度结果标记为需要人工审核。

### 退出标准

- 新增 Canvas 插件不修改核心 Run Workflow。
- 同一测试可以在空白和模板画布环境执行。
- 结构断言输出分数、通过状态、解释和证据。
- 评分保存模型、Prompt、Scorer 和插件版本。
- 插件只依赖公开 SDK。

### 后续详细计划

执行 M3 验收后创建：

```text
docs/superpowers/plans/YYYY-MM-DD-m4-canvas-plugin.md
```

---

## 8. M5：浏览器双引擎

### 范围

- BrowserExecutionAdapter。
- Playwright 确定性 Runner。
- 浏览器 Session、测试账号和登录状态。
- Screenshot、Video、Playwright Trace 和网络错误采集。
- Browser Harness 探索 Runner Beta。
- 探索轨迹和候选 Helper/Domain Skill。
- 候选轨迹转换为待审核 Playwright 用例。

### 退出标准

- 同一关键任务可通过 API 和 Playwright 执行。
- Playwright 用例可稳定复现失败。
- Browser Harness 不能修改共享技能或 CI 基线。
- 所有浏览器运行保留浏览器和执行器版本。
- Browser Harness 候选用例必须审核后才能进入回归集。

### 后续详细计划

执行 M4 验收后创建：

```text
docs/superpowers/plans/YYYY-MM-DD-m5-browser-runners.md
```

---

## 9. M6：安全、审核、对比与发布门禁

### 范围

- Promptfoo Adapter。
- Prompt Injection、敏感信息泄露和基础越狱扫描。
- Security Policy Engine。
- 禁止工具、危险动作确认、步骤、成本和时间限制。
- 人工审核队列和决策。
- Agent 版本 A/B 对比。
- Release Gate。
- GitHub Actions 状态和 PR 报告。

### 退出标准

- 安全发现具有类型、严重度、证据和修复建议。
- 危险工具调用和业务状态修改可被策略拦截或判定。
- 低置信度结果可以进入审核并恢复 Workflow。
- 版本退化可以阻止 CI 合并。
- 门禁豁免必须有权限、原因和审计。

### 后续详细计划

执行 M5 验收后创建：

```text
docs/superpowers/plans/YYYY-MM-DD-m6-security-gates.md
```

---

## 10. 跨阶段质量门禁

每个里程碑必须通过：

```text
format
lint
typecheck
unit tests
integration tests
architecture tests
contract tests
critical E2E
build
migration tests
secret scan
dependency/license scan
```

并完成：

- 更新 OpenAPI 和生成 Client。
- 更新数据库迁移和数据字典。
- 更新 ADR。
- 更新当前任务和开发进度。
- 记录未验证项和风险。

---

## 11. 计划管理

- 路线图只定义阶段边界，不在后续阶段提前锁死实现细节。
- 每个阶段开始前，根据当时代码和最新稳定框架版本编写详细计划。
- 详细计划经用户确认后执行。
- 如果需求或架构变化，先更新 PRD/架构/ADR，再修改计划。

