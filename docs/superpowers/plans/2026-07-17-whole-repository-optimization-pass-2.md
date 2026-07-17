# Whole Repository Optimization Pass Two Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove duplicate composition code, split the largest backend/frontend hotspots, standardize generated API/TanStack Query usage, and isolate E2E build artifacts without changing product, API, database, permission, or execution behavior.

**Architecture:** Keep the existing modular monolith, Registrar composition root, Feature public exports, generated OpenAPI client, and Temporal/Worker boundaries. Replace the legacy bootstrap with explicit providers/model registration, preserve public Facades while splitting query/capability implementations, and move Web request/cache ownership into Feature-level factories. Every change is contract-preserving and independently reversible.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Pydantic, Pytest, Ruff, mypy, Next.js 16, React 19, TypeScript Strict, TanStack Query, generated Hey API client, Vitest, Playwright, Bash.

---

### Task 1: Capture the compatibility and hotspot baseline

**Files:**
- Modify: `docs/开发进度与变更记录.md`
- Verify: `docs/api/openapi.json`
- Verify: `packages/generated-api-client/src/client`

- [x] **Step 1: Record the branch, commit, and file hotspot baseline**

Run:

```bash
git branch --show-current
git status --short
rg --files apps/control-api/src workers plugins -g '*.py' | xargs wc -l | sort -nr | head -20
rg --files apps/web/src -g '*.ts' -g '*.tsx' | xargs wc -l | sort -nr | head -20
```

Expected: branch is `codex/whole-repository-optimization-pass-2`; only plan/task documentation is changed; the known 2301/1333/1249/1113-line hotspots are present.

- [x] **Step 2: Run the pre-change quality baseline**

Run: `make verify`

Expected: format, lint, TypeScript/mypy, Web/Python tests, build, architecture and API generation pass with zero tracked OpenAPI/client drift.

- [x] **Step 3: Run pre-change performance and browser baselines**

Run:

```bash
make performance
pnpm --filter @warmy/web e2e
```

Expected: four route budgets and backend query budgets pass; complete Playwright passes with only the explicitly credential-gated performance scenario allowed to skip.

- [x] **Step 4: Record exact counts and measured hotspot sizes**

Add the commands, counts, skips and file sizes to `TASK-20260717-003` in the progress ledger. Do not infer performance improvements from line count.

- [x] **Step 5: Commit the baseline record**

```bash
git add docs/开发进度与变更记录.md docs/当前任务.md docs/superpowers/plans/2026-07-17-whole-repository-optimization-pass-2.md
git commit -m "docs: plan repository optimization pass two"
```

### Task 2: Remove the duplicate Bootstrap wiring

**Files:**
- Create: `apps/control-api/src/agenttest/bootstrap/providers/__init__.py`
- Create: `apps/control-api/src/agenttest/bootstrap/providers/identity.py`
- Create: `apps/control-api/src/agenttest/bootstrap/model_registry.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/context.py`
- Delete: `apps/control-api/src/agenttest/bootstrap/wiring.py`
- Modify: `apps/control-api/tests/performance/test_query_bounds.py`
- Modify: `apps/control-api/tests/architecture/test_module_boundaries.py`
- Modify: `apps/control-api/tests/unit/bootstrap/test_composition.py`

- [x] **Step 1: Add failing architecture tests for one composition root**

Add assertions equivalent to:

```python
def test_legacy_wiring_is_not_a_runtime_dependency() -> None:
    source = Path("apps/control-api/src/agenttest")
    imports = find_importers(source, "agenttest.bootstrap.wiring")
    assert imports == []
    assert not (source / "bootstrap/wiring.py").exists()
```

Add a source compilation test importing `agenttest.bootstrap.model_registry` and asserting `Base.metadata.tables` contains representative Identity, Project, Run and Audit tables.

- [x] **Step 2: Run the new tests and observe RED**

Run:

```bash
uv run pytest apps/control-api/tests/architecture/test_module_boundaries.py apps/control-api/tests/unit/bootstrap/test_composition.py -q
```

Expected: failure because `context.py` imports the legacy module and `wiring.py` still exists.

- [x] **Step 3: Extract the Identity provider**

Move the complete current `build_auth_dependencies(settings)` implementation from `bootstrap/wiring.py:627-667` into `bootstrap/providers/identity.py` without changing its repositories, Argon2 hasher, login throttle policy, cookie/CSRF settings or returned `AuthApiDependencies` fields.

Update `context.py` to import this provider at module scope; preserve `AppOverrides` and `BootstrapContext` signatures.

- [x] **Step 4: Add explicit ORM model registration**

Create `bootstrap/model_registry.py` with explicit imports of each module's persistence `models` module and a public function:

```python
def register_models() -> MetaData:
    """Return complete Control API metadata after importing every ORM model module."""
    return Base.metadata
```

The module may import for registration only; it must not create engines, sessions, repositories, or business objects. Replace the performance test's `import agenttest.bootstrap.wiring` side effect with `register_models()`.

- [x] **Step 5: Delete the legacy wiring and verify GREEN**

Delete `bootstrap/wiring.py`, then run:

```bash
uv run pytest apps/control-api/tests/unit/bootstrap apps/control-api/tests/contract/test_health.py apps/control-api/tests/contract/test_auth_api.py apps/control-api/tests/performance/test_query_bounds.py apps/control-api/tests/architecture -q
uv run mypy apps/control-api/src
```

Expected: all pass; no API registration, override or metadata table is lost.

- [x] **Step 6: Commit the composition cleanup**

```bash
git add apps/control-api/src/agenttest/bootstrap apps/control-api/tests
git commit -m "refactor(api): remove duplicate bootstrap wiring"
```

### Task 3: Split Core Summary query implementations

**Files:**
- Delete: `apps/control-api/src/agenttest/bootstrap/core_summaries.py`
- Create: `apps/control-api/src/agenttest/bootstrap/core_summaries/__init__.py`
- Create: `apps/control-api/src/agenttest/bootstrap/core_summaries/reader.py`
- Create: `apps/control-api/src/agenttest/bootstrap/core_summaries/assets.py`
- Create: `apps/control-api/src/agenttest/bootstrap/core_summaries/execution.py`
- Create: `apps/control-api/src/agenttest/bootstrap/core_summaries/quality.py`
- Create: `apps/control-api/src/agenttest/bootstrap/core_summaries/lookups.py`
- Modify: `apps/control-api/tests/performance/test_query_bounds.py`
- Create: `apps/control-api/tests/unit/bootstrap/test_core_summary_reader.py`

- [x] **Step 1: Add Facade compatibility and empty-input tests**

Test that the stable import and every Protocol method remain available:

```python
def test_core_summary_facade_keeps_public_methods() -> None:
    assert set(CoreSummaryReader.__dict__) <= set(SqlAlchemyCoreSummaryReader.__dict__)

@pytest.mark.asyncio
async def test_summary_reader_skips_database_for_empty_ids() -> None:
    sessions = FailIfOpenedSessionFactory()
    reader = SqlAlchemyCoreSummaryReader(sessions)
    assert await reader.agents(uuid4(), []) == {}
    assert await reader.gates(uuid4(), []) == {}
```

- [x] **Step 2: Run focused tests and observe RED for empty input where applicable**

Run: `uv run pytest apps/control-api/tests/unit/bootstrap/test_core_summary_reader.py -q`

Expected: new package imports are missing and any method that opens a session before checking IDs fails.

- [x] **Step 3: Move query groups without changing SQL**

Move methods as complete units:

- `assets.py`: `projects`, `agents`, `datasets`, `test_plans`, `environments`.
- `execution.py`: `runs`, `experiments`.
- `quality.py`: `scorers`, `security_scans`, `reviews`, `gates`.
- `lookups.py`: `_group_count`, version/resource/user/profile/run lookup helpers and scalar coercion helpers.

Each group accepts the same `async_sessionmaker`. Do not rewrite joins, order clauses, window functions or result projection while moving them.

- [x] **Step 4: Implement the stable Facade**

`reader.py` constructs the three query groups once and delegates all eleven Protocol methods. `__init__.py` re-exports only `SqlAlchemyCoreSummaryReader`, preserving every existing import path.

- [x] **Step 5: Verify query-count and behavior compatibility**

Run:

```bash
uv run pytest apps/control-api/tests/unit/bootstrap/test_core_summary_reader.py apps/control-api/tests/performance/test_query_bounds.py -q
uv run pytest apps/control-api/tests/contract/test_projects_api.py apps/control-api/tests/contract/test_agents_api.py apps/control-api/tests/contract/test_datasets_api.py apps/control-api/tests/contract/test_runs_api.py -q
```

Expected: query counts do not increase and list response summaries stay identical.

- [x] **Step 6: Commit the query split**

```bash
git add apps/control-api/src/agenttest/bootstrap/core_summaries apps/control-api/tests
git commit -m "refactor(api): split core summary queries"
```

### Task 4: Split Test Agent platform capabilities

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/test_agent/adapters/platform.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/adapters/platform_assets.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/adapters/platform_execution.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/adapters/platform_quality.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/adapters/platform_projection.py`
- Modify: `apps/control-api/tests/unit/test_agent/test_platform_capability_catalog.py`
- Modify: `apps/control-api/tests/unit/test_agent/test_platform_dataset_cases.py`
- Modify: `apps/control-api/tests/unit/test_agent/test_platform_list_summaries.py`
- Modify: `apps/control-api/tests/unit/test_agent/test_platform_project_scope.py`

- [x] **Step 1: Freeze the capability contract before moving code**

Add a parameterized test that records every supported capability name, its owning group and required context project ID. Assert representative results for Agent, Dataset/Test Case, Run, Scorer, Review and Gate still return the same `resource_ref` keys and relation values.

- [x] **Step 2: Run the focused catalog and behavior tests as the baseline**

Run:

```bash
uv run pytest apps/control-api/tests/unit/test_agent/test_platform_capability_catalog.py apps/control-api/tests/unit/test_agent/test_platform_dataset_cases.py apps/control-api/tests/unit/test_agent/test_platform_list_summaries.py apps/control-api/tests/unit/test_agent/test_platform_project_scope.py -q
```

Expected: existing tests pass; the new ownership assertion fails because one class still owns every capability.

- [x] **Step 3: Extract pure projections**

Move `_artifact`, `_created`, `_resource_ref`, `_summary_item`, resource DTO projections, JSON schema inference and serialization helpers into `platform_projection.py`. Keep function signatures and returned dictionaries exact.

- [x] **Step 4: Extract capability groups**

Implement `PlatformAssetCapabilities`, `PlatformExecutionCapabilities` and `PlatformQualityCapabilities`, each with the same asynchronous `execute(capability, context, values)` call shape currently used by `HandlerPlatformGateway.execute`. Assets own Agent/Environment/Dataset/Test Case/Test Plan/Credential operations; Execution owns Run, endpoint analysis and report generation; Quality owns Scorer/Experiment/Security/Review/Gate. Existing project-scoped repository calls and command DTO construction move unchanged.

- [x] **Step 5: Reduce the Facade to routing**

`HandlerPlatformGateway.execute` validates the capability name, selects exactly one group and returns its result. Unknown capabilities preserve the current classified error. Mission delegation remains in the existing Mission gateway.

- [x] **Step 6: Verify all Test Agent behavior and architecture**

Run:

```bash
uv run pytest apps/control-api/tests/unit/test_agent apps/control-api/tests/contract/test_super_agent_chat_api.py -q
make architecture
```

Expected: capability count, schemas, resource references, error types and project isolation remain unchanged.

- [x] **Step 7: Commit the capability split**

```bash
git add apps/control-api/src/agenttest/modules/test_agent/adapters apps/control-api/tests/unit/test_agent
git commit -m "refactor(test-agent): split platform capabilities"
```

### Task 5: Replace business-data type suppressions at touched boundaries

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/reviews/domain/auto_collector.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/infrastructure/persistence/repositories.py`
- Modify: `apps/control-api/src/agenttest/modules/test_plans/domain/value_objects.py`
- Create: `apps/control-api/tests/unit/shared/test_typed_payloads.py`
- Modify: `apps/control-api/tests/architecture/test_module_boundaries.py`

- [x] **Step 1: Add failure-closed payload parsing tests**

Cover wrong types for confidence, scores, retry policy, scorer IDs and run-case IDs. Assertions must require a classified `ValueError`/validation error rather than coercing invalid containers or silently using defaults.

- [x] **Step 2: Add a production suppression budget test**

Scan production Python sources and allow only exact optional-dependency reasons:

```python
ALLOWED = {"import-not-found", "import-untyped"}
assert business_type_ignore_codes(source_root) <= ALLOWED
```

The test must report file/line/code without printing runtime secrets.

- [x] **Step 3: Run tests and observe RED**

Run: `uv run pytest apps/control-api/tests/unit/shared/test_typed_payloads.py apps/control-api/tests/architecture/test_module_boundaries.py -q`

Expected: invalid payload tests or suppression budget fail on current `arg-type/assignment/misc` ignores.

- [x] **Step 4: Introduce typed parsers at each boundary**

Use `isinstance` narrowing and small functions returning `UUID | None`, `float`, `dict[str, object]`, or validated DTOs. Do not change valid serialized payloads or Domain method signatures.

- [x] **Step 5: Verify focused behavior and mypy**

Run:

```bash
uv run pytest apps/control-api/tests/unit/reviews apps/control-api/tests/unit/runs apps/control-api/tests/unit/test_plans apps/control-api/tests/unit/shared/test_typed_payloads.py -q
uv run mypy apps/control-api/src
```

Expected: valid payload behavior passes, invalid input fails closed, and no business conversion `type: ignore` remains in touched modules.

- [x] **Step 6: Commit the typed boundaries**

```bash
git add apps/control-api/src apps/control-api/tests
git commit -m "refactor(api): type dynamic payload boundaries"
```

### Task 6: Standardize Web API access on the generated client

**Files:**
- Modify: `apps/web/src/features/{agents,browser-profiles,datasets,environments,experiments,gates,reviews,runs,scorers,security,test-plans}/api.ts`
- Modify: `apps/web/src/lib/api/problem.ts`
- Create: `apps/web/src/test/architecture/generated-client-usage.test.ts`
- Modify: relevant Feature API tests

- [x] **Step 1: Add an architecture test for raw Control API fetches**

Scan production Feature sources. Allow raw Control API `fetch` only in files/functions registered for SSE, upload/download streams or third-party navigation. The initial test must list each violating JSON endpoint and fail.

- [x] **Step 2: Run the test and observe RED**

Run: `pnpm --filter @warmy/web exec vitest run src/test/architecture/generated-client-usage.test.ts`

Expected: violations include Browser Profiles and remaining Agent/Dataset/Scorer/Review/Gate JSON mutations.

- [x] **Step 3: Migrate each JSON endpoint to its generated SDK function**

Use this exact pattern:

```typescript
const { data } = await updateProfileApiV1ProjectsProjectIdBrowserProfilesProfileIdPatch({
  body: payload,
  client: apiClient,
  headers: csrfHeaders(),
  path: { profile_id: profileId, project_id: projectId },
  signal,
  throwOnError: true,
});
return data;
```

Accept optional `signal?: AbortSignal` on list/detail functions used by Query. Replace handwritten response types with generated exports. Keep `runEventsUrl`, Artifact download URLs and upload streaming only where generated SDK cannot preserve the existing semantics.

- [x] **Step 4: Normalize generated and raw Problem Details**

Extend `problemKind/problemMessage` only as required to read generated client errors; preserve existing Chinese fallbacks. Add tests for 401/403/404/409/422 and non-JSON proxy responses.

- [x] **Step 5: Verify APIs and zero schema drift**

Run:

```bash
pnpm --filter @warmy/web test
pnpm --filter @warmy/web typecheck
make api-check
```

Expected: all Web tests/typecheck pass and OpenAPI/generated output has no diff.

- [x] **Step 6: Commit generated-client convergence**

```bash
git add apps/web/src packages/generated-api-client docs/api/openapi.json
git commit -m "refactor(web): standardize generated api usage"
```

### Task 7: Centralize Feature Query ownership and split UI hotspots

**Files:**
- Create/Modify: `apps/web/src/features/{agents,datasets,environments,runs,test-plans,browser-profiles}/queries.ts`
- Modify: corresponding `index.ts` and `*-screen.tsx`
- Create: `apps/web/src/features/test-agent/chat-timeline.tsx`
- Create: `apps/web/src/features/test-agent/chat-workspace-model.ts`
- Modify: `apps/web/src/features/test-agent/chat-workspace.tsx`
- Create: `apps/web/src/features/agents/agent-detail-tabs.tsx`
- Modify: `apps/web/src/features/agents/agent-detail.tsx`
- Create: `apps/web/src/features/agents/agent-version-sections.tsx`
- Modify: `apps/web/src/features/agents/agent-version-dialog.tsx`
- Create: `apps/web/src/features/datasets/test-case-editor-sections.tsx`
- Modify: `apps/web/src/features/datasets/test-case-editor.tsx`
- Create: `apps/web/src/features/test-plans/test-plan-version-fields.tsx`
- Modify: `apps/web/src/features/test-plans/test-plan-version-dialog.tsx`
- Create: `apps/web/src/components/layout/app-shell-navigation.tsx`
- Create: `apps/web/src/components/layout/app-shell-command.tsx`
- Modify: `apps/web/src/components/layout/app-shell.tsx`
- Modify/Create: associated Vitest component/model tests

- [x] **Step 1: Add Query key and cancellation tests**

Assert resource hierarchy and reuse:

```typescript
expect(agentQueries.list(projectId).queryKey).toEqual(["agents", projectId]);
expect(datasetQueries.cases(projectId, datasetId, versionId).queryKey).toEqual([
  "datasets", projectId, datasetId, "versions", versionId, "cases",
]);
```

Call a Query Function with an aborted signal and assert the SDK receives that signal. Add a mutation test proving only the owning resource prefix is invalidated.

- [x] **Step 2: Run Query tests and observe RED**

Run: `pnpm --filter @warmy/web exec vitest run src/features/**/tests/*quer*.test.ts`

Expected: factories do not exist and current purpose-suffixed keys do not match.

- [x] **Step 3: Implement Feature-owned Query factories**

Each `queries.ts` exports stable key factories and `queryOptions`; Screen components import them from the Feature public export. Replace direct resource Query literals. Mutations use `useMutation` plus precise invalidation or `setQueryData`; retain explicit `refetch` only for operations that must return newly created version data synchronously.

- [x] **Step 4: Extract pure models and controlled sections from UI hotspots**

Move existing functions/components without changing markup or class names:

- Chat timeline/bubbles/date/task projection to `chat-timeline.tsx` and `chat-workspace-model.ts`.
- Agent tabs/relationship lists to `agent-detail-tabs.tsx`; limits/metadata to `agent-version-sections.tsx`.
- Test Case basic/evidence/select fields to `test-case-editor-sections.tsx`.
- Test Plan asset/number/select fields to `test-plan-version-fields.tsx`.
- App Shell navigation and command palette to the two layout files.

Container components retain state ownership until a behavior test proves a Hook extraction is safe.

- [x] **Step 5: Add behavior-preservation tests for extracted models/components**

Cover Chat task-state projection and relative dates, Agent relationship empty/content states, Test Case numeric conversion, Test Plan field validation, command keyboard navigation and mobile navigation focus. Reuse existing accessible labels and test IDs; do not add test-only production branches.

- [x] **Step 6: Verify Web behavior and bundle budgets**

Run:

```bash
pnpm --filter @warmy/web format
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web test
pnpm --filter @warmy/web build
pnpm --filter @warmy/web run perf:bundle-check
```

Expected: no visual/token/route change, all tests pass, and no bundle threshold increases.

- [x] **Step 7: Commit Query and component ownership**

```bash
git add apps/web/src
git commit -m "refactor(web): centralize query and ui ownership"
```

### Task 8: Isolate E2E build artifacts

**Files:**
- Modify: `apps/web/next.config.ts`
- Modify: `scripts/start_e2e_server.sh`
- Create: `scripts/tests/test_start_e2e_server.sh`
- Modify: `apps/web/playwright.config.test.ts`

- [x] **Step 1: Add a failing isolated-distDir test**

The shell test creates a fake repository Web directory containing a locked `.next` and stubs `pnpm`/`uv`. It asserts both build and start receive the same `AGENTTEST_NEXT_DIST_DIR` beneath the Runtime Directory and that the directory is absent after exit.

- [x] **Step 2: Run the script test and observe RED**

Run: `bash scripts/tests/test_start_e2e_server.sh`

Expected: failure because Next always uses `apps/web/.next`.

- [x] **Step 3: Make distDir configurable only for test orchestration**

Use:

```typescript
const distDir = process.env.AGENTTEST_NEXT_DIST_DIR?.trim() || ".next";
const nextConfig: NextConfig = {
  distDir,
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: [
      "lucide-react",
      "@radix-ui/react-dialog",
      "@radix-ui/react-dropdown-menu",
      "@radix-ui/react-popover",
    ],
  },
};
```

Set `AGENTTEST_NEXT_DIST_DIR="$RUNTIME_DIR/next"` for both `pnpm build` and `next start`. Keep the existing cleanup trap and port checks; cleanup must preserve the original exit status.

- [x] **Step 4: Verify script, config, and complete Playwright**

Run:

```bash
bash scripts/tests/test_start_e2e_server.sh
pnpm --filter @warmy/web exec vitest run playwright.config.test.ts
pnpm --filter @warmy/web e2e
```

Expected: a pre-existing `.next/lock` does not affect startup; complete browser tests pass with only the credential-gated performance scenario allowed to skip.

- [x] **Step 5: Commit E2E isolation**

```bash
git add apps/web/next.config.ts apps/web/playwright.config.test.ts scripts/start_e2e_server.sh scripts/tests/test_start_e2e_server.sh
git commit -m "test(e2e): isolate next build artifacts"
```

### Task 9: Complete repository-wide verification and documentation

**Files:**
- Modify: `docs/Agent测试平台技术架构与开发规范.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`
- Modify: this plan's checkboxes

- [ ] **Step 1: Run architecture, Worker, and Workflow gates**

Run:

```bash
make architecture
uv run pytest workers/api-runner/tests workers/model-runner/tests plugins/canvas-agent/tests -q
```

Run the repository selections containing replay, retry, timeout, cancellation, heartbeat, idempotency, artifact upload and error classification. Record exact tests/counts.

- [ ] **Step 2: Run isolated PostgreSQL tests**

Create a disposable database with `AGENTTEST_TEST_DATABASE_URL`, run migration, constraints/index, project isolation, audit, professional asset and concurrency tests, then drop the database in a trap.

- [ ] **Step 3: Run complete quality, performance and security gates**

Run:

```bash
make verify
make performance
make security-audit
pnpm --filter @warmy/web e2e
```

Expected: all required gates pass; only documented environment-conditioned tests skip.

- [ ] **Step 4: Verify compatibility and measured outcomes**

Run:

```bash
git diff --check
git diff --exit-code -- docs/api/openapi.json packages/generated-api-client/src/client
rg -n "agenttest.bootstrap.wiring" apps/control-api/src apps/control-api/tests
rg --files apps/control-api/src apps/web/src | xargs wc -l | sort -nr | head -30
```

Expected: no Wiring import/file, zero API/client drift, no protected-scope changes, and hotspot reductions are recorded as maintainability measurements rather than runtime performance claims.

- [ ] **Step 5: Perform final diff and security review**

Review for behavior changes, lost ORM registrations, query-count regressions, cache-key collisions, excessive invalidation, swallowed errors, secret-bearing keys, raw JSON fetch bypasses, changed DOM/visual semantics and E2E process leaks. Fix all Critical/Important findings before completion.

- [ ] **Step 6: Update architecture and task records**

Document explicit Bootstrap providers/model registry, Feature-owned Query factories, generated-client raw-fetch exceptions and isolated E2E `distDir`. Move `TASK-20260717-003` to completed only with exact verification evidence; otherwise mark `待验证` with the remaining risk.

- [ ] **Step 7: Commit the verified delivery**

```bash
git add apps packages scripts docs
git commit -m "refactor: complete repository optimization pass two"
```

Do not push or merge unless the user explicitly requests it.
