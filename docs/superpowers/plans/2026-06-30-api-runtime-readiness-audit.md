# API Runtime Readiness Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every authenticated browser API use one reliable cookie policy, preserve infrastructure failures instead of reporting false authentication errors, and fail closed when execution dependencies are unavailable.

**Architecture:** Keep cookie attributes environment-driven through `Settings`, use the shared authentication guard as the canonical error boundary, and expose explicit application errors for unavailable execution runtimes. Frontend mutation screens extract RFC 7807 details through one helper instead of replacing actionable server errors with generic copy.

**Tech Stack:** FastAPI, Pydantic Settings, Temporal Python SDK, pytest, Next.js, TypeScript, Vitest.

---

### Task 1: Authentication error boundary

**Files:**
- Modify: `apps/control-api/src/agenttest/shared/api/auth_guard.py`
- Create: `apps/control-api/tests/unit/shared/test_auth_guard.py`

- [ ] **Step 1: Write failing tests** proving missing/invalid sessions return 401 while an unexpected `RuntimeError` from the identity dependency propagates instead of becoming 401.
- [ ] **Step 2: Run** `uv run pytest apps/control-api/tests/unit/shared/test_auth_guard.py -q` and verify the infrastructure-error case fails.
- [ ] **Step 3: Remove the broad `Exception` catch** so `require_actor` handles only `InvalidSessionError`.
- [ ] **Step 4: Re-run the focused test** and verify all cases pass.

### Task 2: Run execution fail-closed behavior

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/runs/application/ports.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/application/commands.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/infrastructure/orchestrator.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/infrastructure/temporal_orchestrator.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/api/router.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Test: `apps/control-api/tests/unit/runs/test_run_result_handler.py`
- Test: `apps/control-api/tests/contract/test_runs_api.py`

- [ ] **Step 1: Write failing tests** asserting an unavailable runtime returns 503 and does not call the run repository `add` operation.
- [ ] **Step 2: Run the focused Run tests** and verify the new expectations fail against `LocalRunOrchestrator`.
- [ ] **Step 3: Add `RunRuntimeUnavailableError` and `ensure_available()`** to the orchestration port; Temporal connects during readiness checking and the unavailable adapter raises a stable error.
- [ ] **Step 4: Check readiness before persistence** in `CreateRunHandler`, remove the successful-looking local workflow fallback, and map runtime unavailability to an RFC 7807 503 response.
- [ ] **Step 5: Re-run unit and contract tests** and verify no queued Run is created when execution cannot start.

### Task 3: Actionable frontend API errors

**Files:**
- Modify: `apps/web/src/lib/api/problem.ts`
- Create: `apps/web/src/lib/api/tests/problem.test.ts`
- Modify: `apps/web/src/features/model-configs/model-config-list.tsx`
- Modify: `apps/web/src/features/security/api.ts`
- Modify: `apps/web/src/features/runs/run-center.tsx`

- [ ] **Step 1: Write failing Vitest cases** for extracting `detail` from generated-client errors and RFC 7807 fetch responses with a safe fallback.
- [ ] **Step 2: Run** `pnpm --dir apps/web exec vitest run src/lib/api/tests/problem.test.ts` and verify the helper expectations fail.
- [ ] **Step 3: Implement `problemMessage()` and `responseProblem()`** without exposing unknown objects or response bodies.
- [ ] **Step 4: Use the helpers** for model save/test, security scan, and Run creation so configuration failures are visible to the operator.
- [ ] **Step 5: Run focused frontend tests, ESLint, and TypeScript**.

### Task 4: Regression gate and documentation

**Files:**
- Modify: `scripts/check_production_truthfulness.py`
- Modify: `apps/control-api/tests/architecture/test_production_truthfulness.py`
- Modify: `README.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [ ] **Step 1: Add scanner patterns** for broad authentication exception swallowing and successful local execution fallbacks.
- [ ] **Step 2: Run the production truthfulness test and script**.
- [ ] **Step 3: Run backend focused/full tests, Web typecheck/build, Ruff, ESLint, and `git diff --check`**.
- [ ] **Step 4: Record exact evidence and any environment-limited integration checks** in the task ledger.

### Task 5: API Runner executable bootstrap

**Files:**
- Create: `workers/api-runner/src/agenttest_api_runner/main.py`
- Create: `workers/api-runner/tests/test_main.py`
- Modify: `README.md`

- [ ] **Step 1: Write failing tests** for required Temporal address, environment defaults, and exact Workflow/Activity registration.
- [ ] **Step 2: Run the focused API Runner test** and verify it fails because no startup module exists.
- [ ] **Step 3: Implement the Worker entry point** using the same Temporal namespace and API Runner task queue as the control plane.
- [ ] **Step 4: Document the startup command** and run the API Runner test suite, Ruff, and mypy.
