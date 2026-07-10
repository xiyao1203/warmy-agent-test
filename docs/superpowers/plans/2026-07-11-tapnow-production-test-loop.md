# TapNow Production Test Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 AgentTest 平台内完成 TapNow 类 Agent 的真实浏览器执行、证据采集、质量与安全评测、平台结果闭环和真实联调。

**Architecture:** 保留 PydanticAI SuperAgent、9 个 SubAgent 和 Temporal `RunWorkflow`；控制面生成 secret-free 快照，Worker 通过短期凭证租约执行目标登录、Playwright 回归、Canvas 采集与评测，所有结果以标准 Evidence 回写平台。大型证据进入对象存储，数据库保存项目隔离的描述符、阶段事件和聚合结论。

**Tech Stack:** FastAPI、SQLAlchemy、Alembic、PostgreSQL、Temporal Python SDK、Playwright、PydanticAI、DeepEval 4.0.5、Promptfoo、MinIO/S3、Next.js、React、TypeScript、TanStack Query、Vitest、Pytest。

## Global Constraints

- 平台是 Run、RunCase、Trace、Score、Artifact、Finding、Review、Experiment 和 Gate 的唯一事实来源。
- Worker 不连接业务数据库；Workflow 只编排，外部 I/O 全部位于 Activity/Adapter。
- 所有业务数据强制携带并校验 `project_id`。
- 快照、Workflow 历史、日志和 Trace 禁止出现密码、Cookie、Token 和 API Key。
- 目标产品默认只读；删除、发布、支付、订阅和权限变更必须阻断。
- 新功能和缺陷修复先写失败测试；依赖缺失必须明确 error，禁止 Mock 或假成功。
- 依赖使用精确版本并提交 Lockfile；偏离架构版本需要 ADR。

---

### Task 1: 运行证据领域契约与数据库迁移

**Files:**
- Create: `apps/control-api/migrations/versions/0018_run_case_evidence.py`
- Create: `apps/control-api/src/agenttest/modules/runs/domain/evidence.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/domain/entities.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/infrastructure/persistence/models.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/infrastructure/persistence/repositories.py`
- Test: `apps/control-api/tests/unit/runs/test_run_evidence.py`
- Test: `apps/control-api/tests/integration/test_migrations.py`

**Interfaces:**
- Produces: `RunCaseEvidence`, `RunCaseStageEvent`, `ExecutionOutcome`, `QualityDecision`, `SecurityDecision` and repository methods `save_stage_event(project_id, event)` / `list_stage_events(project_id, run_case_id)`.

- [ ] **Step 1: Write failing domain and migration tests** proving enum validation, secret-free serialization, project isolation, empty database upgrade and downgrade/upgrade of revision `0018`.

```python
def test_evidence_rejects_secret_fields() -> None:
    with pytest.raises(ValueError, match="sensitive"):
        RunCaseEvidence.from_payload({"credentials": {"password": "secret"}})
```

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest apps/control-api/tests/unit/runs/test_run_evidence.py apps/control-api/tests/integration/test_migrations.py -q`
Expected: FAIL because the evidence types and revision `0018` do not exist.

- [ ] **Step 3: Implement focused evidence models and migration**

```python
class ExecutionOutcome(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"

@dataclass(frozen=True, slots=True)
class RunCaseEvidence:
    execution_outcome: ExecutionOutcome
    quality_decision: QualityDecision
    security_decision: SecurityDecision
    canvas: dict[str, object]
    artifacts: list[dict[str, object]]
```

Migration `0018` adds JSON columns `evidence`, `quality_summary`, `security_summary` to `run_cases` and table `run_case_stage_events` with composite project/run/case indexes and foreign keys.

- [ ] **Step 4: Re-run tests and architecture checks**

Run: `uv run pytest apps/control-api/tests/unit/runs/test_run_evidence.py apps/control-api/tests/integration/test_migrations.py apps/control-api/tests/architecture/test_module_boundaries.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/control-api/migrations/versions/0018_run_case_evidence.py apps/control-api/src/agenttest/modules/runs apps/control-api/tests
git commit -m "feat: add run case evidence persistence"
```

### Task 2: 结果回调、API 与人工审核闭环

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/runs/api/schemas.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/api/router.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/application/commands.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/application/ports.py`
- Modify: `apps/control-api/src/agenttest/modules/reviews/domain/auto_collector.py`
- Test: `apps/control-api/tests/contract/test_runs_api.py`
- Test: `apps/control-api/tests/unit/runs/test_run_result_handler.py`
- Test: `apps/control-api/tests/integration/test_run_evaluation_chain.py`

**Interfaces:**
- Consumes: Task 1 evidence types.
- Produces: `RunCaseResponse.evidence`, `RunCaseResponse.stage_events` and callback acceptance of evidence, scores and findings.

- [ ] **Step 1: Write failing API and application tests** for evidence validation, score evidence/model metadata, security findings, low-confidence review collection and `project_id` isolation.
- [ ] **Step 2: Verify tests fail** with `uv run pytest apps/control-api/tests/contract/test_runs_api.py apps/control-api/tests/unit/runs/test_run_result_handler.py apps/control-api/tests/integration/test_run_evaluation_chain.py -q`.
- [ ] **Step 3: Extend callback DTOs and handler** using strict Pydantic payloads and repository writes in one Unit of Work.

```python
class ApplyRunCaseResultRequest(BaseModel):
    run_case_id: UUID
    status: Literal["passed", "failed", "error", "cancelled"]
    evidence: RunCaseEvidenceRequest
    scores: list[RunCaseScoreRequest] = Field(default_factory=list)
    findings: list[SecurityFindingRequest] = Field(default_factory=list)
```

- [ ] **Step 4: Re-run API/application/integration tests** and expect PASS.
- [ ] **Step 5: Commit** with `git commit -m "feat: persist unified execution evidence"`.

### Task 3: 短期凭证租约与 Worker 取密

**Files:**
- Create: `apps/control-api/src/agenttest/modules/environments/application/leases.py`
- Create: `apps/control-api/src/agenttest/modules/environments/api/lease_router.py`
- Modify: `apps/control-api/src/agenttest/modules/environments/public.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/credentials.py`
- Test: `apps/control-api/tests/unit/environments/test_credential_leases.py`
- Test: `apps/control-api/tests/contract/test_environment_versions_api.py`
- Test: `workers/api-runner/tests/test_credentials.py`

**Interfaces:**
- Produces: internal endpoint `POST /api/v1/internal/projects/{project_id}/credential-leases:redeem` and `CredentialLeaseClient.redeem(binding_ids, run_id, run_case_id) -> dict[str, str]`.

- [ ] **Step 1: Write failing tests** proving one-time redemption, expiry, Run/RunCase binding, project isolation and response/log redaction.
- [ ] **Step 2: Verify failures** with the three focused test files.
- [ ] **Step 3: Implement HMAC-signed 60-second lease tokens and one-time redemption**; decrypted values exist only in the response body and Worker Activity memory.

```python
@dataclass(frozen=True, slots=True)
class CredentialLease:
    project_id: UUID
    run_id: UUID
    run_case_id: UUID
    binding_ids: tuple[UUID, ...]
    expires_at: datetime
    nonce: str
```

- [ ] **Step 4: Re-run tests plus secret scan**: `rg -n "password|token|cookie" workers/api-runner/src/agenttest_api_runner -g '*.py'` and inspect every log/trace use.
- [ ] **Step 5: Commit** with `git commit -m "feat: add scoped credential leases"`.

### Task 4: TapNow Canvas Plugin 真实页面协议

**Files:**
- Create: `plugins/canvas-agent/src/agenttest_plugin_canvas/tapnow.py`
- Modify: `plugins/canvas-agent/src/agenttest_plugin_canvas/adapter.py`
- Modify: `plugins/canvas-agent/src/agenttest_plugin_canvas/__init__.py`
- Modify: `plugins/canvas-agent/manifest.json`
- Test: `plugins/canvas-agent/tests/test_tapnow_adapter.py`
- Fixtures: `plugins/canvas-agent/tests/fixtures/tapnow_canvas.html`

**Interfaces:**
- Produces: `TapNowBrowserContract.login(page, credentials)`, `submit(page, intent)`, `wait_until_complete(page)`, `collect(page) -> CanvasTrace`, and `assert_safe_action(request) -> None`.

- [ ] **Step 1: Add fixture-based failing Playwright tests** for login success/failure, task submission, stable completion, node/edge/artifact extraction and dangerous action blocking.
- [ ] **Step 2: Run `uv run pytest plugins/canvas-agent/tests/test_tapnow_adapter.py -q`** and expect FAIL.
- [ ] **Step 3: Implement selector sets with semantic fallbacks and network/DOM extraction**; no fixed `window.__canvasState` dependency.

```python
DANGEROUS_ACTIONS = frozenset({"delete", "publish", "payment", "subscribe", "permission"})

def assert_safe_action(action: str) -> None:
    if action.strip().lower() in DANGEROUS_ACTIONS:
        raise UnsafeTargetActionError(action)
```

- [ ] **Step 4: Re-run plugin tests and Ruff** and expect PASS.
- [ ] **Step 5: Commit** with `git commit -m "feat: add TapNow browser contract"`.

### Task 5: Playwright 生产执行与 Artifact 上传

**Files:**
- Create: `workers/api-runner/src/agenttest_api_runner/artifact_uploader.py`
- Create: `workers/api-runner/src/agenttest_api_runner/tapnow_activity.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/playwright_activity.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/contracts.py`
- Modify: `workers/api-runner/pyproject.toml`
- Test: `workers/api-runner/tests/test_tapnow_activity.py`
- Test: `workers/api-runner/tests/test_playwright_activity.py`
- Test: `workers/api-runner/tests/test_artifact_uploader.py`

**Interfaces:**
- Consumes: credential client and TapNow plugin.
- Produces: `execute_tapnow_case(TapNowTaskInput) -> RunCaseEvidenceBundle`; screenshots, video, trace and network data are `ArtifactDescriptor`s, never Base64 callback fields.

- [ ] **Step 1: Write failing tests** for isolated context, profile/storage-state selection, login, completion timeout, cancellation heartbeat, Artifact upload and cleanup.
- [ ] **Step 2: Verify focused tests fail.**
- [ ] **Step 3: Implement Activity with phase timeouts and `try/finally` cleanup**.

```python
async with async_playwright() as playwright:
    context = await create_isolated_context(playwright, task.browser)
    try:
        trace = await TapNowBrowserContract().execute(context, task)
        return await build_evidence(trace, uploader)
    finally:
        redact_in_memory(task.credentials)
        await context.close()
```

- [ ] **Step 4: Re-run Worker tests and Ruff**; assert Artifact payload contains hashes/keys and no Base64.
- [ ] **Step 5: Commit** with `git commit -m "feat: execute TapNow cases with production evidence"`.

### Task 6: Codex 发现到 Playwright 回归与 Temporal 可靠性

**Files:**
- Modify: `workers/api-runner/src/agenttest_api_runner/workflow.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/codex_browser_activity.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/callback.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/main.py`
- Test: `workers/api-runner/tests/test_workflow.py`
- Test: `workers/api-runner/tests/test_protocol_execution.py`
- Test: `workers/api-runner/tests/test_callback.py`
- Test: `workers/api-runner/tests/test_codex_to_playwright.py`

**Interfaces:**
- Produces: discovery script validation followed by real `execute_tapnow_case`; `RunCaseResult` includes evidence, scores and findings.

- [ ] **Step 1: Write failing Workflow tests** proving generated script is validated and executed, invalid/dangerous scripts error, quality failures do not retry, transient errors retry at most twice, cancel stops new activities and Workflow replay succeeds.
- [ ] **Step 2: Verify failures.**
- [ ] **Step 3: Implement deterministic Workflow orchestration**; script parsing and I/O remain Activities.

```python
if case.execution_mode == "codex_explore":
    discovery = await workflow.execute_activity(discover_tapnow_steps, ...)
    evidence = await workflow.execute_activity(execute_tapnow_case, discovery.task, ...)
```

- [ ] **Step 4: Re-run all API Runner tests**: `uv run pytest workers/api-runner/tests -q` and expect PASS.
- [ ] **Step 5: Commit** with `git commit -m "feat: run discovered TapNow flows deterministically"`.

### Task 7: DeepEval 质量评测适配器

**Files:**
- Create: `workers/api-runner/src/agenttest_api_runner/deepeval_adapter.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/scorer_activities.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/workflow.py`
- Modify: `workers/api-runner/pyproject.toml`
- Modify: `uv.lock`
- Test: `workers/api-runner/tests/test_deepeval_adapter.py`
- Test: `workers/api-runner/tests/test_protocol_execution.py`

**Interfaces:**
- Produces: `DeepEvalAdapter.evaluate(EvaluationInput) -> list[CaseScore]` with metric/version/threshold/explanation/confidence/evidence/model usage.

- [ ] **Step 1: Verify official DeepEval version/license/API**, record evidence in this plan execution notes, and use exact compatible version; architecture target is `4.0.5`.
- [ ] **Step 2: Write failing adapter tests** with a deterministic fake metric object at the SDK boundary; missing SDK/model config must return `EnvironmentError`, not pass.
- [ ] **Step 3: Implement Agent task completion, tool-use/trajectory and multimodal metric mappings**.

```python
class DeepEvalAdapter:
    async def evaluate(self, item: EvaluationInput) -> list[CaseScore]:
        test_case = LLMTestCase(input=item.intent, actual_output=item.output, tools_called=item.tools)
        return [await self._run(metric, test_case) for metric in self._metrics(item)]
```

- [ ] **Step 4: Run adapter, Worker and lockfile verification** and expect PASS.
- [ ] **Step 5: Commit** with `git commit -m "feat: integrate DeepEval scoring"`.

### Task 8: Promptfoo Finding 回写与门禁

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/security/adapters/promptfoo_adapter.py`
- Modify: `apps/control-api/src/agenttest/modules/security/domain/models.py`
- Modify: `apps/control-api/src/agenttest/modules/security/infrastructure/repositories.py`
- Modify: `apps/control-api/src/agenttest/modules/gates/application/evaluate.py`
- Test: `apps/control-api/tests/unit/security/test_scanner_adapters.py`
- Test: `apps/control-api/tests/integration/test_security_asset_chain.py`
- Test: `apps/control-api/tests/integration/test_release_decision_chain.py`

**Interfaces:**
- Consumes: evidence and target config.
- Produces: project-scoped Finding linked to RunCase and Artifact evidence; high/critical findings produce blocked gate evidence.

- [ ] **Step 1: Write failing tests** for real result schema mapping, RunCase linkage, invalid JSON/error semantics, token redaction and blocking severity.
- [ ] **Step 2: Verify failures.**
- [ ] **Step 3: Implement schema adapter and gate evidence aggregation** without changing Promptfoo into a fact store.
- [ ] **Step 4: Run security/gate tests and an installed Promptfoo CLI smoke test** against the repository fake target.
- [ ] **Step 5: Commit** with `git commit -m "feat: close Promptfoo findings into release gates"`.

### Task 9: 前端运行证据工作台

**Files:**
- Modify: `apps/web/src/features/runs/run-detail.tsx`
- Modify: `apps/web/src/features/runs/run-result-workbench.tsx`
- Modify: `apps/web/src/features/runs/trace-timeline.tsx`
- Modify: `apps/web/src/features/runs/artifact-preview.tsx`
- Modify: `apps/web/src/features/runs/api.ts`
- Test: `apps/web/src/features/runs/tests/run-result-workbench.test.tsx`
- Test: `apps/web/src/features/runs/tests/trace-timeline.test.tsx`
- Test: `apps/web/src/features/runs/tests/artifact-preview.test.tsx`
- Generated: `packages/generated-api-client/src/client/types.gen.ts`

**Interfaces:**
- Consumes: extended RunCase API.
- Produces: execution/quality/security summary, phase timeline, Canvas evidence, Score evidence, Finding severity and Artifact preview/download.

- [ ] **Step 1: Write failing component tests** for all three decisions, stage errors/retries, low-confidence review, security blocked state and safe Artifact rendering.
- [ ] **Step 2: Verify Vitest failures.**
- [ ] **Step 3: Regenerate API client and implement UI** using existing Tokens/components; raw JSON remains behind a detail disclosure.

```tsx
<DecisionSummary
  execution={caseItem.evidence.execution_outcome}
  quality={caseItem.evidence.quality_decision}
  security={caseItem.evidence.security_decision}
/>
```

- [ ] **Step 4: Run focused tests, ESLint, typecheck and build** and expect PASS.
- [ ] **Step 5: Commit** with `git commit -m "feat: show production execution evidence"`.

### Task 10: 全栈联调、真实目标验收与文档收口

**Files:**
- Modify: `infra/compose/compose.yaml`
- Create: `docs/runbooks/tapnow-production-testing.md`
- Modify: `README.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`
- Test: `apps/control-api/tests/integration/test_tapnow_production_loop.py`
- Test: `workers/api-runner/tests/test_tapnow_end_to_end.py`

**Interfaces:**
- Produces: repeatable local/staging deployment and auditable real Run ID.

- [ ] **Step 1: Add a deterministic fake target integration test** covering login, task, completion, Canvas extraction, DeepEval adapter boundary, Promptfoo Finding, callback, review and gate.
- [ ] **Step 2: Run database migration checks** on empty and previous revision databases.
- [ ] **Step 3: Run all relevant backend/Worker/plugin tests, Ruff, mypy and architecture checks.**
- [ ] **Step 4: Run frontend format/lint/typecheck/tests/build.**
- [ ] **Step 5: Start PostgreSQL, Temporal, MinIO, Control API, Web and Worker; execute API health and fake-target full-stack smoke.**
- [ ] **Step 6: Execute a read-only real TapNow staging run** using the configured dedicated browser profile/credential; record Run ID, Case result, Artifact IDs, scores/findings and any external blocker. No destructive action is permitted.
- [ ] **Step 7: Verify failure injections** for invalid credential, timeout, cancellation and Worker restart.
- [ ] **Step 8: Update runbook and task records with exact commands/results; do not mark complete if the real target run is unverified.**
- [ ] **Step 9: Run final `git diff --check`, secret scan and status review.**
- [ ] **Step 10: Commit** with `git commit -m "test: verify TapNow production test loop"`.

## Plan self-review

- Spec coverage: Tasks 1–10 cover contracts/database, control-plane callback, credential leases, TapNow plugin, browser execution, Temporal reliability, DeepEval, Promptfoo, frontend, infrastructure and real integration.
- Type consistency: `RunCaseEvidence` is the control-plane domain type; `RunCaseEvidenceBundle` is the Worker DTO serialized to the callback; API maps it to `RunCaseEvidenceRequest`.
- Scope: RAGAS, LangSmith and Langfuse remain outside this implementation; no second Agent framework or fact store is introduced.
- Completion gate: Task 10 explicitly prevents completion when the real target run or required infrastructure is unverified.
