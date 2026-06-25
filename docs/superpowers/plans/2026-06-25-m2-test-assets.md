# M2: Agent 与测试资产 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 Agent、Dataset、TestCase、TestPlan 和 EnvironmentTemplate 的领域模型、数据库迁移、API 和前端管理界面，支持不可变版本、项目隔离、导入导出和个人草稿。

**Architecture:** 后端按 Domain/Application/Infrastructure/API 分层，新增 `agents`、`datasets`、`test_plans`、`environments` 四个模块。所有项目资源强制关联 `project_id`，已发布版本不可修改。前端按 Feature 组织，复用 M1 平台壳和 UI 组件。

**Tech Stack:** 复用 M1 技术栈，不引入新框架。

---

## File Structure

本计划创建以下结构：

```text
apps/control-api/src/agenttest/modules/
├── agents/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── api/
│   └── public.py
├── datasets/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── api/
│   └── public.py
├── test_plans/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   ├── api/
│   └── public.py
└── environments/
    ├── domain/
    ├── application/
    ├── infrastructure/
    ├── api/
    └── public.py

apps/control-api/migrations/versions/
└── 0002_test_assets.py

apps/web/src/features/
├── agents/
├── datasets/
└── test-plans/
```

---

### Task 1: Add Test Assets Database Migration

**Files:**
- Create: `apps/control-api/migrations/versions/0002_test_assets.py`
- Create: `apps/control-api/src/agenttest/modules/agents/infrastructure/persistence/models.py`
- Create: `apps/control-api/src/agenttest/modules/datasets/infrastructure/persistence/models.py`
- Create: `apps/control-api/src/agenttest/modules/test_plans/infrastructure/persistence/models.py`
- Create: `apps/control-api/src/agenttest/modules/environments/infrastructure/persistence/models.py`
- Create: `apps/control-api/tests/integration/test_test_assets_constraints.py`

- [ ] **Step 1: Write failing constraint tests**

Tests must verify:
- All tables have `project_id` with foreign key to `projects`.
- `agent_versions` unique `(agent_id, version_number)`.
- `dataset_versions` unique `(dataset_id, version_number)`.
- `test_cases` foreign key to `dataset_version_id`.
- `test_plan_versions` unique `(test_plan_id, version_number)`.
- Published versions have `published_at` set and cannot be modified (domain-level).
- `environment_templates` unique `(project_id, name)`.

- [ ] **Step 2: Create ORM models**

Tables to create:

```text
agents
  - id (UUID PK)
  - project_id (UUID FK → projects)
  - name (TEXT)
  - description (TEXT)
  - agent_type (TEXT)  -- 'generic_http' | 'canvas' | future types
  - created_at, updated_at, created_by, updated_by

agent_versions
  - id (UUID PK)
  - agent_id (UUID FK → agents)
  - version_number (INT)
  - status (TEXT)  -- 'draft' | 'published'
  - config (JSONB)  -- api_url, code_version, git_commit, model, params, system_prompt, tools, etc.
  - published_at (TIMESTAMP NULL)
  - created_at, updated_at, created_by

datasets
  - id (UUID PK)
  - project_id (UUID FK → projects)
  - name (TEXT)
  - description (TEXT)
  - created_at, updated_at, created_by, updated_by

dataset_versions
  - id (UUID PK)
  - dataset_id (UUID FK → datasets)
  - version_number (INT)
  - status (TEXT)  -- 'draft' | 'published'
  - published_at (TIMESTAMP NULL)
  - created_at, updated_at, created_by

test_cases
  - id (UUID PK)
  - dataset_version_id (UUID FK → dataset_versions)
  - name (TEXT)
  - input (JSONB)
  - initial_state (JSONB)
  - execution_mode (TEXT)  -- 'api' | 'browser'
  - expected_outcome (JSONB)
  - assertions (JSONB)
  - scorers (JSONB)
  - security_policies (JSONB)
  - tags (JSONB)
  - scenario (TEXT)
  - priority (TEXT)
  - risk_level (TEXT)
  - difficulty (TEXT)
  - test_group (TEXT)  -- 'train' | 'validation' | 'test'
  - sort_order (INT)
  - created_at, updated_at

test_plans
  - id (UUID PK)
  - project_id (UUID FK → projects)
  - name (TEXT)
  - description (TEXT)
  - created_at, updated_at, created_by, updated_by

test_plan_versions
  - id (UUID PK)
  - test_plan_id (UUID FK → test_plans)
  - version_number (INT)
  - status (TEXT)  -- 'draft' | 'published'
  - agent_version_id (UUID FK → agent_versions, NULLABLE)
  - dataset_version_id (UUID FK → dataset_versions, NULLABLE)
  - environment_template_id (UUID FK → environment_templates, NULLABLE)
  - config (JSONB)  -- api_browser_ratio, runs_per_case, concurrency, timeout, retry, scorers, thresholds, budget
  - published_at (TIMESTAMP NULL)
  - created_at, updated_at, created_by

environment_templates
  - id (UUID PK)
  - project_id (UUID FK → projects)
  - name (TEXT)
  - description (TEXT)
  - template_type (TEXT)  -- 'blank' | 'preset'
  - config (JSONB)
  - created_at, updated_at, created_by
```

Indexes:
- Unique `agent_versions(agent_id, version_number)`.
- Unique `dataset_versions(dataset_id, version_number)`.
- Unique `test_plan_versions(test_plan_id, version_number)`.
- Unique `environment_templates(project_id, name)`.
- `agents(project_id, created_at desc)`.
- `datasets(project_id, created_at desc)`.
- `test_plans(project_id, created_at desc)`.
- `test_cases(dataset_version_id, sort_order)`.

- [ ] **Step 3: Create Alembic migration**

Migration `0002_test_assets` must:
- Use Expand → Migrate → Contract pattern.
- Create all tables with proper constraints and indexes.
- Not modify existing M1 tables.

- [ ] **Step 4: Verify**

```bash
uv run alembic -c apps/control-api/alembic.ini upgrade head
uv run pytest apps/control-api/tests/integration/test_test_assets_constraints.py -v
```

Expected: PASS (or skipped if no PostgreSQL).

- [ ] **Step 5: Commit**

```bash
git add apps/control-api/migrations apps/control-api/src/agenttest/modules/*/infrastructure/persistence/models.py apps/control-api/tests/integration
git commit -m "feat(db): add test assets schema"
```

---

### Task 2: Implement Agent Domain and Application

**Files:**
- Create: `apps/control-api/src/agenttest/modules/agents/domain/entities.py`
- Create: `apps/control-api/src/agenttest/modules/agents/domain/value_objects.py`
- Create: `apps/control-api/src/agenttest/modules/agents/domain/repositories.py`
- Create: `apps/control-api/src/agenttest/modules/agents/application/commands.py`
- Create: `apps/control-api/src/agenttest/modules/agents/application/queries.py`
- Create: `apps/control-api/src/agenttest/modules/agents/application/ports.py`
- Create: `apps/control-api/src/agenttest/modules/agents/infrastructure/persistence/repositories.py`
- Create: `apps/control-api/src/agenttest/modules/agents/public.py`
- Create: `apps/control-api/tests/unit/agents/test_agent_domain.py`

- [ ] **Step 1: Write failing domain tests**

Cover:
- Agent belongs to a project (`project_id`).
- AgentVersion starts as draft, can be published.
- Published AgentVersion is immutable — editing creates a new draft version.
- Version number auto-increments per agent.
- Generic HTTP Agent config schema validation (api_url required, timeout > 0).

- [ ] **Step 2: Implement domain**

Entities:
- `Agent`: project_id, name, description, agent_type.
- `AgentVersion`: agent_id, version_number, status, config, published_at.
- `AgentConfig` (value object): api_url, code_version, git_commit, model, model_params, system_prompt, tools, timeout, max_steps, cost_limit.

Domain rules:
- `publish()`: sets status to published, sets published_at.
- `is_editable`: only draft versions can be modified.
- `create_new_version_from()`: copies config from a published version to a new draft.

- [ ] **Step 3: Implement application layer**

Commands:
- `CreateAgent`: creates agent in a project.
- `UpdateAgent`: updates name/description.
- `CreateAgentVersion`: creates a new draft version.
- `UpdateAgentVersion`: updates draft version config.
- `PublishAgentVersion`: publishes a draft version.

Queries:
- `ListAgents`: paginated, filtered by project.
- `GetAgent`: single agent with latest version.
- `ListAgentVersions`: versions for an agent.

- [ ] **Step 4: Implement infrastructure**

SQLAlchemy repositories following the same pattern as `projects` module.

- [ ] **Step 5: Create public export**

`public.py` exports `AgentVersionRef` (agent_version_id, agent_id, version_number) for other modules to reference.

- [ ] **Step 6: Verify**

```bash
uv run pytest apps/control-api/tests/unit/agents -v
uv run pytest apps/control-api/tests/architecture -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/control-api/src/agenttest/modules/agents apps/control-api/tests/unit/agents
git commit -m "feat(agents): add agent domain and application layer"
```

---

### Task 3: Implement Dataset Domain and Application

**Files:**
- Create: `apps/control-api/src/agenttest/modules/datasets/domain/entities.py`
- Create: `apps/control-api/src/agenttest/modules/datasets/domain/value_objects.py`
- Create: `apps/control-api/src/agenttest/modules/datasets/domain/repositories.py`
- Create: `apps/control-api/src/agenttest/modules/datasets/application/commands.py`
- Create: `apps/control-api/src/agenttest/modules/datasets/application/queries.py`
- Create: `apps/control-api/src/agenttest/modules/datasets/application/ports.py`
- Create: `apps/control-api/src/agenttest/modules/datasets/application/import_export.py`
- Create: `apps/control-api/src/agenttest/modules/datasets/infrastructure/persistence/repositories.py`
- Create: `apps/control-api/src/agenttest/modules/datasets/public.py`
- Create: `apps/control-api/tests/unit/datasets/test_dataset_domain.py`
- Create: `apps/control-api/tests/unit/datasets/test_import_export.py`

- [ ] **Step 1: Write failing domain tests**

Cover:
- Dataset belongs to a project.
- DatasetVersion starts as draft, can be published.
- Published DatasetVersion is immutable.
- TestCase belongs to a DatasetVersion.
- TestCase has name, input, execution_mode, assertions, scorers.
- Tags, priority, risk_level, difficulty and test_group are validated.
- Editing a published dataset creates a new draft version.

- [ ] **Step 2: Implement domain**

Entities:
- `Dataset`: project_id, name, description.
- `DatasetVersion`: dataset_id, version_number, status, published_at.
- `TestCase`: dataset_version_id, name, input, initial_state, execution_mode, expected_outcome, assertions, scorers, security_policies, tags, scenario, priority, risk_level, difficulty, test_group, sort_order.

- [ ] **Step 3: Implement import/export**

`import_export.py` must support:
- JSON import: array of test case objects.
- JSONL import: one JSON object per line.
- CSV import: header row defines fields, JSON columns parsed.
- Export to JSON, JSONL, CSV.
- Line-by-line error reporting with row number and reason.
- No partial state on import failure — all-or-nothing within a transaction.

- [ ] **Step 4: Implement application layer**

Commands:
- `CreateDataset`, `UpdateDataset`.
- `CreateDatasetVersion`, `AddTestCases`, `UpdateTestCase`, `DeleteTestCase`, `ReorderTestCases`.
- `PublishDatasetVersion`.
- `ImportTestCases` (format, content).
- `ExportDatasetVersion` (format) → returns content.

Queries:
- `ListDatasets`, `GetDataset`, `ListDatasetVersions`.
- `ListTestCases` (paginated, filterable by tag/group/priority).

- [ ] **Step 5: Verify**

```bash
uv run pytest apps/control-api/tests/unit/datasets -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/control-api/src/agenttest/modules/datasets apps/control-api/tests/unit/datasets
git commit -m "feat(datasets): add dataset domain, import/export and application layer"
```

---

### Task 4: Implement TestPlan Domain and Application

**Files:**
- Create: `apps/control-api/src/agenttest/modules/test_plans/domain/entities.py`
- Create: `apps/control-api/src/agenttest/modules/test_plans/domain/repositories.py`
- Create: `apps/control-api/src/agenttest/modules/test_plans/application/commands.py`
- Create: `apps/control-api/src/agenttest/modules/test_plans/application/queries.py`
- Create: `apps/control-api/src/agenttest/modules/test_plans/application/ports.py`
- Create: `apps/control-api/src/agenttest/modules/test_plans/infrastructure/persistence/repositories.py`
- Create: `apps/control-api/src/agenttest/modules/test_plans/public.py`
- Create: `apps/control-api/tests/unit/test_plans/test_test_plan_domain.py`

- [ ] **Step 1: Write failing domain tests**

Cover:
- TestPlan belongs to a project.
- TestPlanVersion references specific AgentVersion, DatasetVersion and EnvironmentTemplate.
- TestPlanVersion starts as draft, can be published.
- Published TestPlanVersion is immutable.
- Config includes api_browser_ratio, runs_per_case, concurrency, timeout, retry_policy, scorers, pass_threshold, cost_budget.

- [ ] **Step 2: Implement domain**

Entities:
- `TestPlan`: project_id, name, description.
- `TestPlanVersion`: test_plan_id, version_number, status, agent_version_id, dataset_version_id, environment_template_id, config, published_at.
- `TestPlanConfig` (value object): api_browser_ratio, runs_per_case, concurrency, timeout, retry_policy, scorers, pass_threshold, cost_budget.

Domain rules:
- Agent/Dataset/Environment references must be published versions.
- `publish()` validates that all references are published.

- [ ] **Step 3: Implement application layer**

Commands:
- `CreateTestPlan`, `UpdateTestPlan`.
- `CreateTestPlanVersion`, `UpdateTestPlanVersion`, `PublishTestPlanVersion`.

Queries:
- `ListTestPlans`, `GetTestPlan`, `ListTestPlanVersions`.

- [ ] **Step 4: Verify**

```bash
uv run pytest apps/control-api/tests/unit/test_plans -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/control-api/src/agenttest/modules/test_plans apps/control-api/tests/unit/test_plans
git commit -m "feat(test-plans): add test plan domain and application layer"
```

---

### Task 5: Implement EnvironmentTemplate Domain and Application

**Files:**
- Create: `apps/control-api/src/agenttest/modules/environments/domain/entities.py`
- Create: `apps/control-api/src/agenttest/modules/environments/domain/repositories.py`
- Create: `apps/control-api/src/agenttest/modules/environments/application/commands.py`
- Create: `apps/control-api/src/agenttest/modules/environments/application/queries.py`
- Create: `apps/control-api/src/agenttest/modules/environments/application/ports.py`
- Create: `apps/control-api/src/agenttest/modules/environments/infrastructure/persistence/repositories.py`
- Create: `apps/control-api/src/agenttest/modules/environments/public.py`
- Create: `apps/control-api/tests/unit/environments/test_environment_domain.py`

- [ ] **Step 1: Write failing domain tests**

Cover:
- EnvironmentTemplate belongs to a project.
- template_type is 'blank' or 'preset'.
- Blank template has empty config.
- Preset template has config with initial state, mock services, test accounts.
- Unique name per project.

- [ ] **Step 2: Implement domain and application**

Commands: `CreateEnvironmentTemplate`, `UpdateEnvironmentTemplate`, `DeleteEnvironmentTemplate`.
Queries: `ListEnvironmentTemplates`, `GetEnvironmentTemplate`.

- [ ] **Step 3: Verify**

```bash
uv run pytest apps/control-api/tests/unit/environments -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add apps/control-api/src/agenttest/modules/environments apps/control-api/tests/unit/environments
git commit -m "feat(environments): add environment template domain and application layer"
```

---

### Task 6: Add Test Assets API Routes

**Files:**
- Create: `apps/control-api/src/agenttest/modules/agents/api/router.py`
- Create: `apps/control-api/src/agenttest/modules/agents/api/schemas.py`
- Create: `apps/control-api/src/agenttest/modules/datasets/api/router.py`
- Create: `apps/control-api/src/agenttest/modules/datasets/api/schemas.py`
- Create: `apps/control-api/src/agenttest/modules/test_plans/api/router.py`
- Create: `apps/control-api/src/agenttest/modules/test_plans/api/schemas.py`
- Create: `apps/control-api/src/agenttest/modules/environments/api/router.py`
- Create: `apps/control-api/src/agenttest/modules/environments/api/schemas.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Create: `apps/control-api/tests/contract/test_agents_api.py`
- Create: `apps/control-api/tests/contract/test_datasets_api.py`
- Create: `apps/control-api/tests/contract/test_test_plans_api.py`
- Create: `apps/control-api/tests/contract/test_environments_api.py`

- [ ] **Step 1: Write failing API tests**

Endpoints:

```text
# Agents
GET    /api/v1/projects/{project_id}/agents
POST   /api/v1/projects/{project_id}/agents
GET    /api/v1/projects/{project_id}/agents/{agent_id}
PATCH  /api/v1/projects/{project_id}/agents/{agent_id}
GET    /api/v1/projects/{project_id}/agents/{agent_id}/versions
POST   /api/v1/projects/{project_id}/agents/{agent_id}/versions
GET    /api/v1/projects/{project_id}/agents/{agent_id}/versions/{version_id}
PATCH  /api/v1/projects/{project_id}/agents/{agent_id}/versions/{version_id}
POST   /api/v1/projects/{project_id}/agents/{agent_id}/versions/{version_id}/publish

# Datasets
GET    /api/v1/projects/{project_id}/datasets
POST   /api/v1/projects/{project_id}/datasets
GET    /api/v1/projects/{project_id}/datasets/{dataset_id}
PATCH  /api/v1/projects/{project_id}/datasets/{dataset_id}
GET    /api/v1/projects/{project_id}/datasets/{dataset_id}/versions
POST   /api/v1/projects/{project_id}/datasets/{dataset_id}/versions
GET    /api/v1/projects/{project_id}/datasets/{dataset_id}/versions/{version_id}
POST   /api/v1/projects/{project_id}/datasets/{dataset_id}/versions/{version_id}/publish
GET    /api/v1/projects/{project_id}/datasets/{dataset_id}/versions/{version_id}/cases
POST   /api/v1/projects/{project_id}/datasets/{dataset_id}/versions/{version_id}/cases
PATCH  /api/v1/projects/{project_id}/datasets/{dataset_id}/versions/{version_id}/cases/{case_id}
DELETE /api/v1/projects/{project_id}/datasets/{dataset_id}/versions/{version_id}/cases/{case_id}
POST   /api/v1/projects/{project_id}/datasets/{dataset_id}/versions/{version_id}/import
GET    /api/v1/projects/{project_id}/datasets/{dataset_id}/versions/{version_id}/export

# TestPlans
GET    /api/v1/projects/{project_id}/test-plans
POST   /api/v1/projects/{project_id}/test-plans
GET    /api/v1/projects/{project_id}/test-plans/{plan_id}
PATCH  /api/v1/projects/{project_id}/test-plans/{plan_id}
GET    /api/v1/projects/{project_id}/test-plans/{plan_id}/versions
POST   /api/v1/projects/{project_id}/test-plans/{plan_id}/versions
GET    /api/v1/projects/{project_id}/test-plans/{plan_id}/versions/{version_id}
PATCH  /api/v1/projects/{project_id}/test-plans/{plan_id}/versions/{version_id}
POST   /api/v1/projects/{project_id}/test-plans/{plan_id}/versions/{version_id}/publish

# EnvironmentTemplates
GET    /api/v1/projects/{project_id}/environment-templates
POST   /api/v1/projects/{project_id}/environment-templates
GET    /api/v1/projects/{project_id}/environment-templates/{template_id}
PATCH  /api/v1/projects/{project_id}/environment-templates/{template_id}
DELETE /api/v1/projects/{project_id}/environment-templates/{template_id}
```

All endpoints require project membership. Developer/tester can create/edit. Viewer can only GET. Non-members get 404.

- [ ] **Step 2: Implement API routers and schemas**

Follow the same pattern as `projects` module:
- CSRF protection on all mutations.
- Project membership check via dependency.
- Problem Details for errors.
- Pagination via cursor.

- [ ] **Step 3: Register routers in app factory**

- [ ] **Step 4: Verify**

```bash
uv run pytest apps/control-api/tests/contract/test_agents_api.py apps/control-api/tests/contract/test_datasets_api.py apps/control-api/tests/contract/test_test_plans_api.py apps/control-api/tests/contract/test_environments_api.py -v
uv run ruff check apps/control-api
uv run mypy apps/control-api/src
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/control-api/src/agenttest/modules/*/api apps/control-api/src/agenttest/bootstrap/app.py apps/control-api/tests/contract
git commit -m "feat(api): add test assets CRUD endpoints"
```

---

### Task 7: Update OpenAPI and Generate Client

**Files:**
- Modify: `docs/api/openapi.json`
- Modify: `packages/generated-api-client/src/`
- Modify: `docs/api/identity-and-projects.md` → rename or create `docs/api/test-assets.md`

- [ ] **Step 1: Regenerate OpenAPI**

```bash
make api-generate
make api-check
```

- [ ] **Step 2: Verify no drift**

```bash
git diff --exit-code -- docs/api/openapi.json packages/generated-api-client/src
```

- [ ] **Step 3: Commit**

```bash
git add docs/api/openapi.json packages/generated-api-client/src docs/api
git commit -m "build: regenerate API client for test assets"
```

---

### Task 8: Build Agent Management UI

**Files:**
- Create: `apps/web/src/features/agents/api.ts`
- Create: `apps/web/src/features/agents/agent-list.tsx`
- Create: `apps/web/src/features/agents/agent-detail.tsx`
- Create: `apps/web/src/features/agents/agent-version-dialog.tsx`
- Create: `apps/web/src/features/agents/index.ts`
- Create: `apps/web/src/app/(platform)/projects/[projectId]/agents/page.tsx`
- Create: `apps/web/src/app/(platform)/projects/[projectId]/agents/[agentId]/page.tsx`
- Create: `apps/web/src/features/agents/tests/agent-list.test.tsx`

- [ ] **Step 1: Write failing component tests**

Cover:
- Agent list loading, empty, error and populated states.
- Create agent dialog with name and type.
- Agent detail with version list.
- Create version dialog with HTTP Agent config form.
- Publish version button with confirmation.
- Published versions show lock icon and no edit button.
- Project isolation: non-member sees 404.

- [ ] **Step 2: Implement UI**

Follow M1 patterns:
- Use generated API client.
- TanStack Query for data fetching.
- Reuse AppShell, Table, Dialog, Drawer, Badge components.
- High-density table for agent list.
- Drawer for agent detail.
- Dialog for create/edit.

- [ ] **Step 3: Verify**

```bash
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web test
pnpm --filter @warmy/web build
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/features/agents apps/web/src/app
git commit -m "feat(web): add agent management UI"
```

---

### Task 9: Build Dataset Management UI

**Files:**
- Create: `apps/web/src/features/datasets/api.ts`
- Create: `apps/web/src/features/datasets/dataset-list.tsx`
- Create: `apps/web/src/features/datasets/dataset-detail.tsx`
- Create: `apps/web/src/features/datasets/test-case-editor.tsx`
- Create: `apps/web/src/features/datasets/import-dialog.tsx`
- Create: `apps/web/src/features/datasets/export-button.tsx`
- Create: `apps/web/src/features/datasets/index.ts`
- Create: `apps/web/src/app/(platform)/projects/[projectId]/datasets/page.tsx`
- Create: `apps/web/src/app/(platform)/projects/[projectId]/datasets/[datasetId]/page.tsx`
- Create: `apps/web/src/features/datasets/tests/dataset-list.test.tsx`
- Create: `apps/web/src/features/datasets/tests/import-export.test.tsx`

- [ ] **Step 1: Write failing component tests**

Cover:
- Dataset list states.
- Dataset detail with version tabs and test case table.
- Test case editor dialog (JSON input/output/assertions).
- Import dialog with format selector and file/text input.
- Import error display (line number + reason).
- Export button (JSON/JSONL/CSV).
- Publish version with confirmation.
- Published versions are read-only.

- [ ] **Step 2: Implement UI**

- [ ] **Step 3: Verify**

```bash
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web test
pnpm --filter @warmy/web build
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/features/datasets apps/web/src/app
git commit -m "feat(web): add dataset management UI with import/export"
```

---

### Task 10: Build TestPlan Management UI

**Files:**
- Create: `apps/web/src/features/test-plans/api.ts`
- Create: `apps/web/src/features/test-plans/test-plan-list.tsx`
- Create: `apps/web/src/features/test-plans/test-plan-detail.tsx`
- Create: `apps/web/src/features/test-plans/test-plan-version-dialog.tsx`
- Create: `apps/web/src/features/test-plans/index.ts`
- Create: `apps/web/src/app/(platform)/projects/[projectId]/test-plans/page.tsx`
- Create: `apps/web/src/app/(platform)/projects/[projectId]/test-plans/[planId]/page.tsx`
- Create: `apps/web/src/features/test-plans/tests/test-plan-list.test.tsx`

- [ ] **Step 1: Write failing component tests**

Cover:
- TestPlan list states.
- TestPlan detail with version list.
- Create version dialog with agent/dataset/environment selectors.
- Config form (concurrency, timeout, runs_per_case, pass_threshold).
- Publish version.
- Published versions are read-only.
- Only published agent/dataset/environment versions appear in selectors.

- [ ] **Step 2: Implement UI**

- [ ] **Step 3: Verify**

```bash
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web test
pnpm --filter @warmy/web build
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add apps/web/src/features/test-plans apps/web/src/app
git commit -m "feat(web): add test plan management UI"
```

---

### Task 11: Update Project Overview and Navigation

**Files:**
- Modify: `apps/web/src/app/(platform)/projects/[projectId]/overview/page.tsx`
- Modify: `apps/web/src/components/layout/app-shell.tsx`

- [ ] **Step 1: Update navigation**

Add links to Agents, Datasets and Test Plans in the left navigation. Show counts in project overview.

- [ ] **Step 2: Update project overview**

Show test asset summary:
- Agent count and latest versions.
- Dataset count and total test cases.
- TestPlan count and latest versions.

- [ ] **Step 3: Verify**

```bash
pnpm --filter @warmy/web test
pnpm --filter @warmy/web build
```

- [ ] **Step 4: Commit**

```bash
git add apps/web/src
git commit -m "feat(web): update navigation and project overview for test assets"
```

---

### Task 12: Acceptance Tests and Documentation

**Files:**
- Create: `apps/web/playwright/test-assets.spec.ts`
- Create: `docs/api/test-assets.md`
- Modify: `README.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [ ] **Step 1: Write E2E acceptance tests**

Scenarios:
1. Developer creates an Agent and publishes a version.
2. Developer creates a Dataset, adds test cases via import, publishes.
3. Developer creates a TestPlan referencing published Agent and Dataset versions.
4. Viewer can see but not edit test assets.
5. Non-member gets 404 on project test assets.
6. Published version cannot be edited.
7. Import with invalid data shows line-by-line errors.

- [ ] **Step 2: Write API documentation**

Document all test assets endpoints in `docs/api/test-assets.md`.

- [ ] **Step 3: Update README**

Add test assets management to the feature list.

- [ ] **Step 4: Run full verification**

```bash
make verify
make api-check
```

Expected: PASS.

- [ ] **Step 5: Update progress documents**

- [ ] **Step 6: Commit**

```bash
git add apps/web/playwright docs README.md
git commit -m "test: add M2 acceptance tests and documentation"
```

---

## Plan Completion Checklist

- [ ] All test asset tables have `project_id` with FK to projects.
- [ ] Published versions are immutable at domain level.
- [ ] Non-project members get 404 on all test asset endpoints.
- [ ] Developer/tester can create; viewer can only read.
- [ ] Import errors are reported line by line.
- [ ] Export supports JSON, JSONL and CSV.
- [ ] TestPlan references only published versions.
- [ ] OpenAPI Client has no drift.
- [ ] Architecture boundary tests pass.
- [ ] UI covers loading, empty, error and permission states.
- [ ] Current task and progress documents are updated.
