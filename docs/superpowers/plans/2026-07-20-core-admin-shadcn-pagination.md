# Core Admin shadcn Pagination Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every core administration list real numbered server pagination with 10/20/50 page sizes and migrate its cards, toolbars, tables, dialogs, and list states to a brand-preserving shadcn component layer.

**Architecture:** Add shared pagination value objects and API parsing without moving business ownership out of Features. Each Repository performs stable paged reads and filtered counts, each Application handler returns a typed page, and each API response exposes common metadata while preserving legacy cursor/limit behavior. The Web owns controlled URL-backed pagination and shared shadcn primitives; Feature screens continue to own columns, filters, permissions, and actions.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy 2, PostgreSQL/SQLite tests, OpenAPI generated TypeScript client, Next.js 16, React 19, TanStack Query/Table, Tailwind CSS 4, Radix UI, Vitest, Testing Library, Playwright.

---

## File Map

### Shared backend

- Create `apps/control-api/src/agenttest/shared/application/pagination.py`: `PageRequest` and `PageResult[T]` application values.
- Create `apps/control-api/src/agenttest/shared/api/pagination.py`: optional page-mode query parsing and response metadata helpers.
- Create `apps/control-api/tests/unit/shared/test_pagination.py`: validation and metadata tests.
- Create `apps/control-api/tests/contract/test_core_list_pagination_api.py`: cross-module API pagination contract.

### Backend Feature adapters

- Modify `apps/control-api/src/agenttest/modules/{projects,identity,agents,datasets,test_plans,runs,environments,browser_profiles,model_configs,test_accounts,scorers,experiments,reviews,security,gates}` in their existing Repository/Application/API files.
- Modify the matching contract/unit/integration tests under `apps/control-api/tests`.
- Modify `docs/api/openapi.json` and `packages/generated-api-client/src/client/**` only through the repository generator.

### Shared Web UI

- Create `apps/web/components.json`: pinned shadcn path/style configuration.
- Create `apps/web/src/components/ui/card.tsx`, `select.tsx`, `pagination.tsx`, `resource-pagination.tsx`, `list-toolbar.tsx`, and `summary-strip.tsx`.
- Create `apps/web/src/lib/pagination.ts` and `apps/web/src/lib/use-pagination-state.ts`.
- Add colocated component tests and `apps/web/src/lib/use-pagination-state.test.tsx`.
- Modify `apps/web/package.json` and `pnpm-lock.yaml` only to promote the already-resolved `@radix-ui/react-select@2.3.2` to a direct dependency.

### Web Feature migrations

- Modify core list APIs, queries, screens, and existing tests under `apps/web/src/features/{projects,users,agents,datasets,test-plans,runs,environments,browser-profiles,model-configs,test-accounts,scorers,experiments,reviews,security,gates}`.
- Extend `apps/web/src/test/architecture/list-table-contract.test.ts` and add `apps/web/src/test/architecture/pagination-contract.test.ts`.
- Extend `apps/web/tests/e2e/list-layout.spec.ts` and add `apps/web/tests/e2e/core-pagination.spec.ts`.

### Documentation

- Modify `docs/design.md`, `docs/当前任务.md`, and `docs/开发进度与变更记录.md`.

---

### Task 1: Establish the isolated execution branch and baseline

**Files:**

- Verify: `docs/当前任务.md`
- Verify: `docs/superpowers/specs/2026-07-20-core-admin-shadcn-pagination-design.md`
- Track: `docs/superpowers/plans/2026-07-20-core-admin-shadcn-pagination.md`

- [x] **Step 1: Create the implementation branch from the confirmed design commit**

```bash
git switch -c codex/core-admin-shadcn-pagination
```

Expected: branch points at the confirmed list-layout and pagination design baseline.

- [x] **Step 2: Capture the clean baseline**

```bash
git status --short --branch
pnpm --filter @warmy/web exec vitest run src/test/architecture/list-table-contract.test.ts --maxWorkers=2
uv run pytest apps/control-api/tests/architecture apps/control-api/tests/contract/test_agents_api.py apps/control-api/tests/contract/test_user_admin_api.py -q
```

Expected: clean worktree and all selected baseline tests pass.

- [ ] **Step 3: Commit the implementation plan**

```bash
git add docs/superpowers/plans/2026-07-20-core-admin-shadcn-pagination.md docs/当前任务.md docs/开发进度与变更记录.md
git commit -m "docs: plan core admin pagination"
```

### Task 2: Add shared backend pagination values and API parsing

**Files:**

- Create: `apps/control-api/src/agenttest/shared/application/pagination.py`
- Create: `apps/control-api/src/agenttest/shared/api/pagination.py`
- Modify: `apps/control-api/src/agenttest/shared/application/__init__.py`
- Modify: `apps/control-api/src/agenttest/shared/api/__init__.py`
- Test: `apps/control-api/tests/unit/shared/test_pagination.py`

- [ ] **Step 1: Write failing value and parser tests**

```python
def test_page_request_converts_to_offset() -> None:
    request = PageRequest(page=3, page_size=20)
    assert request.offset == 40


def test_optional_page_mode_preserves_legacy_calls() -> None:
    assert resolve_page_request(page=None, page_size=None) is None
    assert resolve_page_request(page=2, page_size=None) == PageRequest(page=2, page_size=10)
```

- [ ] **Step 2: Run the tests and confirm the missing-module failure**

```bash
uv run pytest apps/control-api/tests/unit/shared/test_pagination.py -q
```

Expected: FAIL because shared pagination modules do not exist.

- [ ] **Step 3: Implement immutable application values and response metadata**

```python
@dataclass(frozen=True, slots=True)
class PageRequest:
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


@dataclass(frozen=True, slots=True)
class PageResult(Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return ceil(self.total / self.page_size) if self.total else 0
```

`resolve_page_request` returns `None` only when both optional parameters are absent and raises FastAPI validation errors for page `< 1` or page sizes outside `{10, 20, 50}`.

- [ ] **Step 4: Run tests and type checks**

```bash
uv run pytest apps/control-api/tests/unit/shared/test_pagination.py -q
uv run mypy apps/control-api/src/agenttest/shared
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add apps/control-api/src/agenttest/shared apps/control-api/tests/unit/shared/test_pagination.py
git commit -m "feat(api): add shared pagination contract"
```

### Task 3: Paginate cursor-based asset modules

**Files:**

- Modify: `apps/control-api/src/agenttest/modules/agents/{domain/repositories.py,application/queries.py,infrastructure/persistence/repositories.py,api/router.py,api/schemas.py}`
- Modify: `apps/control-api/src/agenttest/modules/datasets/{domain/repositories.py,application/queries.py,infrastructure/persistence/repositories.py,api/router.py,api/schemas.py}`
- Modify: `apps/control-api/src/agenttest/modules/test_plans/{domain/repositories.py,application/queries.py,infrastructure/persistence/repositories.py,api/router.py,api/schemas.py}`
- Modify: `apps/control-api/src/agenttest/modules/environments/{domain/repositories.py,application/queries.py,infrastructure/persistence/repositories.py,api/router.py,api/schemas.py}`
- Modify: `apps/control-api/src/agenttest/modules/identity/{application/ports.py,application/queries/list_users.py,infrastructure/persistence/repositories.py,api/admin_router.py,api/schemas.py}`
- Test: existing module unit/contract tests plus `apps/control-api/tests/contract/test_core_list_pagination_api.py`

- [ ] **Step 1: Add failing page-mode API tests for agents, datasets, plans, environments, and users**

```python
response = client.get(url, params={"page": 2, "page_size": 10}, headers=auth_headers)
assert response.status_code == 200
assert response.json().keys() >= {"items", "total", "page", "page_size", "total_pages"}
assert response.json()["page"] == 2
assert response.json()["page_size"] == 10
assert response.json().get("next_cursor") is None
```

Also assert legacy `limit/cursor` requests retain their previous item count and cursor behavior.

- [ ] **Step 2: Run the contract tests and confirm metadata is absent**

```bash
uv run pytest apps/control-api/tests/contract/test_core_list_pagination_api.py apps/control-api/tests/contract/test_agents_api.py apps/control-api/tests/contract/test_datasets_api.py apps/control-api/tests/contract/test_test_plans_api.py apps/control-api/tests/contract/test_environments_api.py apps/control-api/tests/contract/test_user_admin_api.py -q
```

Expected: new page-mode assertions fail.

- [ ] **Step 3: Add paged Repository and Application methods without removing legacy cursor methods**

```python
async def list_page_by_project(
    self, project_id: ProjectId, *, page: PageRequest
) -> PageResult[Agent]:
    filters = AgentModel.project_id == project_id.value
    async with session_scope(self._session_factory) as session:
        total = await session.scalar(select(func.count()).select_from(AgentModel).where(filters))
        models = list((await session.scalars(
            select(AgentModel)
            .where(filters)
            .order_by(AgentModel.created_at.desc(), AgentModel.id.desc())
            .offset(page.offset)
            .limit(page.page_size)
        )).all())
    return PageResult([_to_agent(model) for model in models], int(total or 0), page.page, page.page_size)
```

Use the same stable timestamp-plus-ID ordering and project filter in each module. User ordering remains stable by ID and is permission gated at the Application/API boundary.

Every filter already visible in the migrated Web screens must be accepted by the matching page-mode endpoint and applied identically to the `items` and `count(*)` queries. This includes user search/role/status and the existing resource status/type/search filters. Agent versions, dataset versions/cases, test-plan versions, and environment versions are paged with the same values; their URL state uses list-specific namespaces in Task 8.

- [ ] **Step 4: Translate optional page mode in each router**

```python
page_request = resolve_page_request(page=page, page_size=page_size)
if page_request is not None:
    result = await dependencies.list_agents.execute_page(actor, ProjectId(project_id), page_request)
    return AgentListResponse.from_page(result, next_cursor=None)
items, next_cursor = await dependencies.list_agents.execute(actor, ProjectId(project_id), limit=limit, cursor=cursor)
total = await dependencies.list_agents.count(actor, ProjectId(project_id))
return AgentListResponse.from_legacy(items, next_cursor=next_cursor, total=total, limit=limit, page=None)
```

Legacy cursor/offset responses expose `page: null`, a real filtered `total`, the effective legacy limit as `page_size`, and a derived `total_pages`. Page mode always exposes a positive numeric page.

- [ ] **Step 5: Run module tests, project-isolation tests, and mypy**

```bash
uv run pytest apps/control-api/tests/contract/test_core_list_pagination_api.py apps/control-api/tests/contract/test_agents_api.py apps/control-api/tests/contract/test_datasets_api.py apps/control-api/tests/contract/test_test_plans_api.py apps/control-api/tests/contract/test_environments_api.py apps/control-api/tests/contract/test_user_admin_api.py apps/control-api/tests/integration/test_project_isolation.py -q
uv run mypy apps/control-api/src/agenttest/modules/agents apps/control-api/src/agenttest/modules/datasets apps/control-api/src/agenttest/modules/test_plans apps/control-api/src/agenttest/modules/environments apps/control-api/src/agenttest/modules/identity
```

Expected: pass with legacy tests unchanged.

- [ ] **Step 6: Commit**

```bash
git add apps/control-api/src/agenttest/modules/{agents,datasets,test_plans,environments,identity} apps/control-api/tests
git commit -m "feat(api): paginate core asset lists"
```

### Task 4: Paginate project, execution, and governance modules

**Files:**

- Modify: `apps/control-api/src/agenttest/modules/projects/{domain/repositories.py,application/queries/list_projects.py,infrastructure/persistence/repositories.py,api/router.py,api/schemas.py}`
- Modify: `apps/control-api/src/agenttest/modules/runs/{application/ports.py,application/queries.py,infrastructure/persistence/repositories.py,api/router.py,api/schemas.py}`
- Modify: `apps/control-api/src/agenttest/modules/browser_profiles/{application/service.py,infrastructure/repository.py,api/router.py}`
- Modify: `apps/control-api/src/agenttest/modules/model_configs/{domain/repositories.py,application/service.py,infrastructure/persistence/repositories.py,api/router.py,api/schemas.py}`
- Modify: `apps/control-api/src/agenttest/modules/test_accounts/{application/service.py,infrastructure/persistence/repositories.py,api/router.py}`
- Modify: `apps/control-api/src/agenttest/modules/scorers/{domain/repositories.py,application/service.py,infrastructure/persistence/repositories.py,api/router.py}`
- Modify: `apps/control-api/src/agenttest/modules/experiments/{application/service.py,infrastructure/persistence/repositories.py,api/router.py}`
- Modify: `apps/control-api/src/agenttest/modules/reviews/{application/service.py,infrastructure/persistence/repositories.py,api/router.py}`
- Modify: `apps/control-api/src/agenttest/modules/security/{application/scan_service.py,infrastructure/repositories.py,api/scan_router.py}`
- Modify: `apps/control-api/src/agenttest/modules/gates/{application/service.py,infrastructure/persistence/repositories.py,api/router.py}`
- Test matching contract/unit tests and `apps/control-api/tests/contract/test_core_list_pagination_api.py`.

- [ ] **Step 1: Extend failing cross-module tests**

For every listed collection endpoint, create at least 12 records, request page 2 with size 10, and assert two items, `total == 12`, `total_pages == 2`, stable non-overlapping IDs, and project isolation. Assert `page_size=25` returns 422.

```python
assert first_page_ids.isdisjoint(second_page_ids)
assert payload["total"] == 12
assert payload["total_pages"] == 2
assert client.get(url, params={"page": 1, "page_size": 25}, headers=headers).status_code == 422
```

- [ ] **Step 2: Run the expanded tests and confirm failure**

```bash
uv run pytest apps/control-api/tests/contract/test_core_list_pagination_api.py -q
```

Expected: modules without page metadata fail.

- [ ] **Step 3: Implement offset/count page methods behind current services**

Use `PageRequest.offset`, filtered `count(*)`, stable ordering with an ID tie-breaker, and `PageResult`. Project membership checks remain before Repository access. Global project and model configuration lists retain their existing actor visibility filters.

Apply every existing Web search/status/type filter to both page items and totals. Project members, run cases, environment credentials/snapshots, and other detail collections rendered as management lists receive namespaced page-mode endpoints in the same files; event streams, traces, evidence timelines, select options, and bounded lookup menus remain non-paginated because they are not management lists.

```python
page_result = await repository.list_page_by_project(project_id, page=page_request, status=status)
return ListResponse(
    items=[Response.from_domain(item) for item in page_result.items],
    total=page_result.total,
    page=page_result.page,
    page_size=page_result.page_size,
    total_pages=page_result.total_pages,
)
```

- [ ] **Step 4: Run all affected contract, integration, and architecture tests**

```bash
uv run pytest apps/control-api/tests/contract apps/control-api/tests/integration/test_project_isolation.py apps/control-api/tests/architecture -q
uv run mypy apps/control-api/src/agenttest/modules/{projects,runs,browser_profiles,model_configs,test_accounts,scorers,experiments,reviews,security,gates}
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add apps/control-api/src/agenttest/modules/{projects,runs,browser_profiles,model_configs,test_accounts,scorers,experiments,reviews,security,gates} apps/control-api/tests
git commit -m "feat(api): paginate execution and governance lists"
```

### Task 5: Regenerate OpenAPI and the generated client

**Files:**

- Modify generated: `docs/api/openapi.json`
- Modify generated: `packages/generated-api-client/src/client/**`
- Test: `packages/generated-api-client/src/generated-client.test.ts`

- [ ] **Step 1: Generate the contract and client**

```bash
make api-generate
```

Expected: collection operation types expose optional `page`/`page_size` and response metadata.

- [ ] **Step 2: Add generated-client type assertions**

```ts
expectTypeOf<UserPageResponse>().toMatchTypeOf<{
  items: UserResponse[];
  total: number;
  page: number | null;
  page_size: number;
  total_pages: number;
}>();
```

- [ ] **Step 3: Verify deterministic generation**

```bash
make api-check
pnpm --filter @warmy/generated-api-client test
```

Expected: zero generation drift and tests pass.

- [ ] **Step 4: Commit**

```bash
git add docs/api/openapi.json packages/generated-api-client
git commit -m "chore(api): generate pagination client"
```

### Task 6: Build the shared shadcn UI and URL pagination state

**Files:**

- Create: `apps/web/components.json`
- Create: `apps/web/src/components/ui/{card,select,pagination,resource-pagination,list-toolbar,summary-strip}.tsx`
- Create tests: matching `*.test.tsx` files
- Create: `apps/web/src/lib/pagination.ts`
- Create: `apps/web/src/lib/use-pagination-state.ts`
- Create: `apps/web/src/lib/use-pagination-state.test.tsx`
- Modify: `apps/web/package.json`, `pnpm-lock.yaml`, `docs/design.md`

- [ ] **Step 1: Write failing component and state tests**

```tsx
render(
  <ResourcePagination
    page={2}
    pageSize={20}
    total={95}
    totalPages={5}
    onPageChange={onPage}
    onPageSizeChange={onSize}
  />,
);
expect(screen.getByText("共 95 条")).toBeVisible();
await user.click(screen.getByRole("button", { name: "下一页" }));
expect(onPage).toHaveBeenCalledWith(3);
await user.click(screen.getByRole("combobox", { name: "每页条数" }));
await user.click(screen.getByRole("option", { name: "50" }));
expect(onSize).toHaveBeenCalledWith(50);
```

Test page-window ellipsis, disabled boundaries, 0/0 empty state, 390px compact controls, keyboard focus, and namespaced URL keys.

- [ ] **Step 2: Run tests and confirm missing components**

```bash
pnpm --filter @warmy/web exec vitest run src/components/ui/resource-pagination.test.tsx src/lib/use-pagination-state.test.tsx --maxWorkers=2
```

Expected: FAIL because components and hooks do not exist.

- [ ] **Step 3: Add pinned Select dependency and local shadcn primitives**

```bash
pnpm --filter @warmy/web add @radix-ui/react-select@2.3.2 --save-exact
```

`Card` exposes the standard composition. `ResourcePagination` is controlled and delegates page-window calculation to a pure `buildPageWindow(page, totalPages)` function. `usePaginationState` parses positive integer URL values, constrains page size to 10/20/50, uses `router.replace`, and resets page when filters change.

- [ ] **Step 4: Run component tests, lint, and typecheck**

```bash
pnpm --filter @warmy/web exec vitest run src/components/ui src/lib/use-pagination-state.test.tsx --maxWorkers=4
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add apps/web/components.json apps/web/package.json pnpm-lock.yaml apps/web/src/components/ui apps/web/src/lib docs/design.md
git commit -m "feat(web): add shadcn list primitives"
```

### Task 7: Migrate projects and users as reference screens

**Files:**

- Modify: `apps/web/src/features/projects/**`
- Modify: `apps/web/src/features/users/**`
- Test: existing project/user tests.

- [ ] **Step 1: Write failing page-mode Query and UI tests**

Assert API functions send `page` and `page_size`; query keys contain both; filters reset page; URL refresh restores page; summaries use server totals where provided; deleting the last item requests the previous valid page.

```tsx
expect(screen.getByRole("navigation", { name: "分页" })).toBeVisible();
expect(screen.getByRole("combobox", { name: "每页条数" })).toHaveTextContent(
  "10",
);
expect(mockListUsers).toHaveBeenCalledWith(
  expect.objectContaining({ page: 2, pageSize: 20 }),
);
```

- [ ] **Step 2: Run the focused tests and confirm failure**

```bash
pnpm --filter @warmy/web exec vitest run src/features/projects src/features/users --maxWorkers=4
```

Expected: new pagination assertions fail.

- [ ] **Step 3: Implement the reference layout**

Compose `PageHeader`, `SummaryStrip`, `ListToolbar`, existing `Table`, and `ResourcePagination`. Keep feature-specific columns and CRUD dialogs. Send all visible search, role, status, and project filters to the page-mode endpoint so rows and totals describe the same filtered collection; do not filter only the current page.

- [ ] **Step 4: Verify reference screens and responsive layout**

```bash
pnpm --filter @warmy/web exec vitest run src/features/projects src/features/users --maxWorkers=4
pnpm --filter @warmy/web typecheck
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/features/projects apps/web/src/features/users
git commit -m "feat(web): paginate project and user lists"
```

### Task 8: Migrate asset and execution screens

**Files:**

- Modify: `apps/web/src/features/{agents,datasets,test-plans,runs,environments,browser-profiles,model-configs,test-accounts}/**`
- Test: existing Feature tests.

- [ ] **Step 1: Add failing pagination and shadcn composition tests**

For each list assert explicit page parameters, query-key isolation, standard pagination controls, page-size changes, loading retention, empty/error states, and unchanged action callbacks. Detail sublists use namespaced URL pagination keys.

- [ ] **Step 2: Run the focused tests and confirm failure**

```bash
pnpm --filter @warmy/web exec vitest run src/features/agents src/features/datasets src/features/test-plans src/features/runs src/features/environments src/features/browser-profiles src/features/model-configs src/features/test-accounts --maxWorkers=4
```

Expected: new assertions fail.

- [ ] **Step 3: Migrate APIs, queries, screens, and cards**

```ts
export const resourceListQueryOptions = (
  projectId: string,
  pagination: PaginationState,
  filters: Filters,
) =>
  queryOptions({
    queryKey: [
      "resource",
      projectId,
      pagination.page,
      pagination.pageSize,
      filters,
    ],
    queryFn: () =>
      listResources(projectId, {
        page: pagination.page,
        pageSize: pagination.pageSize,
        ...filters,
      }),
    placeholderData: (previous) => previous,
  });
```

Preserve immutable-version actions, publish rules, credential handling, run state, and browser lifecycle behavior.

- [ ] **Step 4: Run tests and typecheck**

```bash
pnpm --filter @warmy/web exec vitest run src/features/agents src/features/datasets src/features/test-plans src/features/runs src/features/environments src/features/browser-profiles src/features/model-configs src/features/test-accounts --maxWorkers=4
pnpm --filter @warmy/web typecheck
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/features/{agents,datasets,test-plans,runs,environments,browser-profiles,model-configs,test-accounts}
git commit -m "feat(web): paginate asset and execution lists"
```

### Task 9: Migrate governance screens and enforce architecture rules

**Files:**

- Modify: `apps/web/src/features/{scorers,experiments,reviews,security,gates}/**`
- Modify: `apps/web/src/test/architecture/list-table-contract.test.ts`
- Create: `apps/web/src/test/architecture/pagination-contract.test.ts`

- [ ] **Step 1: Add failing governance and architecture tests**

The AST test finds exported core list screens and requires `ResourcePagination` or an approved non-paginated exemption. It rejects local duplicated page-window functions and generated-client query calls that hard-code `limit: 100` for core list screens.

```ts
expect(violations).toEqual([]);
expect(
  syntheticViolation("const pageCount = Math.ceil(total / pageSize)"),
).toContain("shared pagination");
```

- [ ] **Step 2: Run tests and confirm current violations**

```bash
pnpm --filter @warmy/web exec vitest run src/features/scorers src/features/experiments src/features/reviews src/features/security src/features/gates src/test/architecture --maxWorkers=4
```

Expected: architecture and screen assertions fail before migration.

- [ ] **Step 3: Migrate governance cards and list states**

Use Card composition only for repeated business resources, keep page sections unframed, preserve evidence links and dangerous-operation confirmation, and attach `ResourcePagination` to every core collection.

- [ ] **Step 4: Run focused and architecture tests**

```bash
pnpm --filter @warmy/web exec vitest run src/features/scorers src/features/experiments src/features/reviews src/features/security src/features/gates src/test/architecture --maxWorkers=4
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/features/{scorers,experiments,reviews,security,gates} apps/web/src/test/architecture
git commit -m "feat(web): paginate governance lists"
```

### Task 10: Add end-to-end pagination coverage and finish records

**Files:**

- Create: `apps/web/tests/e2e/core-pagination.spec.ts`
- Modify: `apps/web/tests/e2e/list-layout.spec.ts`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`
- Modify: this plan checklist.

- [ ] **Step 1: Add E2E scenarios**

Seed at least 21 deterministic rows for representative users, projects, agents, datasets, plans, and runs. Verify page 1/2/3 boundaries, 10/20/50 selection, filter reset, URL refresh restoration, deletion fallback, loading retention, dark theme, and 390px compact pagination.

```ts
await expect(page.getByRole("navigation", { name: "分页" })).toBeVisible();
await page.getByRole("combobox", { name: "每页条数" }).click();
await page.getByRole("option", { name: "20" }).click();
await expect(page).toHaveURL(/pageSize=20/);
await expect(page.getByText("第 1 / 2 页")).toBeVisible();
```

- [ ] **Step 2: Run critical E2E and inspect screenshots**

```bash
E2E_WEB_PORT=5176 E2E_API_PORT=8182 pnpm --filter @warmy/web exec playwright test tests/e2e/core-pagination.spec.ts tests/e2e/list-layout.spec.ts
```

Expected: pass at desktop/mobile and light/dark viewports with no page-level horizontal overflow.

- [ ] **Step 3: Run complete verification**

```bash
pnpm --filter @warmy/web format
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web exec vitest run --maxWorkers=4
uv run ruff format --check apps/control-api/src apps/control-api/tests
uv run ruff check apps/control-api/src apps/control-api/tests
uv run mypy apps/control-api/src
uv run pytest apps/control-api/tests -q
make api-check
pnpm --filter @warmy/web build
pnpm --filter @warmy/web perf:bundle-check
E2E_WEB_PORT=5176 E2E_API_PORT=8182 pnpm --filter @warmy/web e2e
git diff --check
```

Expected: every command passes; credential-conditioned external tests may retain only their documented skips.

- [ ] **Step 4: Update completion records**

Move `TASK-20260720-001` to completed, record actual files/API/config changes, exact test counts, skips, residual risks, and next step. Set `docs/当前任务.md` to no active task.

- [ ] **Step 5: Request final code review and address findings**

Use `superpowers:requesting-code-review` with the base commit and current HEAD. Re-run affected verification after every accepted fix.

- [ ] **Step 6: Commit the completed task**

```bash
git add apps/web/tests/e2e docs
git commit -m "test: verify core admin pagination"
```
