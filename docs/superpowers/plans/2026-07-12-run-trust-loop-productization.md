# Run Trust Loop Productization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist and automatically execute the complete Run trust loop so every terminal Run receives deterministic classification, evidence-bounded diagnosis, verified regression handling, calibration and an explainable joint gate through one project-scoped API contract.

**Architecture:** A new `run_postprocessing` module owns the durable job and stage-result records. `ApplyRunResultHandler` creates the job through a public port after saving the terminal Run, a Temporal workflow calls authenticated Control API stage endpoints, and consumers read one aggregate trust-loop projection. Optional model and reproduction stages degrade to warnings; deterministic persistence and gate failures mark the postprocess job failed without changing the Run terminal state.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2 async, Alembic, Temporal Python SDK, Pydantic v2, Next.js 16, React 19, TypeScript, Vitest, Playwright, PostgreSQL 17.

## Global Constraints

- Every business record and query is scoped by `project_id`; Worker processes never connect to the business database.
- Workflow history contains IDs, versions and stage status only; no credentials, cookies, tokens, raw HTML or secret-bearing Evidence.
- Model output may propose cited diagnostics but may not change Evidence, Outcome, deterministic classification, regression publication rules or gate decisions.
- Run completion is never rolled back by postprocessing failure.
- Regression publication requires the same fingerprint and two independent successful reproductions after minimization; unstable candidates enter Quarantine.
- Safety, execution and Evidence failures cannot be compensated by quality scores.
- All behavior changes follow RED-GREEN-REFACTOR and each task ends with focused verification and a commit.

---

### Task 1: Register The Active Productization Task

**Files:**
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

**Interfaces:**
- Consumes: approved design `docs/superpowers/specs/2026-07-12-run-trust-loop-productization-design.md`
- Produces: unique active task `TASK-20260712-003` with exact scope and acceptance commands

- [x] **Step 1: Replace the waiting task entry with the new active task**

Record status `进行中`, the new specification and this plan, allowed modules, migration/API/Workflow/frontend scope, and the external real-target limitation inherited from `TASK-20260712-002`.

- [x] **Step 2: Add the same task to the progress ledger**

Keep `TASK-20260712-002` as `待验证`; do not claim the real-target gate passed.

- [x] **Step 3: Verify and commit**

Run: `git diff --check docs/当前任务.md docs/开发进度与变更记录.md`
Expected: exit 0.

Commit: `docs: register run trust loop productization`

### Task 2: Durable Postprocess Job And Stage Records

**Files:**
- Create: `apps/control-api/src/agenttest/modules/run_postprocessing/__init__.py`
- Create: `apps/control-api/src/agenttest/modules/run_postprocessing/domain.py`
- Create: `apps/control-api/src/agenttest/modules/run_postprocessing/ports.py`
- Create: `apps/control-api/src/agenttest/modules/run_postprocessing/infrastructure/models.py`
- Create: `apps/control-api/src/agenttest/modules/run_postprocessing/infrastructure/repository.py`
- Create: `apps/control-api/migrations/versions/0022_run_trust_loop.py`
- Create: `apps/control-api/tests/unit/run_postprocessing/test_domain.py`
- Create: `apps/control-api/tests/unit/run_postprocessing/test_repository.py`
- Modify: `apps/control-api/tests/integration/test_migrations.py`
- Modify: `apps/control-api/tests/integration/test_database_constraints.py`

**Interfaces:**
- Produces: `RunPostprocessJob.create(project_id, run_id, pipeline_version)`, `start(workflow_id)`, `begin_stage(stage)`, `complete_stage(stage, output, warnings)`, `fail_stage(stage, error_type, error_message, required)`, `finalize()`
- Produces: `PostprocessRepository.create_or_get(job)`, `get(project_id, run_id, pipeline_version)`, `save(job)`, `list_stage_results(project_id, job_id)`

- [x] **Step 1: Write failing state-machine tests**

Cover ordered stages, required-stage failure, optional-stage warning, final `completed_with_warnings`, and rejection of out-of-order transitions.

- [x] **Step 2: Run RED**

Run: `uv run pytest apps/control-api/tests/unit/run_postprocessing/test_domain.py -q`
Expected: collection/import failure because the module does not exist.

- [x] **Step 3: Implement the minimal domain types**

Use `PostprocessStatus`, `PostprocessStage`, immutable `StageResult`, and a mutable aggregate that validates the fixed stage order `classify, diagnose, reproduce, calibrate, evaluate_gate, finalize`.

- [x] **Step 4: Run domain GREEN**

Run: `uv run pytest apps/control-api/tests/unit/run_postprocessing/test_domain.py -q`
Expected: all pass.

- [x] **Step 5: Write failing repository and migration tests**

Assert `(project_id, run_id, pipeline_version)` uniqueness, project-scoped reads, stage idempotency, composite project foreign keys, indexes and migration revision `0022`.

- [x] **Step 6: Run repository RED**

Run: `uv run pytest apps/control-api/tests/unit/run_postprocessing/test_repository.py apps/control-api/tests/integration/test_migrations.py -q`
Expected: failures for missing tables/repository/revision.

- [x] **Step 7: Implement models, repository and migration**

Create `run_postprocess_jobs`, `run_postprocess_stage_results`, `run_diagnostics`, `run_regression_candidates`, `run_calibrations`, and `run_joint_gate_decisions`. Store structured payloads as JSON only after application validation; add project/run/status indexes and composite uniqueness.

- [x] **Step 8: Run GREEN and commit**

Run: `uv run pytest apps/control-api/tests/unit/run_postprocessing apps/control-api/tests/integration/test_migrations.py -q`
Expected: all pass, PostgreSQL-only case may skip without test URL.

Commit: `feat: persist run trust loop jobs`

### Task 3: Create Jobs Idempotently From Terminal Run Results

**Files:**
- Create: `apps/control-api/src/agenttest/modules/run_postprocessing/public.py`
- Create: `apps/control-api/src/agenttest/modules/run_postprocessing/application.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/application/ports.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/application/commands.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Modify: `apps/control-api/tests/unit/runs/test_run_result_handler.py`
- Create: `apps/control-api/tests/unit/run_postprocessing/test_application.py`

**Interfaces:**
- Produces: `PostprocessJobCreator.ensure_for_terminal_run(project_id: UUID, run_id: UUID) -> RunPostprocessJob`
- Produces: `PostprocessScheduler.schedule(job) -> str`
- Consumes from Run handler: `RunPostprocessPort.ensure_scheduled(project_id, run_id)` after `save_result` succeeds

- [x] **Step 1: Write failing duplicate-callback and scheduling tests**

Assert a terminal result creates exactly one job in the same API Unit of Work as the Run result, a duplicate callback reuses it, transaction commit happens before scheduling, and a scheduling exception leaves the Run terminal and the job pending.

- [x] **Step 2: Run RED**

Run: `uv run pytest apps/control-api/tests/unit/runs/test_run_result_handler.py apps/control-api/tests/unit/run_postprocessing/test_application.py -q`
Expected: failures because the postprocess port is absent.

- [x] **Step 3: Implement the public port and application service**

Keep the Run module dependent only on `run_postprocessing.public`. Use pipeline version `trust-loop-v1` as a constant and stable Workflow ID `run-trust-loop-{run_id}-trust-loop-v1`.

- [x] **Step 4: Wire bootstrap dependencies**

Inject the SQLAlchemy repository and Temporal scheduler into `ApplyRunResultHandler`. Do not schedule cancelled Runs.

- [x] **Step 5: Run GREEN and commit**

Run: `uv run pytest apps/control-api/tests/unit/runs/test_run_result_handler.py apps/control-api/tests/unit/run_postprocessing/test_application.py -q`
Expected: all pass.

Commit: `feat: schedule terminal run postprocessing`

### Task 4: Deterministic Stage Services And Aggregate Projection

**Files:**
- Create: `apps/control-api/src/agenttest/modules/run_postprocessing/stages.py`
- Create: `apps/control-api/src/agenttest/modules/run_postprocessing/projection.py`
- Modify: `apps/control-api/src/agenttest/modules/diagnostics/application.py`
- Modify: `apps/control-api/src/agenttest/modules/regressions/domain.py`
- Modify: `apps/control-api/src/agenttest/modules/regressions/minimizer.py`
- Modify: `apps/control-api/src/agenttest/modules/scorers/domain/calibration.py`
- Modify: `apps/control-api/src/agenttest/modules/gates/application/joint_gate.py`
- Create: `apps/control-api/tests/unit/run_postprocessing/test_stages.py`
- Create: `apps/control-api/tests/unit/run_postprocessing/test_projection.py`

**Interfaces:**
- Produces: `PostprocessStageService.execute(project_id, run_id, pipeline_version, stage, idempotency_key) -> StageExecution`
- Produces: `TrustLoopProjection.build(job, stage_results) -> dict[str, object]`
- Consumes: existing `FailureClassifier`, `DiagnosticService`, `RegressionCandidate`, `CalibrationMetrics`, `EvaluationArbiter`, `JointGateEvaluator`

- [ ] **Step 1: Write the failing classification and degradation matrix**

Assert target/test/environment/platform/evaluation mapping, no-evidence diagnosis `inconclusive`, model exception `inconclusive`, and deterministic stage completion despite optional warnings.

- [ ] **Step 2: Run RED**

Run: `uv run pytest apps/control-api/tests/unit/run_postprocessing/test_stages.py -q`
Expected: failure because `PostprocessStageService` is missing.

- [ ] **Step 3: Implement classify and diagnose stages**

Read Run Cases through a project-scoped port, verify Evidence hashes/scopes, store deterministic classifications, and pass only allowlisted redacted Evidence projections to the diagnostic model.

- [ ] **Step 4: Add failing regression, calibration and gate tests**

Assert two same-fingerprint reproductions publish, one reproduction remains reproducing, mixed results quarantine, insufficient calibration is explicit, and safety/execution/evidence failures block without compensation.

- [ ] **Step 5: Implement reproduce, calibrate and gate stages**

Apply a bounded minimization budget, permit auto-publication only for target/test failures, preserve baseline IDs, and save ordered gate rules with input facts and explanations.

- [ ] **Step 6: Implement and test the aggregate projection**

The projection contains job status/current stage, per-case outcomes/classifications/diagnostics, regressions, calibration, gate decision, warning codes and timestamps. Missing optional results remain explicit `inconclusive`/empty values.

- [ ] **Step 7: Run GREEN and commit**

Run: `uv run pytest apps/control-api/tests/unit/run_postprocessing apps/control-api/tests/unit/diagnostics apps/control-api/tests/unit/regressions apps/control-api/tests/unit/scorers/test_calibration.py apps/control-api/tests/unit/gates/test_joint_gate.py -q`
Expected: all pass.

Commit: `feat: execute run trust loop stages`

### Task 5: Authenticated Internal Stage API

**Files:**
- Create: `apps/control-api/src/agenttest/modules/run_postprocessing/api/__init__.py`
- Create: `apps/control-api/src/agenttest/modules/run_postprocessing/api/internal_router.py`
- Create: `apps/control-api/src/agenttest/modules/run_postprocessing/api/schemas.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Create: `apps/control-api/tests/contract/test_run_postprocessing_internal_api.py`

**Interfaces:**
- Produces: `POST /internal/projects/{project_id}/runs/{run_id}/trust-loop/{pipeline_version}/stages/{stage}`
- Produces: `POST /internal/projects/{project_id}/runs/{run_id}/trust-loop/{pipeline_version}/finalize`
- Consumes headers: `X-Internal-Token`; body: `idempotency_key`, `workflow_id`, `attempt`

- [ ] **Step 1: Write failing contract tests**

Cover 403 without the internal token, 404 for foreign project/Run, 409 for out-of-order stage, idempotent replay and sanitized error payloads.

- [ ] **Step 2: Run RED**

Run: `uv run pytest apps/control-api/tests/contract/test_run_postprocessing_internal_api.py -q`
Expected: 404 because routes are missing.

- [ ] **Step 3: Implement schemas and router**

Use strict enums and bounded strings. Never return raw exception representations, model prompts, Evidence payloads or secrets.

- [ ] **Step 4: Wire the router and run GREEN**

Run: `uv run pytest apps/control-api/tests/contract/test_run_postprocessing_internal_api.py -q`
Expected: all pass.

- [ ] **Step 5: Commit**

Commit: `feat: expose internal trust loop stages`

### Task 6: Temporal Postprocess Workflow And Recovery

**Files:**
- Create: `workers/api-runner/src/agenttest_api_runner/postprocess_contracts.py`
- Create: `workers/api-runner/src/agenttest_api_runner/postprocess_activities.py`
- Create: `workers/api-runner/src/agenttest_api_runner/postprocess_workflow.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/main.py`
- Create: `apps/control-api/src/agenttest/modules/run_postprocessing/infrastructure/temporal.py`
- Create: `workers/api-runner/tests/test_postprocess_workflow.py`
- Create: `apps/control-api/tests/unit/run_postprocessing/test_temporal_scheduler.py`

**Interfaces:**
- Produces Workflow: `RunPostprocessWorkflow(PostprocessWorkflowTask) -> PostprocessWorkflowResult`
- Produces Activity: `execute_postprocess_stage(PostprocessStageTask) -> PostprocessStageResponse`
- Scheduler: `TemporalPostprocessScheduler.schedule(job) -> workflow_id`

- [ ] **Step 1: Write failing workflow state-machine and serialization tests**

Cover ordered stages, optional-stage warning continuation, required-stage terminal failure, cancellation, nested JSON serialization and secret-free task representations.

- [ ] **Step 2: Run RED**

Run: `uv run pytest workers/api-runner/tests/test_postprocess_workflow.py apps/control-api/tests/unit/run_postprocessing/test_temporal_scheduler.py -q`
Expected: import failures for missing Workflow and scheduler.

- [ ] **Step 3: Implement contracts, activity and deterministic Workflow**

Use bounded retries. Activity calls Control API with `trust_env=False`; Workflow contains no network/database/model access and no non-deterministic calls.

- [ ] **Step 4: Register Worker and implement scheduler**

Add Workflow and Activity to the same task queue with worker tests proving registration. Use stable Workflow IDs and `REJECT_DUPLICATE` behavior.

- [ ] **Step 5: Add recovery tests**

Test duplicate start, activity retry, worker restart replay and resumption from a previously completed stage result.

- [ ] **Step 6: Run GREEN and commit**

Run: `uv run pytest workers/api-runner/tests/test_postprocess_workflow.py apps/control-api/tests/unit/run_postprocessing/test_temporal_scheduler.py -q`
Expected: all pass.

Commit: `feat: orchestrate run trust loop workflow`

### Task 7: Project-Scoped Public API And Generated Client

**Files:**
- Create: `apps/control-api/src/agenttest/modules/run_postprocessing/api/router.py`
- Modify: `apps/control-api/src/agenttest/modules/run_postprocessing/api/schemas.py`
- Create: `apps/control-api/src/agenttest/modules/run_postprocessing/queries.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Modify: `apps/control-api/src/agenttest/modules/test_missions/application/stages.py`
- Modify: `apps/control-api/tests/unit/test_missions/test_stages.py`
- Create: `apps/control-api/tests/contract/test_run_trust_loop_api.py`
- Modify generated: `docs/api/openapi.json`
- Modify generated: `packages/generated-api-client/src/client/*`

**Interfaces:**
- Produces the five GET endpoints from the approved design
- Produces generated types `TrustLoopResponse`, `DiagnosticResponse`, `RegressionCandidateResponse`, `CalibrationResponse`, `JointGateDecisionResponse`

- [ ] **Step 1: Write failing public contract tests**

Cover member authorization, project isolation, 404 for unknown Run, pending projection, completed-with-warnings projection and pagination for diagnostics/regressions.

- [ ] **Step 2: Run RED**

Run: `uv run pytest apps/control-api/tests/contract/test_run_trust_loop_api.py -q`
Expected: route failures.

- [ ] **Step 3: Implement project-scoped query handlers and routes**

Routes call application query ports only, never ORM. Sort records deterministically and expose no internal error message containing model/provider details.

- [ ] **Step 4: Make Mission consume the shared projection**

Replace duplicate regression and release-gate evaluation inside Mission `close_loop` with the persisted trust-loop summary for its Run. Keep report generation and review collection, and return `completed_with_warnings` details without changing the Run terminal state.

- [ ] **Step 5: Regenerate OpenAPI client**

Run: `make api-generate`
Expected: OpenAPI and typed client include all trust-loop responses.

- [ ] **Step 6: Run GREEN and commit**

Run: `uv run pytest apps/control-api/tests/contract/test_run_trust_loop_api.py -q && pnpm --filter @warmy/generated-api-client typecheck`
Expected: all pass.

Commit: `feat: expose run trust loop api`

### Task 8: Run Detail And Test Agent Product Closure

**Files:**
- Modify: `apps/web/src/features/runs/api.ts`
- Modify: `apps/web/src/features/runs/run-detail-screen.tsx`
- Modify: `apps/web/src/features/runs/run-detail.tsx`
- Create: `apps/web/src/features/runs/trust-loop-panel.tsx`
- Modify: `apps/web/src/features/test-agent/trust-loop-result.tsx`
- Modify: `apps/web/src/features/test-agent/diagnostic-panel.tsx`
- Modify: `apps/web/src/features/test-agent/regression-panel.tsx`
- Modify: `apps/web/src/features/test-agent/gate-decision-card.tsx`
- Create: `apps/web/src/features/runs/tests/trust-loop-panel.test.tsx`
- Modify: `apps/web/src/features/test-agent/tests/trust-loop.test.tsx`
- Modify: `apps/web/e2e/test-agent-mission.spec.ts`

**Interfaces:**
- Consumes generated `TrustLoopResponse`
- Produces one shared typed view for Run detail and Test Agent result rendering

- [ ] **Step 1: Write failing component tests**

Cover pending progress, completed data, warnings, `inconclusive`, Quarantine, blocking gate explanations, Evidence citations and empty optional lists.

- [ ] **Step 2: Run RED**

Run: `pnpm --filter @warmy/web test -- trust-loop-panel.test.tsx trust-loop.test.tsx`
Expected: component/import/assertion failures.

- [ ] **Step 3: Implement API loading and the shared panel**

Use existing UI primitives, stable dimensions, accessible status labels and links to cited Run Cases/Evidence. Do not introduce nested cards or explanatory marketing copy.

- [ ] **Step 4: Extend E2E coverage**

Verify navigation from Mission to Run, automatic refresh while pending, final warning/failure states and no overlapping controls at desktop/mobile widths.

- [ ] **Step 5: Run GREEN and commit**

Run: `pnpm --filter @warmy/web format && pnpm --filter @warmy/web lint && pnpm --filter @warmy/web typecheck && pnpm --filter @warmy/web test && pnpm --filter @warmy/web build`
Expected: all pass.

Commit: `feat: show persisted run trust loop`

### Task 9: Public-Path Fault Matrix And Workflow Verification

**Files:**
- Modify: `tests/fake_agent_target/app.py`
- Modify: `tests/fake_agent_target/tests/test_fake_target.py`
- Create: `tests/acceptance/test_run_trust_loop_public_path.py`
- Modify: `scripts/run_mission_acceptance.py`
- Modify: `Makefile`

**Interfaces:**
- Produces deterministic scenarios for success, target failure, protocol failure, auth, quota, timeout, transient recovery, incomplete Evidence and security failure
- Produces `make trust-loop-acceptance`

- [ ] **Step 1: Write failing acceptance assertions**

Assert public API completion, one postprocess job, stable classifications, model degradation, regression publication/quarantine rules, calibration state and non-compensating gate results.

- [ ] **Step 2: Run RED**

Run: `uv run pytest tests/acceptance/test_run_trust_loop_public_path.py -q`
Expected: failures until the complete service stack and API projection are connected.

- [ ] **Step 3: Extend deterministic Fake Target controls**

Keep scenarios independent, resettable and secret-free. Use real HTTP and Temporal paths; do not monkeypatch production services.

- [ ] **Step 4: Run the full public path**

Run: `make trust-loop-acceptance`
Expected: all matrix scenarios reach the expected Run and postprocess terminal states with persisted records.

- [ ] **Step 5: Commit**

Commit: `test: verify run trust loop public path`

### Task 10: Full Verification, Documentation And Task Closure

**Files:**
- Modify: `docs/Agent测试平台技术架构与开发规范.md`
- Create: `docs/runbooks/run-trust-loop-operations.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

**Interfaces:**
- Produces operator recovery/rollback instructions and final evidence ledger

- [ ] **Step 1: Run backend and architecture gates**

Run: `uv run ruff format --check . && uv run ruff check . && uv run mypy apps/control-api/src apps/admin-cli/src && uv run pytest && uv run pytest apps/control-api/tests/architecture -v && uv run python scripts/check_architecture.py`
Expected: all pass; only explicitly documented external-key tests may skip.

- [ ] **Step 2: Run isolated PostgreSQL gates**

Create a temporary database and run migration, constraints, project isolation, audit and historical upgrade tests with `AGENTTEST_TEST_DATABASE_URL`. Expected: all pass, then drop the database.

- [ ] **Step 3: Run frontend, build and API gates**

Run: `pnpm format && pnpm lint && pnpm typecheck && pnpm test && pnpm build && make api-check`
Expected: all pass with no generated diff.

- [ ] **Step 4: Run Workflow and public-path gates**

Run: `uv run pytest workers/api-runner/tests/test_postprocess_workflow.py -q && make trust-loop-acceptance`
Expected: all pass.

- [ ] **Step 5: Document operations and rollback**

Document pending-job recovery, version-mixed Worker detection, model degradation, Quarantine review, migration downgrade boundaries and safe disablement of new scheduling.

- [ ] **Step 6: Update ledgers with exact evidence**

Move `TASK-20260712-003` to completed only when all local acceptance criteria pass. Keep the unrelated external real-target verification as a separate waiting item.

- [ ] **Step 7: Commit final records**

Run: `git diff --check && git status --short`
Expected: no whitespace errors and only intended files before commit; clean after commit.

Commit: `docs: close run trust loop productization`
