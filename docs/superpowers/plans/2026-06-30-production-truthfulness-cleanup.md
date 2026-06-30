# Production Truthfulness Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove production-path mocks, demo responses, false success states, in-memory business facts, floating dependencies, and duplicated runtime endpoints while preserving explicit network-mocking test features.

**Architecture:** Production execution fails closed when dependencies are unavailable. Project-scoped PostgreSQL repositories become the source of truth for test-agent conversations, run reports, and generated regression cases; misleading Playwright Agent endpoints are removed. Shared configuration and an audit gate prevent silent localhost fallbacks and known placeholder patterns from returning.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Temporal Python SDK, React 19, Next.js 16, TypeScript, Vitest, pytest, Docker Compose.

---

### Task 1: Add a production-truthfulness regression gate

**Files:**
- Create: `scripts/check_production_truthfulness.py`
- Create: `apps/control-api/tests/architecture/test_production_truthfulness.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write a failing architecture test**

```python
from pathlib import Path

from scripts.check_production_truthfulness import scan_repository


def test_production_paths_have_no_false_fallbacks() -> None:
    root = Path(__file__).resolve().parents[4]
    assert scan_repository(root) == []
```

- [ ] **Step 2: Run the test and confirm it reports current violations**

Run: `uv run pytest apps/control-api/tests/architecture/test_production_truthfulness.py -q`

Expected: FAIL listing `mock_scanner.py`, demo report data, `_mock_result`, `latest` images, in-memory test-agent stores, and duplicated frontend API base URLs.

- [ ] **Step 3: Implement a focused scanner**

```python
@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    rule: str


RULES = {
    "automatic mock fallback": re.compile(r"MockScanner|_mock_result|fallback to Mock", re.I),
    "demo business response": re.compile(r"demo-project|示例测试计划|这里使用示例数据"),
    "in-memory business fact": re.compile(r"production should use DB|_sessions: dict|_tasks: dict"),
    "floating container image": re.compile(r"image:\s+\S+:latest"),
}
```

Scan only production source and `infra/compose`; exclude test directories, generated clients, UI `placeholder=` attributes, `modules/plugins/network_mock.py`, and environment-domain Mock service descriptions.

- [ ] **Step 4: Run the focused test and keep its failures as the work queue**

Run: `uv run pytest apps/control-api/tests/architecture/test_production_truthfulness.py -q`

Expected: FAIL only for the known production violations.

### Task 2: Make browser activities fail closed

**Files:**
- Modify: `workers/api-runner/src/agenttest_api_runner/playwright_activity.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/browser_harness_activity.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/workflow.py`
- Modify: `workers/api-runner/tests/test_playwright_activity.py`
- Modify: `workers/api-runner/tests/test_browser_harness_activity.py`
- Modify: `workers/api-runner/tests/test_harness_workflow_integration.py`

- [ ] **Step 1: Replace mock-mode tests with dependency-error tests**

```python
def test_missing_playwright_is_an_explicit_error() -> None:
    result = dependency_unavailable_result("case-1", "https://target.test")
    assert result.status == "error"
    assert result.error_message == "Playwright runtime is not installed"
```

Add a Browser Harness test asserting missing runtime raises `ApplicationError` with type `DependencyUnavailable` and `non_retryable=True`.

- [ ] **Step 2: Verify the new tests fail**

Run: `uv run pytest workers/api-runner/tests/test_playwright_activity.py workers/api-runner/tests/test_browser_harness_activity.py -q`

Expected: FAIL because the current code returns skipped/empty snapshot results.

- [ ] **Step 3: Remove `_mock_result` and return/raise classified errors**

```python
except ImportError:
    return PlaywrightResult(
        run_case_id=inp.run_case_id,
        status="error",
        steps=[],
        final_url=inp.url,
        page_title="",
        error_message="Playwright runtime is not installed",
    )
```

Browser Harness raises `ApplicationError("Browser Harness runtime is not installed", type="DependencyUnavailable", non_retryable=True)` instead of constructing an empty `PageSnapshot`.

- [ ] **Step 4: Make pre-capture failure become the current case result**

Move pre-capture into the same guarded execution block and assert Workflow replay produces a RunCase `error` rather than continuing to the target Agent call.

- [ ] **Step 5: Run Worker tests**

Run: `uv run pytest workers/api-runner/tests -q`

Expected: all API Runner tests pass.

### Task 3: Remove the security scanner mock and require a real target

**Files:**
- Delete: `apps/control-api/src/agenttest/modules/security/adapters/mock_scanner.py`
- Modify: `apps/control-api/src/agenttest/modules/security/adapters/__init__.py`
- Modify: `apps/control-api/src/agenttest/modules/security/adapters/promptfoo_adapter.py`
- Modify: `apps/control-api/src/agenttest/modules/security/api/scan_router.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/settings.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Modify: `apps/control-api/tests/unit/security/test_scanner_adapters.py`
- Create: `apps/control-api/tests/unit/security/test_scan_router.py`

- [ ] **Step 1: Test missing Promptfoo and missing target as failures**

```python
def test_create_scanner_rejects_missing_binary() -> None:
    with pytest.raises(ScannerUnavailableError):
        create_scanner("missing-promptfoo")


def test_trigger_scan_requires_agent_endpoint(client) -> None:
    response = client.post(SCAN_URL, json={"scan_type": "full"})
    assert response.status_code == 422
```

- [ ] **Step 2: Run the tests and confirm the mock fallback causes failure**

Run: `uv run pytest apps/control-api/tests/unit/security/test_scanner_adapters.py apps/control-api/tests/unit/security/test_scan_router.py -q`

Expected: FAIL because missing Promptfoo currently returns `MockScanner` and the API accepts no body.

- [ ] **Step 3: Implement explicit scanner construction and strict parsing**

```python
class ScannerUnavailableError(RuntimeError):
    pass


def create_scanner(promptfoo_bin: str) -> PromptfooScanner:
    resolved = shutil.which(promptfoo_bin)
    if resolved is None:
        raise ScannerUnavailableError("Promptfoo runtime is not installed")
    return PromptfooScanner(resolved)
```

Invalid JSON raises `PromptfooOutputError`; stderr is summarized and stripped of authorization-like values before storage.

- [ ] **Step 4: Inject `settings.promptfoo_bin` and persist failed scans**

Define `SecurityScanRequest(agent_endpoint: AnyHttpUrl, scan_type: Literal[...])`. Create the scan record, call the real scanner, and call `scan.fail()` for dependency/tool/output failures.

- [ ] **Step 5: Run security tests**

Run: `uv run pytest apps/control-api/tests/unit/security apps/control-api/tests/unit/test_security_scan.py -q`

Expected: all security tests pass without importing `MockScanner`.

### Task 4: Export reports from real project-scoped runs

**Files:**
- Create: `apps/control-api/src/agenttest/modules/reports/application/service.py`
- Modify: `apps/control-api/src/agenttest/modules/reports/api/router.py`
- Modify: `apps/control-api/src/agenttest/modules/reports/generators.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/application/ports.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/infrastructure/persistence/repositories.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Create: `apps/control-api/tests/unit/reports/test_report_service.py`
- Create: `apps/control-api/tests/contract/test_reports_api.py`
- Modify: `apps/control-api/tests/unit/reports/test_generators.py`

- [ ] **Step 1: Test real report mapping, isolation, and HTML escaping**

```python
async def test_build_report_uses_run_and_cases() -> None:
    report = await service.build(actor, project_id, run_id)
    assert report.project_id == str(project_id.value)
    assert report.cases[0]["error_message"] == "real timeout"


def test_html_report_escapes_case_content() -> None:
    html = generator.generate_html(report_with_name("<script>alert(1)</script>"))
    assert "<script>" not in html
```

- [ ] **Step 2: Run report tests and confirm demo router fails them**

Run: `uv run pytest apps/control-api/tests/unit/reports apps/control-api/tests/contract/test_reports_api.py -q`

Expected: FAIL because the router has no project scope or repository dependency.

- [ ] **Step 3: Implement `ReportService`**

The service calls `ensure_member`, `get_by_id(project_id, run_id)`, and `list_cases(project_id, run_id)`, then maps exact persisted fields into `RunReport`. Update the repository port so case reads always receive `project_id` and join `runs` to enforce isolation.

- [ ] **Step 4: Replace the legacy route**

Expose `GET /projects/{project_id}/runs/{run_id}/export` with authenticated project membership and `json|junit|html`. Return 404 for absent/cross-project runs.

- [ ] **Step 5: Run report and run-module tests**

Run: `uv run pytest apps/control-api/tests/unit/reports apps/control-api/tests/unit/runs apps/control-api/tests/contract/test_reports_api.py -q`

Expected: all selected tests pass.

### Task 5: Generate regression cases from persisted failed RunCases

**Files:**
- Rewrite: `apps/control-api/src/agenttest/modules/datasets/application/generate_from_run.py`
- Modify: `apps/control-api/src/agenttest/modules/datasets/api/router.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Create: `apps/control-api/tests/unit/datasets/test_generate_from_run.py`
- Modify: `apps/control-api/tests/contract/test_datasets_api.py`

- [ ] **Step 1: Test filtering, persistence, isolation, and duplicate skipping**

```python
async def test_generates_only_failed_and_error_cases() -> None:
    result = await handler.execute(actor, project_id, command)
    assert result.total_failed == 2
    assert [case.input for case in result.generated_cases] == [failed.input_snapshot, errored.input_snapshot]
    assert result.skipped_existing == 0
```

Add cases for a foreign-project Run, a published destination version, and a second invocation that skips both source RunCase IDs.

- [ ] **Step 2: Run the tests and confirm the fixed one-item loop fails**

Run: `uv run pytest apps/control-api/tests/unit/datasets/test_generate_from_run.py -q`

Expected: FAIL because the current function neither reads nor persists RunCases.

- [ ] **Step 3: Implement `GenerateCasesFromFailedRunHandler`**

Inject `RunRepository` and the existing `AddCaseExecutor`. Filter `FAILED` and `ERROR`, build API/browser mode from the source snapshot, and add tags `generated-from-run:<run_id>` and `generated-from-run-case:<run_case_id>` for stable deduplication.

- [ ] **Step 4: Wire the handler into `DatasetApiDependencies`**

The endpoint passes the authenticated actor and project ID to the handler and returns its real counts. All writes go through `AddTestCaseHandler` so draft immutability, permission checks, sort order, and audit remain intact.

- [ ] **Step 5: Run dataset tests**

Run: `uv run pytest apps/control-api/tests/unit/datasets apps/control-api/tests/contract/test_datasets_api.py -q`

Expected: all selected tests pass.

### Task 6: Persist test-agent sessions

**Files:**
- Create: `apps/control-api/migrations/versions/0010_test_agent_sessions.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/application/ports.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/infrastructure/models.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/infrastructure/repositories.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/domain/entities.py`
- Modify: `apps/control-api/tests/integration/test_migrations.py`
- Create: `apps/control-api/tests/unit/test_agent/test_session_repository.py`

- [ ] **Step 1: Write migration and repository contract tests**

```python
async def test_repository_reads_session_only_in_its_project(repository) -> None:
    await repository.save(session)
    assert await repository.get(project_id, session.session_id) == session
    assert await repository.get(other_project_id, session.session_id) is None
```

Assert message sequence ordering, unique `(project_id, session_id, sequence)`, cascade deletion, and project composite foreign key.

- [ ] **Step 2: Run tests and confirm tables/repository are absent**

Run: `uv run pytest apps/control-api/tests/unit/test_agent/test_session_repository.py apps/control-api/tests/integration/test_migrations.py -q`

Expected: FAIL before migration and repository implementation.

- [ ] **Step 3: Add migration `0010` without changing published history**

Create `test_agent_sessions` and `test_agent_messages` exactly as specified in the design, including project composite keys and indexes.

- [ ] **Step 4: Implement repository mapping**

```python
class TestAgentSessionRepository(Protocol):
    async def get(self, project_id: ProjectId, session_id: ChatSessionId) -> ChatSession | None: ...
    async def save(self, session: ChatSession) -> None: ...
```

Persist the aggregate and replace/append messages transactionally while preserving sequence.

- [ ] **Step 5: Run migration and repository tests**

Run: `uv run pytest apps/control-api/tests/unit/test_agent/test_session_repository.py apps/control-api/tests/integration/test_migrations.py -q`

Expected: selected tests pass or PostgreSQL-only checks report their documented environment skip.

### Task 7: Use persisted conversations and remove the false Playwright Agent API

**Files:**
- Delete: `apps/control-api/src/agenttest/modules/test_agent/adapters/playwright_agents.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/api/router.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Create: `apps/control-api/tests/contract/test_test_agent_api.py`
- Modify: `apps/control-api/tests/unit/test_agent/test_chat_domain.py`

- [ ] **Step 1: Test restart-safe sessions and truthful confirmation**

```python
async def test_chat_continues_a_persisted_session(client) -> None:
    first = await client.post(CHAT_URL, json={"message": "test login"})
    second = await new_client.post(CHAT_URL, json={"message": "add security", "session_id": first.json()["session_id"]})
    assert [item["role"] for item in second.json()["messages"]] == ["user", "assistant", "user", "assistant"]


async def test_confirm_does_not_claim_execution_started(client) -> None:
    response = await client.post(CONFIRM_URL, json={"session_id": session_id})
    assert response.json()["status"] == "confirmed"
    assert "开始执行" not in response.json()["message"]
```

- [ ] **Step 2: Run the contract tests and confirm in-memory behavior fails**

Run: `uv run pytest apps/control-api/tests/contract/test_test_agent_api.py -q`

Expected: FAIL across app instances and for the current fake execution message.

- [ ] **Step 3: Inject the session repository into the router**

Load and save every session through the project-scoped repository. Return 404 for foreign-project IDs. Confirmation transitions to `confirmed` and tells the caller to create/publish a test-plan asset before starting a Run.

- [ ] **Step 4: Delete Planner/Generator/Healer routes and adapter**

Remove their request schema, task dictionary, factory construction, route handlers, and imports. Do not leave a 200 compatibility response.

- [ ] **Step 5: Run test-agent tests**

Run: `uv run pytest apps/control-api/tests/unit/test_agent apps/control-api/tests/contract/test_test_agent_api.py -q`

Expected: all selected tests pass.

### Task 8: Centralize Web API configuration and remove the misleading panel

**Files:**
- Create: `apps/web/src/lib/api/base-url.ts`
- Modify: `apps/web/src/lib/api/client.ts`
- Modify: `apps/web/src/features/{agents,datasets,experiments,gates,reviews,runs,scorers,security,test-agent,test-plans}/api.ts`
- Modify: `apps/web/src/features/test-agent/chat-screen.tsx`
- Create: `apps/web/src/lib/api/tests/base-url.test.ts`
- Modify: `apps/web/src/features/test-agent/tests/chat-screen.test.tsx`

- [ ] **Step 1: Test single-source URL resolution**

```typescript
it("uses same-origin requests when production has no external API", () => {
  expect(resolveControlApiUrl({ NODE_ENV: "production" })).toBe("");
});
```

Add a development case that accepts an explicitly supplied URL and a normalization case that removes trailing `/`.

- [ ] **Step 2: Run Web tests and confirm current localhost fallbacks fail**

Run: `pnpm --filter @warmy/web test -- src/lib/api/tests/base-url.test.ts src/features/test-agent/tests/chat-screen.test.tsx`

Expected: FAIL because each Feature currently creates its own fallback and the panel still renders.

- [ ] **Step 3: Export one `CONTROL_API_URL` and update all Feature clients**

```typescript
export const CONTROL_API_URL = resolveControlApiUrl({
  NODE_ENV: process.env.NODE_ENV,
  NEXT_PUBLIC_CONTROL_API_URL: process.env.NEXT_PUBLIC_CONTROL_API_URL,
});
```

All Feature API modules import this constant; none reads `process.env` directly.

- [ ] **Step 4: Remove Playwright Agent API types, calls, and UI panel**

Keep the real test-agent chat and model-configuration repair entry. Remove only the pseudo Planner/Generator/Healer controls and tests.

- [ ] **Step 5: Run Web quality checks**

Run: `pnpm --filter @warmy/web test && pnpm --filter @warmy/web lint && pnpm --filter @warmy/web typecheck`

Expected: no new failures; any unrelated baseline failure is recorded with exact test names before proceeding.

### Task 9: Validate runtime configuration and pin deployment dependencies

**Files:**
- Modify: `apps/control-api/src/agenttest/bootstrap/settings.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Modify: `apps/control-api/tests/unit/test_settings.py`
- Modify: `apps/control-api/tests/contract/test_app.py`
- Modify: `infra/compose/compose.yaml`
- Modify: `README.md`

- [ ] **Step 1: Test non-local settings fail on unsafe defaults**

```python
def test_production_rejects_default_internal_token() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production", internal_api_token="local-internal-token")
```

Add a CORS test asserting only `settings.web_origin` is emitted with credentials enabled.

- [ ] **Step 2: Run settings tests and confirm current defaults fail them**

Run: `uv run pytest apps/control-api/tests/unit/test_settings.py apps/control-api/tests/contract/test_app.py -q`

Expected: FAIL because CORS currently uses `*` and production accepts the local token.

- [ ] **Step 3: Add cross-field settings validation and configured CORS**

Use a Pydantic model validator to reject the local token outside `local`/`test`. Configure `allow_origins=[str(settings.web_origin).rstrip("/")]` and retain credentials.

- [ ] **Step 4: Replace every Compose `:latest` with an exact tested tag**

Pin Temporal server/UI and MinIO client/server images to explicit versions available in the existing lock/update policy. Keep local credentials behind `${VAR:-local-value}` and label them local-only in README.

- [ ] **Step 5: Validate deployment config**

Run: `docker compose -f infra/compose/compose.yaml config`

Expected: configuration renders successfully with no `:latest` image.

### Task 10: Synchronize contracts, run the audit gate, and close the task

**Files:**
- Modify: `docs/api/openapi.json`
- Modify: `packages/generated-api-client/src/client/**`
- Modify: `.github/workflows/templates/test-report.yml`
- Modify: `docs/Agent测试平台产品需求文档-PRD.md`
- Modify: `docs/Agent测试平台技术架构与开发规范.md`
- Modify: `docs/开发进度与变更记录.md`
- Modify: `docs/当前任务.md`

- [ ] **Step 1: Export OpenAPI and regenerate the TypeScript client**

Run: `make openapi && make generate-client`

Expected: generated contracts contain project-scoped report and persistent chat endpoints, and contain no Playwright Agent pseudo endpoints.

- [ ] **Step 2: Update CI report URL and architecture docs**

The report workflow calls `/api/v1/projects/${PROJECT_ID}/runs/${RUN_ID}/export`. PRD and architecture explicitly distinguish user-configured network mocks from prohibited automatic production fallbacks.

- [ ] **Step 3: Run focused and full verification**

Run:

```bash
uv run ruff check apps/control-api workers/api-runner scripts
uv run mypy apps/control-api/src workers/api-runner/src
uv run pytest apps/control-api/tests workers/api-runner/tests
pnpm --filter @warmy/web format
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web test
pnpm --filter @warmy/web build
pnpm --filter @warmy/generated-api-client typecheck
uv run python scripts/check_production_truthfulness.py
```

Expected: task-scope checks pass; all full-suite results and any pre-existing failures are recorded exactly.

- [ ] **Step 4: Verify migrations**

Run PostgreSQL empty-database upgrade, `0009 -> 0010` upgrade, constraints/index inspection, and project-isolation tests. If PostgreSQL is unavailable, leave task `待验证` and record the unverified commands and risk.

- [ ] **Step 5: Update task records**

Move TASK-20260630-001 to completed only if all required checks pass. Otherwise set `待验证` with exact evidence, remaining environment dependency, and recovery conditions; set `docs/当前任务.md` to no active task only when the task is genuinely closed.
