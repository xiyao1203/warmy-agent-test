# Business and Architecture Boundary Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate the remaining inward-layer dependency violations and make them impossible to reintroduce without changing product, API, database, frontend, Workflow, Worker, or plugin behavior.

**Architecture:** Keep the modular-monolith control plane and independent Workers. Domain and Application expose framework-free contracts; Infrastructure implements Application ports; API translates HTTP only; Bootstrap remains the composition root. AST architecture tests enforce the dependency direction across the control plane, Workers, and plugins.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy 2, Pytest, Ruff, mypy, AST source analysis, pnpm/Vitest/Playwright, Temporal.

---

### Task 1: Establish the compatibility baseline

**Files:**
- Verify: `docs/api/openapi.json`
- Verify: `packages/generated-api-client/src/client`
- Verify: `apps/control-api/tests/architecture`

- [x] **Step 1: Confirm the branch and clean worktree**

Run: `git branch --show-current && git status --short`

Expected: branch is `codex/business-architecture-boundary-convergence`; no uncommitted files except this plan after it is created.

- [x] **Step 2: Run the existing architecture baseline**

Run: `make architecture`

Expected: 11 backend architecture tests, 2 frontend boundary tests, and both source scanners pass.

- [x] **Step 3: Run the full pre-change behavior baseline**

Run: `make verify`

Expected: format, lint, typecheck, all tests, production builds, architecture checks, and OpenAPI generation pass without tracked drift.

- [x] **Step 4: Record exact baseline counts in the progress ledger**

Modify `docs/开发进度与变更记录.md` under `TASK-20260717-002` with the actual command results. Do not infer skipped integration coverage from unit tests.

### Task 2: Strengthen architecture rules with failing tests

**Files:**
- Modify: `scripts/check_architecture.py`
- Modify: `apps/control-api/tests/architecture/test_module_boundaries.py`

- [x] **Step 1: Add tests for Domain reverse dependencies**

Add fixtures equivalent to:

```python
write_module(
    tmp_path,
    "agenttest/modules/feedback/domain/entities.py",
    "from agenttest.modules.feedback.api.schemas import FeedbackType\n",
)
assert find_violations(tmp_path) == [
    "agenttest/modules/feedback/domain/entities.py: "
    "domain imports outward layer agenttest.modules.feedback.api.schemas"
]
```

- [x] **Step 2: Add tests for Application reverse and framework dependencies**

Cover imports from same-module `api` and `infrastructure`, plus `fastapi`, `sqlalchemy`, `redis`, and `temporalio`. Cross-module imports must continue to report the existing `public.py` error without duplicate noise.

- [x] **Step 3: Add tests for Worker/plugin control-plane and database dependencies**

Add a scanner input containing:

```python
from agenttest.modules.runs.public import Run
from sqlalchemy import select
```

Expected violations: Worker/plugin code cannot import Control API modules or business database drivers.

- [x] **Step 4: Run the new tests and observe RED**

Run: `uv run pytest apps/control-api/tests/architecture/test_module_boundaries.py -q`

Expected: the new tests fail because outward-layer and execution-surface rules are not implemented.

- [x] **Step 5: Implement the minimal AST checks**

Extend the scanner with explicit layer detection and execution-surface checks. Bootstrap remains exempt as the composition root; Infrastructure may depend inward; flat Domain/Application Facades remain valid.

- [x] **Step 6: Run against the current source and observe the intended module violations**

Run: `uv run python scripts/check_architecture.py`

Expected before Tasks 3–5: failures only for the audited `feedback` and `user_settings` reverse dependencies; no false positives in valid modules.

### Task 3: Move framework-backed runtime contracts out of Domain

**Files:**
- Create: `apps/control-api/src/agenttest/modules/agents/application/invocation.py`
- Modify: `apps/control-api/src/agenttest/modules/agents/domain/invocation.py`
- Modify: `apps/control-api/src/agenttest/modules/agents/public.py`
- Create: `apps/control-api/src/agenttest/modules/environments/application/runtime.py`
- Delete: `apps/control-api/src/agenttest/modules/environments/domain/runtime.py`
- Modify: `apps/control-api/src/agenttest/modules/environments/public.py`
- Create: `apps/control-api/src/agenttest/modules/scorers/application/config.py`
- Delete: `apps/control-api/src/agenttest/modules/scorers/domain/config.py`
- Modify: Scorer Application imports and focused tests
- Test: `apps/control-api/tests/unit/agents/test_invocation_contract.py`
- Test: `apps/control-api/tests/unit/runs/test_execution_snapshot.py`
- Test: `apps/control-api/tests/unit/scorers/test_scorer_configs.py`

- [x] **Step 1: Use the failing architecture scan as RED evidence**

Run: `uv run python scripts/check_architecture.py`

Expected: Domain/Pydantic violations are reported for Agent Invocation, Environment Runtime and Scorer Config while their existing behavior tests remain green.

- [x] **Step 2: Split pure Domain enums from Application validation contracts**

Keep `InvocationProtocol` in Agents Domain. Move Pydantic-backed runtime DTOs/parsers to each module's Application layer without changing class names, fields, defaults, validation limits or serialization behavior.

- [x] **Step 3: Preserve stable public exports and update internal imports**

`agents.public`, `environments.public` and existing Scorer Application consumers expose/use the same runtime types. Bootstrap and tests stop importing moved internal Domain paths.

- [x] **Step 4: Verify behavior and architecture GREEN**

Run: `uv run pytest apps/control-api/tests/unit/agents/test_invocation_contract.py apps/control-api/tests/unit/runs/test_execution_snapshot.py apps/control-api/tests/unit/scorers/test_scorer_configs.py apps/control-api/tests/integration/test_run_execution_snapshot.py -q`

Expected: validation, legacy config compatibility and serialized snapshots remain unchanged; the three Domain/Pydantic violations disappear.

### Task 4: Invert Feedback dependencies

**Files:**
- Create: `apps/control-api/src/agenttest/modules/feedback/domain/value_objects.py`
- Create: `apps/control-api/src/agenttest/modules/feedback/application/ports.py`
- Modify: `apps/control-api/src/agenttest/modules/feedback/domain/entities.py`
- Modify: `apps/control-api/src/agenttest/modules/feedback/application/commands.py`
- Modify: `apps/control-api/src/agenttest/modules/feedback/api/schemas.py`
- Modify: `apps/control-api/src/agenttest/modules/feedback/infrastructure/persistence/repositories.py`
- Test: `apps/control-api/tests/unit/feedback/test_feedback_repositories.py`
- Test: `apps/control-api/tests/contract/test_feedback_api.py`

- [x] **Step 1: Add a failing Application contract test**

Use an in-memory repository implementing:

```python
class StubFeedbackRepository:
    async def save(self, feedback: Feedback) -> None:
        self.saved = feedback
```

Assert `CreateFeedbackHandler` accepts the port, returns the generated UUID, and preserves type/title/description/contact/user fields.

- [x] **Step 2: Run the focused test and observe RED**

Run: `uv run pytest apps/control-api/tests/unit/feedback apps/control-api/tests/contract/test_feedback_api.py -q`

Expected: the new test fails because the handler is typed to the concrete SQLAlchemy repository and Domain imports the API enum.

- [x] **Step 3: Move the enum inward and define the port**

Create a Domain `FeedbackType(StrEnum)` with the existing values and an Application `FeedbackRepository(Protocol)` with `save(Feedback) -> None`. API Pydantic schemas import the Domain enum, preserving serialized values.

- [x] **Step 4: Make the handler depend only on Domain/Application**

Remove API and Infrastructure imports from `commands.py`; inject `FeedbackRepository`; keep method arguments and return UUID unchanged.

- [x] **Step 5: Verify focused behavior and architecture GREEN**

Run: `uv run pytest apps/control-api/tests/unit/feedback apps/control-api/tests/contract/test_feedback_api.py apps/control-api/tests/architecture -q`

Expected: all focused tests pass and no Feedback reverse dependency remains.

### Task 5: Invert User Settings persistence

**Files:**
- Create: `apps/control-api/src/agenttest/modules/user_settings/application/ports.py`
- Modify: `apps/control-api/src/agenttest/modules/user_settings/application/commands.py`
- Modify: `apps/control-api/src/agenttest/modules/user_settings/application/queries.py`
- Modify: `apps/control-api/src/agenttest/modules/user_settings/infrastructure/persistence/repositories.py`
- Test: `apps/control-api/tests/unit/user_settings/test_user_settings_repositories.py`
- Test: `apps/control-api/tests/contract/test_user_settings_api.py`

- [x] **Step 1: Add failing Handler tests against a stub port**

Cover default creation, partial theme/language update, notification update, and missing-settings query using a stub with `get_by_user_id` and `save`.

- [x] **Step 2: Run the focused tests and observe RED**

Run: `uv run pytest apps/control-api/tests/unit/user_settings apps/control-api/tests/contract/test_user_settings_api.py -q`

Expected: the new port-oriented assertions fail before the port exists.

- [x] **Step 3: Add the Application repository port**

Define:

```python
class UserSettingsRepository(Protocol):
    async def get_by_user_id(self, user_id: UUID) -> UserSettings | None: ...
    async def save(self, settings: UserSettings) -> None: ...
```

Update both handlers to depend on this Protocol. Keep SQLAlchemy implementation and persistence behavior unchanged.

- [x] **Step 4: Verify focused behavior and architecture GREEN**

Run: `uv run pytest apps/control-api/tests/unit/user_settings apps/control-api/tests/contract/test_user_settings_api.py apps/control-api/tests/architecture -q`

Expected: all tests pass and Application has no Infrastructure import.

### Task 6: Separate report rendering adapters from HTTP

**Files:**
- Create: `apps/control-api/src/agenttest/modules/reports/application/contracts.py`
- Create: `apps/control-api/src/agenttest/modules/reports/application/export.py`
- Create: `apps/control-api/src/agenttest/modules/reports/infrastructure/__init__.py`
- Move: `apps/control-api/src/agenttest/modules/reports/generators/*.py` to `apps/control-api/src/agenttest/modules/reports/infrastructure/generators/`
- Modify: `apps/control-api/src/agenttest/modules/reports/application/service.py`
- Modify: `apps/control-api/src/agenttest/modules/reports/api/router.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/modules/core.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/wiring.py`
- Test: `apps/control-api/tests/unit/reports/test_report_service.py`
- Test: `apps/control-api/tests/unit/reports/test_generators.py`
- Test: `apps/control-api/tests/contract/test_reports_api.py`

- [x] **Step 1: Add report export compatibility tests**

Assert all three formats preserve existing media types and content semantics: JSON parses with `format_version=1.0`, JUnit contains the same tests/failures/time attributes, and HTML escapes run/case/error fields.

- [x] **Step 2: Run the focused tests and observe RED**

Run: `uv run pytest apps/control-api/tests/unit/reports apps/control-api/tests/contract/test_reports_api.py -q`

Expected: new `ReportExportService`/renderer contract tests fail because API still constructs renderers directly.

- [x] **Step 3: Introduce runtime-compatible typed report contracts**

Use `TypedDict` for `RunCaseReport` and `RunReport`, so `ReportService.build` keeps returning the exact same dictionary shape while removing `dict[str, Any]` from the renderer boundary.

- [x] **Step 4: Introduce renderer ports and export service**

Define a framework-free `ReportRenderer` Protocol and `ExportedReport` DTO. `ReportExportService` owns the allowlisted `json/junit/html` renderer mapping. Unknown formats remain rejected by the existing FastAPI query validation.

- [x] **Step 5: Move renderers to Infrastructure and inject them in Bootstrap**

API receives an exporter and only maps authentication/errors/content to `PlainTextResponse` or `HTMLResponse`. Bootstrap imports concrete renderers and wires them once. Preserve status codes, headers, body and media types.

- [x] **Step 6: Verify report and API compatibility GREEN**

Run: `uv run pytest apps/control-api/tests/unit/reports apps/control-api/tests/contract/test_reports_api.py -q`

Expected: all report tests pass with no API-to-Infrastructure import.

### Task 7: Validate all execution boundaries

**Files:**
- Modify if required by tests: `workers/*/src/**`
- Modify if required by tests: `plugins/*/**`
- Modify: `docs/Agent测试平台技术架构与开发规范.md`

- [x] **Step 1: Run the complete architecture suite**

Run: `make architecture`

Expected: backend tests and scanners pass; frontend Feature tests and scanner pass.

- [x] **Step 2: Run Worker and plugin tests**

Run: `uv run pytest workers/api-runner/tests workers/model-runner/tests plugins/canvas-agent/tests -q`

Expected: all available tests pass, with existing environment-dependent skips documented.

- [x] **Step 3: Run Workflow replay, retry, timeout, cancellation, and idempotency suites**

Run the relevant Worker test selections discovered in the repository and record exact names/counts. No Temporal payload or Workflow identity may change.

- [x] **Step 4: Update architecture documentation**

Document the new same-module layer rule and Worker/plugin scanner in the architecture acceptance section. Do not claim directory uniformity as a requirement for pure Facades.

### Task 8: Execute complete non-regression gates

**Files:**
- Update: `docs/开发进度与变更记录.md`
- Update: `docs/当前任务.md`
- Update: this plan's checkboxes

- [x] **Step 1: Run all quality and contract gates**

Run: `make verify`

Expected: format, lint, mypy/TypeScript, all unit/component/contract tests, builds, architecture, and API check pass; generated files have no diff.

- [x] **Step 2: Run PostgreSQL migration and isolation integration tests**

Use the repository's isolated PostgreSQL test commands to cover empty migration, previous revision upgrade, constraints/indexes, project isolation, audit, and repositories. Expected: no migration file or Schema difference.

- [x] **Step 3: Run performance and security gates**

Run: `make performance && make security-audit`

Expected: route bundle/query budgets and production dependency audits pass without raising baselines or adding ignores.

- [x] **Step 4: Run complete Playwright**

Run: `pnpm --filter @warmy/web e2e`

Expected: all critical journeys pass; only explicitly credential-gated scenarios may skip with recorded reason.

- [x] **Step 5: Verify compatibility and repository cleanliness**

Run:

```bash
git diff --check
git diff --exit-code HEAD~1 -- docs/api/openapi.json packages/generated-api-client/src/client
git status --short
```

Expected: no whitespace errors, no API/client drift, and only task-scoped files changed.

- [x] **Step 6: Complete final review and documentation**

Review for behavior changes, missed absolute or relative reverse dependencies, security regressions and false-positive architecture rules. Move `TASK-20260717-002` to completed only after every required verification has evidence; otherwise mark it `待验证` with exact risk.

- [x] **Step 7: Commit the verified delivery**

Create a scoped commit describing the boundary convergence. Do not push unless the user explicitly requests it.
