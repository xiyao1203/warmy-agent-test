# M3: 通用 HTTP Agent 测试闭环 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` and apply test-driven development task by task.

**Goal:** 建立从发布测试计划到批量执行、实时查看进度、分析结果与 Trace 的首个完整闭环。

**Architecture:** 控制面新增独立 `runs` 模块，保存运行事实并通过 `RunOrchestrator` 端口启动工作流；Temporal Workflow 只负责编排；API Runner 通过公开任务 DTO 调用目标 HTTP Agent，不导入控制面模块、不访问业务数据库。前端新增 `runs` Feature，通过生成 Client 访问项目隔离 API。

**Tech Stack:** FastAPI、SQLAlchemy、Alembic、Temporal Python SDK、HTTPX、Next.js、React、TanStack Query、Vitest、Playwright。

---

## File Structure

```text
apps/control-api/src/agenttest/modules/runs/
├── domain/
├── application/
├── infrastructure/
├── api/
└── public.py

workers/api-runner/
├── src/agenttest_api_runner/
└── tests/

apps/web/src/features/runs/
apps/web/src/app/(platform)/projects/[projectId]/runs/
```

### Task 1: 依赖核对、Worker 规则和基线测试

- [x] 核对 Temporal Python SDK 官方稳定版、许可证、兼容性和回滚方案。
- [x] 新增 `workers/AGENTS.md`，约束确定性、幂等、超时、取消和数据库隔离。
- [x] 运行现有前后端基线测试并记录结果。

### Task 2: Run 数据模型与迁移

**Files:**
- Create: `apps/control-api/migrations/versions/0003_runs.py`
- Create: `apps/control-api/src/agenttest/modules/runs/domain/`
- Create: `apps/control-api/src/agenttest/modules/runs/infrastructure/persistence/`
- Create: `apps/control-api/tests/unit/runs/test_run_domain.py`
- Create: `apps/control-api/tests/integration/test_run_constraints.py`

- [x] 先编写 Run/RunCase 状态转换和数据库约束失败测试。
- [x] 实现 `runs`、`run_cases`、`run_events` 表和项目维度索引。
- [x] Run 保存发布版本 ID、执行配置、插件版本与配置快照。
- [x] 实现不可逆终态、取消语义和聚合统计。

### Task 3: Run 应用层与幂等

**Files:**
- Create: `apps/control-api/src/agenttest/modules/runs/application/`
- Create: `apps/control-api/tests/unit/runs/test_run_handlers.py`

- [x] 先测试创建、重复幂等键、取消、结果持久化和非法状态转换。
- [x] 定义 Repository、UnitOfWork、Clock 和 `RunOrchestrator` 端口。
- [x] 校验 TestPlanVersion、AgentVersion、DatasetVersion 均为已发布明确版本。
- [x] 创建 RunCase 快照，避免执行时读取“最新版本”。

### Task 4: 项目隔离 Run API 与 SSE

**Files:**
- Create: `apps/control-api/src/agenttest/modules/runs/api/`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Create: `apps/control-api/tests/contract/test_runs_api.py`
- Create: `apps/control-api/tests/integration/runs/test_run_isolation.py`

- [x] 先编写 API 契约、权限、CSRF、跨项目 404 和 SSE 权限测试。
- [x] 实现创建、列表、详情、取消、RunCase 详情和事件流端点。
- [x] `Idempotency-Key` 必填并在项目范围内唯一。
- [x] 稳定返回 Problem Details。

### Task 5: Generic HTTP Agent Adapter

**Files:**
- Create: `workers/api-runner/pyproject.toml`
- Create: `workers/api-runner/src/agenttest_api_runner/adapter.py`
- Create: `workers/api-runner/tests/test_adapter.py`

- [x] 用 Fake HTTP Target 先覆盖同步 JSON、SSE 流式、异步轮询、超时和取消。
- [x] 规范化请求、响应、错误、延迟、重试、消息和工具调用。
- [x] 对 Authorization、Cookie、API Key 和敏感字段脱敏。

### Task 6: Temporal Workflow 与 Activities

**Files:**
- Create: `workers/api-runner/src/agenttest_api_runner/workflow.py`
- Create: `workers/api-runner/src/agenttest_api_runner/activities.py`
- Create: `workers/api-runner/tests/test_workflow.py`

- [x] 使用 Activity Mock 编写工作流失败测试。
- [x] 编排验证、准备、执行、Trace、断言、聚合、报告和清理步骤。
- [x] 为每个 Activity 配置 Timeout、Retry Policy、Heartbeat 和取消处理。
- [ ] 验证 replay、重试、取消后清理与错误分类。（已覆盖聚合与基础错误分类；真实 Temporal replay/取消清理待补）

### Task 7: 控制面 Temporal 适配与结果回写

- [ ] 先测试启动失败、重复启动、结果回写幂等和终态保护。（已覆盖 Temporal 启动/取消载荷、结果回写幂等和终态保护；启动失败/重复启动待补）
- [x] 实现 Temporal `RunOrchestrator` Adapter 与本地 Fake Adapter。（已完成真实 Temporal Adapter 的懒连接、启动载荷和取消 signal；真实 Temporal Server 运行待环境验证）
- [x] Worker 只通过 Workflow 返回 DTO 或受认证内部结果接口回写。（已完成控制面结果 DTO 应用层处理、受 Token 保护的内部结果回写接口、Worker HTTP 回写 Activity 和 Workflow 接入）
- [x] 控制面持久化 RunEvent、RunCase、Trace 和报告摘要。（当前完成基础事件与 Trace 快照；完整报告摘要待补）

### Task 8: OpenAPI、生成 Client 与 API 文档

- [x] 导出 OpenAPI 并更新生成 TypeScript Client。
- [x] 重复生成并验证哈希一致、Lockfile 无漂移。
- [x] 新增 `docs/api/runs.md`。

### Task 9: 前端运行中心与运行详情

**Files:**
- Create: `apps/web/src/features/runs/`
- Create: `apps/web/src/app/(platform)/projects/[projectId]/runs/page.tsx`
- Create: `apps/web/src/app/(platform)/projects/[projectId]/runs/[runId]/page.tsx`
- Modify: `apps/web/src/components/layout/platform-frame.tsx`

- [x] 先编写运行列表、创建、取消、实时进度和 Trace 展示组件测试。
- [x] 实现状态筛选、创建运行、进度摘要、RunCase 结果和错误分类。
- [ ] SSE 断线后使用退避重连并回退到查询刷新。（已完成前端 SSE 接入和断线查询刷新兜底；退避重连待补）
- [x] Trace 组件按需加载，窄屏提供基础查看。
- [x] 保留 Agent 流式对话页面的三栏 `workspaceMode="agent"`。

### Task 10: 报告、批量执行与验收

- [x] 支持 JSON、JUnit XML 和基础 HTML 报告。（已完成 Worker 纯函数报告产物；真实 Artifact 上传待补）
- [x] 使用 Fake Agent 完成 100 条用例批量执行测试。（已完成 100 条结果报告生成与 Workflow 100 case 合约测试；真实 Temporal Server 批量执行待环境验证）
- [ ] 验证幂等、超时、重试、取消、清理和错误分类。
- [x] 运行后端、Worker、前端、契约、架构、迁移和 Build 验证。（真实 PostgreSQL/Docker/Temporal Server 环境仍未验证）
- [x] 更新当前任务、开发进度、README 和未验证风险。（本轮更新当前任务和进度；README 待最终验收时更新）

## 2026-06-26 当前切片状态

- 已完成：Run/RunCase 数据模型与迁移、项目隔离 API、幂等创建/取消/查询、基础 SSE 事件流、受 Token 保护的内部结果回写接口、真实 Temporal Adapter 代码路径、Generic HTTP Agent Adapter、Worker Workflow/Activity 骨架、Worker 内部结果回写 Activity、Worker JSON/JUnit/HTML 报告产物、100 case 合约与报告验收、控制面结果回写应用服务、OpenAPI/Client、运行中心与运行详情页面、前端运行详情 SSE 刷新与断线轮询兜底。
- 未完成：真实 Temporal Server 环境运行验证、前端 SSE 退避重连、真实 Artifact 上传、真实 PostgreSQL/Docker/Temporal Server 环境验证。

## Commit Strategy

每个 Task 保持单一提交目标；任何未通过关键验证的代码不得标记为完成。环境缺少 Docker、PostgreSQL 或 Temporal Server 时，使用 Fake/测试环境完成逻辑验证，并在进度记录中明确保留真实环境验收项。
