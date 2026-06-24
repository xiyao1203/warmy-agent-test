# Platform Foundation and Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可持续开发的 Monorepo，并交付登录、超级管理员用户管理、项目成员和项目级数据隔离的第一版可运行平台。

**Architecture:** Web 使用 Next.js App Router，Control API 使用 FastAPI 模块化单体。身份和项目模块按 Domain/Application/Infrastructure/API 分层，浏览器会话使用可撤销的服务端 Session Cookie，PostgreSQL 保存业务事实，项目权限由后端 Policy 强制执行。

**Tech Stack:** pnpm、Next.js、React、TypeScript、Tailwind CSS、Radix UI、TanStack Query、Vitest、Playwright、Python、uv、FastAPI、Pydantic、SQLAlchemy、Alembic、PostgreSQL、Redis、Temporal、MinIO、Pytest、Ruff、mypy、Docker Compose。

---

## File Structure

本计划创建以下结构：

```text
.
├── apps/
│   ├── web/
│   ├── control-api/
│   └── admin-cli/
├── packages/
│   ├── generated-api-client/
│   ├── eslint-config/
│   └── typescript-config/
├── infra/
│   └── compose/
├── scripts/
├── docs/
│   ├── adr/
│   ├── api/
│   └── runbooks/
├── .github/workflows/
├── Makefile
├── package.json
├── pnpm-workspace.yaml
├── pnpm-lock.yaml
├── pyproject.toml
└── uv.lock
```

后端模块：

```text
apps/control-api/src/agenttest/modules/
├── identity/
├── projects/
└── audit/
```

M1 只创建当前需要的模块，不提前创建 Agent、Dataset、Run 和 Worker 空目录。

---

### Task 1: Establish Monorepo Tooling

**Files:**
- Create: `package.json`
- Create: `pnpm-workspace.yaml`
- Create: `pyproject.toml`
- Create: `Makefile`
- Create: `.editorconfig`
- Modify: `.gitignore`
- Test: `scripts/check_workspace.sh`

- [ ] **Step 1: Write the workspace verification script**

```bash
#!/usr/bin/env bash
set -euo pipefail

test -f package.json
test -f pnpm-workspace.yaml
test -f pyproject.toml
test -d apps/web
test -d apps/control-api
test -d packages/generated-api-client
```

- [ ] **Step 2: Run the script and verify it fails**

Run:

```bash
bash scripts/check_workspace.sh
```

Expected: FAIL because the workspace files and directories do not exist.

- [ ] **Step 3: Create the root Node workspace**

`package.json`:

```json
{
  "name": "warmy-agent-test",
  "private": true,
  "packageManager": "pnpm@10",
  "scripts": {
    "format": "pnpm -r format",
    "lint": "pnpm -r lint",
    "typecheck": "pnpm -r typecheck",
    "test": "pnpm -r test",
    "build": "pnpm -r build",
    "api:generate": "pnpm --filter @warmy/generated-api-client generate"
  }
}
```

`pnpm-workspace.yaml`:

```yaml
packages:
  - apps/web
  - packages/*
```

- [ ] **Step 4: Create the root Python workspace**

`pyproject.toml`:

```toml
[project]
name = "warmy-agent-test-workspace"
version = "0.1.0"
requires-python = ">=3.12,<3.14"

[tool.uv.workspace]
members = [
  "apps/control-api",
  "apps/admin-cli"
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "ASYNC"]

[tool.pytest.ini_options]
addopts = "-ra"
```

- [ ] **Step 5: Create the root developer commands**

`Makefile`:

```make
.PHONY: bootstrap format lint typecheck test build verify

bootstrap:
	pnpm install --frozen-lockfile
	uv sync --all-packages

format:
	pnpm format
	uv run ruff format .

lint:
	pnpm lint
	uv run ruff check .

typecheck:
	pnpm typecheck
	uv run mypy apps/control-api/src apps/admin-cli/src

test:
	pnpm test
	uv run pytest

build:
	pnpm build

verify: format lint typecheck test build
```

- [ ] **Step 6: Add editor and ignore rules**

`.editorconfig`:

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 2

[*.py]
indent_size = 4
```

Add generated and local paths to `.gitignore`:

```gitignore
.coverage
htmlcov/
.turbo/
playwright-report/
test-results/
*.sqlite3
```

- [ ] **Step 7: Create initial directories and lock files**

Run:

```bash
mkdir -p apps/web apps/control-api apps/admin-cli packages/generated-api-client
corepack enable
pnpm install
uv lock
bash scripts/check_workspace.sh
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add package.json pnpm-workspace.yaml pyproject.toml Makefile .editorconfig .gitignore scripts/check_workspace.sh pnpm-lock.yaml uv.lock
git commit -m "build: establish monorepo tooling"
```

---

### Task 2: Add Local Infrastructure

**Files:**
- Create: `infra/compose/compose.yaml`
- Create: `infra/compose/.env.example`
- Create: `scripts/wait_for_services.py`
- Create: `docs/runbooks/local-development.md`
- Test: `scripts/test_compose_config.sh`

- [ ] **Step 1: Write the failing Compose configuration test**

```bash
#!/usr/bin/env bash
set -euo pipefail
docker compose -f infra/compose/compose.yaml config --quiet
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
bash scripts/test_compose_config.sh
```

Expected: FAIL because `infra/compose/compose.yaml` does not exist.

- [ ] **Step 3: Create Compose services**

`infra/compose/compose.yaml` must define:

- PostgreSQL with database `agenttest`.
- Redis with persistence disabled for local development.
- Temporal Server and Temporal UI.
- MinIO and a one-shot bucket initializer.
- Named volumes for PostgreSQL, Temporal, and MinIO.
- Health checks for PostgreSQL, Redis, Temporal, and MinIO.
- No floating `latest` image tags.

Use environment variables from `infra/compose/.env.example`:

```dotenv
POSTGRES_DB=agenttest
POSTGRES_USER=agenttest
POSTGRES_PASSWORD=agenttest-local
MINIO_ROOT_USER=agenttest
MINIO_ROOT_PASSWORD=agenttest-local-secret
MINIO_BUCKET=agenttest-artifacts
```

- [ ] **Step 4: Add service wait script**

`scripts/wait_for_services.py` must:

- Read PostgreSQL, Redis, Temporal, and MinIO endpoints from environment.
- Retry for at most 60 seconds.
- Exit non-zero with the unavailable service name.
- Never print passwords.

- [ ] **Step 5: Document local startup**

`docs/runbooks/local-development.md` must include:

```text
cp infra/compose/.env.example infra/compose/.env
docker compose --env-file infra/compose/.env -f infra/compose/compose.yaml up -d
uv run python scripts/wait_for_services.py
```

- [ ] **Step 6: Verify Compose**

Run:

```bash
bash scripts/test_compose_config.sh
docker compose --env-file infra/compose/.env.example -f infra/compose/compose.yaml up -d
uv run python scripts/wait_for_services.py
docker compose --env-file infra/compose/.env.example -f infra/compose/compose.yaml down
```

Expected: all services become healthy and stop cleanly.

- [ ] **Step 7: Commit**

```bash
git add infra/compose scripts docs/runbooks/local-development.md
git commit -m "build: add local infrastructure stack"
```

---

### Task 3: Scaffold the FastAPI Control Plane

**Files:**
- Create: `apps/control-api/pyproject.toml`
- Create: `apps/control-api/src/agenttest/main.py`
- Create: `apps/control-api/src/agenttest/bootstrap/app.py`
- Create: `apps/control-api/src/agenttest/bootstrap/settings.py`
- Create: `apps/control-api/src/agenttest/shared/api/problem_details.py`
- Create: `apps/control-api/src/agenttest/entrypoints/http/health.py`
- Create: `apps/control-api/tests/unit/test_settings.py`
- Create: `apps/control-api/tests/contract/test_health.py`
- Create: `apps/control-api/AGENTS.md`

- [ ] **Step 1: Write failing health and settings tests**

```python
from fastapi.testclient import TestClient

from agenttest.bootstrap.app import create_app


def test_health_returns_service_status() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "control-api",
        "status": "ok",
        "version": "0.1.0",
    }
```

```python
import pytest
from pydantic import ValidationError

from agenttest.bootstrap.settings import Settings


def test_settings_require_database_url() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url="")
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
uv run pytest apps/control-api/tests/unit/test_settings.py apps/control-api/tests/contract/test_health.py -v
```

Expected: FAIL because the application modules do not exist.

- [ ] **Step 3: Create package configuration**

`apps/control-api/pyproject.toml` must include FastAPI, Uvicorn, Pydantic Settings, SQLAlchemy async, asyncpg, Alembic, Argon2, structlog, OpenTelemetry, pytest, pytest-asyncio, httpx, Ruff and mypy. Resolve the current stable versions during execution and let `uv.lock` pin them.

- [ ] **Step 4: Implement typed settings**

```python
from pydantic import AnyHttpUrl, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AGENTTEST_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "control-api"
    app_version: str = "0.1.0"
    environment: str = "local"
    database_url: PostgresDsn
    web_origin: AnyHttpUrl = "http://localhost:3000"
    session_cookie_name: str = "agenttest_session"
    session_ttl_seconds: int = Field(default=28800, ge=300, le=604800)
```

- [ ] **Step 5: Implement app factory and health route**

`create_app()` must:

- Set title and version.
- Include `/api/v1/health`.
- Return RFC 7807 `application/problem+json` for known application errors.
- Avoid creating database connections at import time.

- [ ] **Step 6: Add local module instructions**

`apps/control-api/AGENTS.md` must contain:

- Required commands.
- Domain/Application/Infrastructure/API dependency rule.
- Migration and project isolation requirements.
- Prohibition on direct ORM use from API routes.

- [ ] **Step 7: Run verification**

```bash
uv sync --all-packages
uv run pytest apps/control-api/tests/unit/test_settings.py apps/control-api/tests/contract/test_health.py -v
uv run ruff check apps/control-api
uv run mypy apps/control-api/src
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add apps/control-api pyproject.toml uv.lock
git commit -m "feat(api): scaffold control plane"
```

---

### Task 4: Scaffold the Next.js Platform Shell

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/next.config.ts`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/src/app/layout.tsx`
- Create: `apps/web/src/app/page.tsx`
- Create: `apps/web/src/app/globals.css`
- Create: `apps/web/src/components/layout/app-shell.tsx`
- Create: `apps/web/src/components/ui/button.tsx`
- Create: `apps/web/src/styles/tokens.css`
- Create: `apps/web/src/test/setup.ts`
- Create: `apps/web/src/components/layout/app-shell.test.tsx`
- Create: `apps/web/AGENTS.md`

- [ ] **Step 1: Write the failing shell test**

```tsx
import { render, screen } from "@testing-library/react";
import { AppShell } from "./app-shell";

it("renders the primary platform navigation", () => {
  render(<AppShell userName="Jason" projectName="Demo Project" />);

  expect(screen.getByText("Warmy Agent Test")).toBeInTheDocument();
  expect(screen.getByText("测试 Agent")).toBeInTheDocument();
  expect(screen.getByText("运行记录")).toBeInTheDocument();
  expect(screen.getByText("Jason")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test and verify it fails**

```bash
pnpm --filter @warmy/web test -- app-shell.test.tsx
```

Expected: FAIL because the Web package and component do not exist.

- [ ] **Step 3: Create the Web package**

Use the current stable Next.js and React releases at execution time, then lock them in `pnpm-lock.yaml`. Configure:

- App Router.
- TypeScript Strict.
- Tailwind CSS.
- ESLint.
- Vitest, Testing Library and jsdom.
- Playwright as a development dependency.
- TanStack Query, React Hook Form and Zod.
- Radix UI primitives needed by M1.

- [ ] **Step 4: Implement design tokens**

`tokens.css` must define semantic CSS variables for:

```text
background
surface
surface-subtle
border
text
text-muted
accent
success
warning
danger
focus-ring
```

Do not expose product pages to raw hexadecimal colors.

- [ ] **Step 5: Implement platform shell**

The initial shell must include:

- Product name.
- Project switcher placeholder.
- Left navigation for Overview, Test Agent, Agents, Datasets, Plans and Runs.
- User menu placeholder.
- Responsive collapse below 1280px.
- Keyboard-visible focus styles.

- [ ] **Step 6: Add local module instructions**

`apps/web/AGENTS.md` must contain:

- `pnpm --filter @warmy/web` commands.
- Feature import boundaries.
- Design token requirement.
- Required component, accessibility and E2E checks.

- [ ] **Step 7: Run verification**

```bash
pnpm install
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web test
pnpm --filter @warmy/web build
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add apps/web package.json pnpm-lock.yaml
git commit -m "feat(web): scaffold platform shell"
```

---

### Task 5: Generate the TypeScript API Client

**Files:**
- Create: `packages/generated-api-client/package.json`
- Create: `packages/generated-api-client/openapi-ts.config.ts`
- Create: `packages/generated-api-client/src/index.ts`
- Create: `scripts/export_openapi.py`
- Create: `docs/api/openapi.json`
- Modify: `Makefile`
- Test: `packages/generated-api-client/src/index.test.ts`

- [ ] **Step 1: Write the failing generated client test**

```ts
import { describe, expect, it } from "vitest";
import { createClient } from "./index";

describe("generated API client", () => {
  it("creates a client with the configured base URL", () => {
    const client = createClient("http://localhost:8000");
    expect(client).toBeDefined();
  });
});
```

- [ ] **Step 2: Export OpenAPI**

`scripts/export_openapi.py` must import `create_app()`, serialize `app.openapi()` with stable key ordering, and write `docs/api/openapi.json`.

- [ ] **Step 3: Configure generation**

Use `@hey-api/openapi-ts` as the OpenAPI TypeScript client generator. Resolve its current stable version during execution and pin it in `pnpm-lock.yaml`. The generated package must:

- Export typed request and response models.
- Export a `createClient(baseUrl)` function.
- Never be edited manually.
- Regenerate from `docs/api/openapi.json`.

- [ ] **Step 4: Add drift check**

Add Make targets:

```make
api-generate:
	uv run python scripts/export_openapi.py
	pnpm --filter @warmy/generated-api-client generate

api-check:
	$(MAKE) api-generate
	git diff --exit-code -- docs/api/openapi.json packages/generated-api-client/src
```

- [ ] **Step 5: Verify**

```bash
make api-generate
pnpm --filter @warmy/generated-api-client test
make api-check
```

Expected: PASS and no generated drift.

- [ ] **Step 6: Commit**

```bash
git add packages/generated-api-client scripts/export_openapi.py docs/api/openapi.json Makefile pnpm-lock.yaml
git commit -m "build: generate typed API client"
```

---

### Task 6: Add CI Quality Gates

**Files:**
- Create: `.github/workflows/ci.yaml`
- Create: `.github/dependabot.yml`
- Create: `scripts/check_architecture.py`
- Create: `apps/control-api/tests/architecture/test_module_boundaries.py`
- Modify: `Makefile`

- [ ] **Step 1: Write a failing architecture test**

The test must scan Python imports and fail when:

- `domain` imports FastAPI, SQLAlchemy, Redis or Temporal.
- An API router imports an infrastructure ORM model.
- One module imports another module's internal path instead of `public.py`.

- [ ] **Step 2: Run the architecture test**

```bash
uv run pytest apps/control-api/tests/architecture -v
```

Expected: PASS for the current minimal code and fail when a fixture introduces a prohibited import.

- [ ] **Step 3: Create CI**

CI jobs:

1. `python-quality`: Ruff, mypy and Pytest.
2. `web-quality`: ESLint, TypeScript, Vitest and Build.
3. `contract`: OpenAPI drift.
4. `compose`: Docker Compose config validation.
5. `security`: secret scan and dependency audit.

Use PostgreSQL service only for integration jobs that require it.

- [ ] **Step 4: Configure dependency updates**

Dependabot must:

- Check npm, pip/uv, GitHub Actions and Docker weekly.
- Group patch updates.
- Never auto-merge.

- [ ] **Step 5: Verify locally**

```bash
make lint
make typecheck
make test
make build
make api-check
bash scripts/test_compose_config.sh
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add .github scripts/check_architecture.py apps/control-api/tests/architecture Makefile
git commit -m "ci: enforce repository quality gates"
```

---

### Task 7: Record Foundational Architecture Decisions

**Files:**
- Create: `docs/adr/0001-modular-monolith.md`
- Create: `docs/adr/0002-temporal-workflows.md`
- Create: `docs/adr/0003-server-side-sessions.md`
- Create: `docs/adr/0004-project-isolation.md`
- Create: `docs/adr/0005-browser-dual-engine.md`
- Create: `docs/adr/0006-plugin-sdk-boundary.md`
- Create: `docs/adr/0007-immutable-published-assets.md`
- Create: `docs/adr/0008-pinned-open-source-dependencies.md`

- [ ] **Step 1: Use one ADR template**

Each ADR must include:

```markdown
# ADR-NNNN: Title

- Status: Accepted
- Date: 2026-06-25

## Context
## Decision
## Consequences
## Alternatives Considered
## Verification
```

- [ ] **Step 2: Write the decisions**

The decisions must match the architecture document exactly and must not introduce new product scope.

- [ ] **Step 3: Verify references**

```bash
rg -n "ADR-00|000[1-8]-" docs AGENTS.md README.md
```

Expected: all eight decisions are discoverable.

- [ ] **Step 4: Commit**

```bash
git add docs/adr
git commit -m "docs: record foundational architecture decisions"
```

---

### Task 8: Implement Identity Domain and Database Base

**Files:**
- Create: `apps/control-api/src/agenttest/shared/domain/clock.py`
- Create: `apps/control-api/src/agenttest/shared/domain/ids.py`
- Create: `apps/control-api/src/agenttest/shared/infrastructure/database.py`
- Create: `apps/control-api/src/agenttest/modules/identity/domain/entities.py`
- Create: `apps/control-api/src/agenttest/modules/identity/domain/value_objects.py`
- Create: `apps/control-api/src/agenttest/modules/identity/domain/repositories.py`
- Create: `apps/control-api/src/agenttest/modules/identity/domain/errors.py`
- Create: `apps/control-api/tests/unit/identity/test_user.py`

- [ ] **Step 1: Write failing User domain tests**

Tests must prove:

- Email is normalized to lowercase.
- Supported roles are `super_admin`, `developer`, `tester`, `reviewer`, `viewer`.
- A disabled user cannot be authenticated.
- The user can require a password change.
- Disabling an already disabled user is idempotent.

Example:

```python
def test_disabling_user_revokes_authentication() -> None:
    user = User.create(
        user_id=UserId.new(),
        email=Email("ADMIN@EXAMPLE.COM"),
        display_name="Admin",
        role=SystemRole.SUPER_ADMIN,
    )

    user.disable()

    assert user.status is UserStatus.DISABLED
    assert user.can_authenticate is False
```

- [ ] **Step 2: Run tests and verify they fail**

```bash
uv run pytest apps/control-api/tests/unit/identity/test_user.py -v
```

Expected: FAIL because identity domain classes do not exist.

- [ ] **Step 3: Implement identity domain**

Use immutable `Email`, typed `UserId`, explicit enums and a `User` entity. Domain code must not import Pydantic, SQLAlchemy or FastAPI.

- [ ] **Step 4: Implement database session factory**

Create an async SQLAlchemy Engine and `async_sessionmaker`, but do not connect at import time.

- [ ] **Step 5: Verify**

```bash
uv run pytest apps/control-api/tests/unit/identity/test_user.py -v
uv run pytest apps/control-api/tests/architecture -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/control-api/src/agenttest/shared apps/control-api/src/agenttest/modules/identity apps/control-api/tests/unit/identity
git commit -m "feat(identity): add user domain model"
```

---

### Task 9: Add Identity, Session, Project and Audit Migrations

**Files:**
- Create: `apps/control-api/alembic.ini`
- Create: `apps/control-api/migrations/env.py`
- Create: `apps/control-api/migrations/versions/0001_identity_projects_audit.py`
- Create: `apps/control-api/src/agenttest/modules/identity/infrastructure/persistence/models.py`
- Create: `apps/control-api/src/agenttest/modules/projects/infrastructure/persistence/models.py`
- Create: `apps/control-api/src/agenttest/modules/audit/infrastructure/persistence/models.py`
- Create: `apps/control-api/tests/integration/test_migrations.py`
- Create: `apps/control-api/tests/integration/test_database_constraints.py`

- [ ] **Step 1: Write failing migration tests**

Tests must:

- Upgrade an empty PostgreSQL database to `head`.
- Downgrade one revision and upgrade again.
- Verify unique normalized email.
- Verify one project member per `(project_id, user_id)`.
- Verify Session token hash uniqueness.
- Verify audit records are append-only at repository level.

- [ ] **Step 2: Run tests and verify they fail**

```bash
uv run pytest apps/control-api/tests/integration/test_migrations.py apps/control-api/tests/integration/test_database_constraints.py -v
```

Expected: FAIL because migrations do not exist.

- [ ] **Step 3: Create tables**

Migration `0001` must create:

```text
users
user_credentials
user_sessions
projects
project_members
audit.audit_logs
```

Required columns:

- UUID primary keys.
- `created_at`, `updated_at`.
- `created_by`, `updated_by` where relevant.
- User role and status check constraints.
- Session `token_hash`, `expires_at`, `revoked_at`.
- Project `archived_at`.
- Audit `actor_user_id`, `action`, `object_type`, `object_id`, `project_id`, `changes`, `source_ip`.

- [ ] **Step 4: Add indexes**

Required indexes:

- Unique `users.email_normalized`.
- Unique `user_sessions.token_hash`.
- `user_sessions(user_id, expires_at)`.
- Unique `project_members(project_id, user_id)`.
- `projects(created_at desc)`.
- `audit.audit_logs(project_id, created_at desc)`.

- [ ] **Step 5: Verify**

```bash
uv run alembic -c apps/control-api/alembic.ini upgrade head
uv run pytest apps/control-api/tests/integration/test_migrations.py apps/control-api/tests/integration/test_database_constraints.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/control-api/alembic.ini apps/control-api/migrations apps/control-api/src/agenttest/modules/*/infrastructure/persistence apps/control-api/tests/integration
git commit -m "feat(db): add identity and project schema"
```

---

### Task 10: Implement Session Authentication

**Files:**
- Create: `apps/control-api/src/agenttest/modules/identity/application/commands/login.py`
- Create: `apps/control-api/src/agenttest/modules/identity/application/commands/logout.py`
- Create: `apps/control-api/src/agenttest/modules/identity/application/queries/current_user.py`
- Create: `apps/control-api/src/agenttest/modules/identity/application/ports.py`
- Create: `apps/control-api/src/agenttest/modules/identity/infrastructure/passwords.py`
- Create: `apps/control-api/src/agenttest/modules/identity/infrastructure/persistence/repositories.py`
- Create: `apps/control-api/src/agenttest/modules/identity/api/router.py`
- Create: `apps/control-api/src/agenttest/modules/identity/api/schemas.py`
- Create: `apps/control-api/tests/unit/identity/test_login_handler.py`
- Create: `apps/control-api/tests/contract/test_auth_api.py`

- [ ] **Step 1: Write failing login handler tests**

Cover:

- Correct password creates Session.
- Wrong password returns the same public error as unknown email.
- Disabled user cannot log in.
- Expired and revoked Sessions are rejected.
- Logout revokes the current Session.
- Password verification uses Argon2id.

- [ ] **Step 2: Write failing API tests**

Endpoints:

```text
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

Assert:

- Login sets Secure, HttpOnly and SameSite Session Cookie.
- `/me` returns 401 without a valid Session.
- Logout clears the Cookie.
- Authentication errors use Problem Details.

- [ ] **Step 3: Implement authentication**

Session tokens:

- Generate 32 random bytes.
- Send only the raw token to the browser.
- Store SHA-256 token hash in PostgreSQL.
- Rotate Session on successful login.
- Enforce configured TTL.

- [ ] **Step 4: Add CSRF protection**

For cookie-authenticated mutating requests:

- Issue a separate readable CSRF token.
- Require matching `X-CSRF-Token`.
- Exempt login only.

- [ ] **Step 5: Verify**

```bash
uv run pytest apps/control-api/tests/unit/identity/test_login_handler.py apps/control-api/tests/contract/test_auth_api.py -v
uv run ruff check apps/control-api
uv run mypy apps/control-api/src
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/control-api/src/agenttest/modules/identity apps/control-api/tests
git commit -m "feat(identity): add server-side session authentication"
```

---

### Task 11: Add Super Administrator Bootstrap and User Management

**Files:**
- Create: `apps/admin-cli/pyproject.toml`
- Create: `apps/admin-cli/src/agenttest_admin/main.py`
- Create: `apps/control-api/src/agenttest/modules/identity/application/commands/create_user.py`
- Create: `apps/control-api/src/agenttest/modules/identity/application/commands/update_user.py`
- Create: `apps/control-api/src/agenttest/modules/identity/application/commands/reset_password.py`
- Create: `apps/control-api/src/agenttest/modules/identity/application/commands/set_user_status.py`
- Create: `apps/control-api/src/agenttest/modules/identity/application/queries/list_users.py`
- Modify: `apps/control-api/src/agenttest/modules/identity/api/router.py`
- Create: `apps/control-api/tests/unit/identity/test_user_management.py`
- Create: `apps/control-api/tests/contract/test_user_admin_api.py`

- [ ] **Step 1: Write failing policy tests**

Cover:

- Only `super_admin` can manage users.
- The final active super administrator cannot be disabled or deleted.
- A super administrator cannot disable itself.
- Resetting a password revokes all existing Sessions.
- Users with historical activity are disabled, not physically deleted.

- [ ] **Step 2: Implement bootstrap CLI**

Command:

```bash
uv run agenttest-admin create-super-admin --email admin@example.com --name Admin
```

Behavior:

- Read password from hidden interactive prompt or environment variable.
- Refuse duplicate email.
- Hash with Argon2id.
- Mark `must_change_password=true`.
- Never print the password.

- [ ] **Step 3: Implement admin endpoints**

```text
GET    /api/v1/system/users
POST   /api/v1/system/users
GET    /api/v1/system/users/{user_id}
PATCH  /api/v1/system/users/{user_id}
POST   /api/v1/system/users/{user_id}/reset-password
POST   /api/v1/system/users/{user_id}/disable
POST   /api/v1/system/users/{user_id}/enable
DELETE /api/v1/system/users/{user_id}
```

Use cursor pagination and never return password hashes or raw Session data.

- [ ] **Step 4: Verify**

```bash
uv run pytest apps/control-api/tests/unit/identity/test_user_management.py apps/control-api/tests/contract/test_user_admin_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/admin-cli apps/control-api/src/agenttest/modules/identity apps/control-api/tests
git commit -m "feat(identity): add super administrator user management"
```

---

### Task 12: Implement Projects, Membership and Authorization Policies

**Files:**
- Create: `apps/control-api/src/agenttest/modules/projects/domain/entities.py`
- Create: `apps/control-api/src/agenttest/modules/projects/domain/repositories.py`
- Create: `apps/control-api/src/agenttest/modules/projects/domain/policies.py`
- Create: `apps/control-api/src/agenttest/modules/projects/application/commands/create_project.py`
- Create: `apps/control-api/src/agenttest/modules/projects/application/commands/manage_members.py`
- Create: `apps/control-api/src/agenttest/modules/projects/application/queries/list_projects.py`
- Create: `apps/control-api/src/agenttest/modules/projects/infrastructure/persistence/repositories.py`
- Create: `apps/control-api/src/agenttest/modules/projects/api/router.py`
- Create: `apps/control-api/src/agenttest/modules/projects/api/schemas.py`
- Create: `apps/control-api/src/agenttest/modules/projects/public.py`
- Create: `apps/control-api/tests/unit/projects/test_project_policy.py`
- Create: `apps/control-api/tests/integration/projects/test_project_isolation.py`
- Create: `apps/control-api/tests/contract/test_projects_api.py`

- [ ] **Step 1: Write failing authorization tests**

Cover:

- Super administrator sees all projects.
- Normal users see only assigned projects.
- Removed members immediately lose access.
- Viewer cannot change membership.
- Project resource lookup requires both `project_id` and resource ID.
- Direct access to another project returns 404 to avoid existence disclosure.

- [ ] **Step 2: Implement project domain**

Project entity supports:

- Create.
- Rename.
- Archive.
- Add member.
- Change member role.
- Remove member.

Only super administrators manage project membership in M1.

- [ ] **Step 3: Implement project API**

```text
GET   /api/v1/projects
POST  /api/v1/projects
GET   /api/v1/projects/{project_id}
PATCH /api/v1/projects/{project_id}
POST  /api/v1/projects/{project_id}/archive
GET   /api/v1/projects/{project_id}/members
POST  /api/v1/projects/{project_id}/members
PATCH /api/v1/projects/{project_id}/members/{user_id}
DELETE /api/v1/projects/{project_id}/members/{user_id}
```

- [ ] **Step 4: Verify isolation with real PostgreSQL**

```bash
uv run pytest apps/control-api/tests/unit/projects apps/control-api/tests/integration/projects apps/control-api/tests/contract/test_projects_api.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/control-api/src/agenttest/modules/projects apps/control-api/tests
git commit -m "feat(projects): enforce project membership isolation"
```

---

### Task 13: Add Audit Logging

**Files:**
- Create: `apps/control-api/src/agenttest/modules/audit/application/ports.py`
- Create: `apps/control-api/src/agenttest/modules/audit/application/record.py`
- Create: `apps/control-api/src/agenttest/modules/audit/infrastructure/persistence/repositories.py`
- Create: `apps/control-api/src/agenttest/modules/audit/api/router.py`
- Create: `apps/control-api/src/agenttest/modules/audit/public.py`
- Create: `apps/control-api/tests/integration/audit/test_audit_logging.py`
- Create: `apps/control-api/tests/contract/test_audit_api.py`

- [ ] **Step 1: Write failing audit tests**

Verify audit entries for:

- Login success and failure.
- Logout.
- User create, edit, reset password, enable and disable.
- Project create, archive and member change.

Audit changes must:

- Store field names and safe before/after values.
- Redact passwords, tokens, cookies and credential values.
- Include actor, source IP, object and project when applicable.

- [ ] **Step 2: Implement audit port**

Application handlers call a shared `AuditRecorder` port in the same transaction when the audit entry is part of the business change.

- [ ] **Step 3: Implement audit API**

```text
GET /api/v1/system/audit
GET /api/v1/projects/{project_id}/audit
```

Only super administrators can query global audit. Project members can query project audit according to role.

- [ ] **Step 4: Verify**

```bash
uv run pytest apps/control-api/tests/integration/audit apps/control-api/tests/contract/test_audit_api.py -v
```

Expected: PASS and no secret values appear in captured records.

- [ ] **Step 5: Commit**

```bash
git add apps/control-api/src/agenttest/modules/audit apps/control-api/tests
git commit -m "feat(audit): record identity and project changes"
```

---

### Task 14: Build Login, User Management and Project UI

**Files:**
- Create: `apps/web/src/app/(auth)/login/page.tsx`
- Create: `apps/web/src/app/(platform)/layout.tsx`
- Create: `apps/web/src/app/(platform)/system/users/page.tsx`
- Create: `apps/web/src/app/(platform)/projects/[projectId]/overview/page.tsx`
- Create: `apps/web/src/features/auth/`
- Create: `apps/web/src/features/users/`
- Create: `apps/web/src/features/projects/`
- Create: `apps/web/src/lib/permissions/`
- Create: `apps/web/src/components/ui/dialog.tsx`
- Create: `apps/web/src/components/ui/input.tsx`
- Create: `apps/web/src/components/ui/table.tsx`
- Create: `apps/web/src/components/ui/toast.tsx`
- Create: `apps/web/src/features/auth/tests/login-form.test.tsx`
- Create: `apps/web/src/features/users/tests/user-management.test.tsx`
- Create: `apps/web/src/features/projects/tests/project-switcher.test.tsx`

- [ ] **Step 1: Write failing component tests**

Cover:

- Login validation and generic authentication error.
- User table loading, empty, error and populated states.
- Create user Dialog and password reset confirmation.
- Disable action displays impact and cannot target current super administrator.
- Project switcher only shows authorized projects.
- Ordinary users do not see System Administration navigation.

- [ ] **Step 2: Implement authentication client**

Requirements:

- Use generated API Client.
- Send credentials with requests.
- Read and attach CSRF token for mutations.
- Redirect unauthenticated users to `/login`.
- Preserve the intended return URL.

- [ ] **Step 3: Implement Linear/Vercel-style screens**

Follow design tokens and shared components:

- Compact login form.
- High-density user table.
- Status and role badges.
- Right-side detail Drawer for quick user inspection.
- Explicit loading, empty, error and permission states.
- Keyboard navigation and WCAG 2.2 AA.

- [ ] **Step 4: Run component verification**

```bash
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web test
pnpm --filter @warmy/web build
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/web packages/generated-api-client docs/api/openapi.json pnpm-lock.yaml
git commit -m "feat(web): add authentication and administration UI"
```

---

### Task 15: Add End-to-End Acceptance and Finish M1

**Files:**
- Create: `apps/web/playwright.config.ts`
- Create: `apps/web/playwright/auth.setup.ts`
- Create: `apps/web/playwright/login.spec.ts`
- Create: `apps/web/playwright/user-management.spec.ts`
- Create: `apps/web/playwright/project-isolation.spec.ts`
- Create: `apps/control-api/tests/security/test_session_security.py`
- Create: `docs/api/identity-and-projects.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`
- Modify: `README.md`

- [ ] **Step 1: Write E2E acceptance tests**

Scenarios:

1. Unauthenticated user is redirected to login.
2. Super administrator logs in and creates a developer.
3. Developer logs in but cannot access `/system/users`.
4. Super administrator creates Project A and Project B.
5. Developer assigned only to Project A cannot list or directly access Project B.
6. Disabling the developer invalidates the active Session.
7. Password reset requires password change and invalidates old Session.
8. Last active super administrator cannot be disabled.

- [ ] **Step 2: Write Session security tests**

Verify:

- Session token is not stored in plaintext.
- Cookie is HttpOnly and SameSite.
- Mutation without CSRF token is rejected.
- Login response does not reveal whether an account exists.
- Rate limit is applied to repeated login failure.

- [ ] **Step 3: Run the full M1 verification**

```bash
docker compose --env-file infra/compose/.env.example -f infra/compose/compose.yaml up -d
uv run alembic -c apps/control-api/alembic.ini upgrade head
make verify
make api-check
pnpm --filter @warmy/web exec playwright test
docker compose --env-file infra/compose/.env.example -f infra/compose/compose.yaml down
```

Expected: all checks PASS.

- [ ] **Step 4: Verify migration paths**

```bash
uv run pytest apps/control-api/tests/integration/test_migrations.py -v
```

Expected: empty database migration and downgrade/upgrade cycle PASS.

- [ ] **Step 5: Update documentation and progress**

Update:

- `docs/api/identity-and-projects.md` with endpoint behavior and examples.
- `README.md` with exact bootstrap and local run commands.
- `docs/开发进度与变更记录.md`: mark M0 and M1 complete.
- `docs/当前任务.md`: set no active task and identify M2 planning as next.

- [ ] **Step 6: Commit**

```bash
git add apps/web/playwright apps/control-api/tests/security docs README.md
git commit -m "test: verify platform foundation acceptance"
```

- [ ] **Step 7: Push after user-approved integration**

```bash
git status --short
git log --oneline --decorate -15
git push origin main
```

Expected: clean worktree and remote branch updated.

---

## Plan Completion Checklist

- [ ] M0 engineering baseline is runnable.
- [ ] M1 identity and project isolation acceptance criteria pass.
- [ ] No API route directly imports ORM models.
- [ ] All project resource queries include `project_id`.
- [ ] OpenAPI Client has no drift.
- [ ] Database migrations pass from empty and prior revision.
- [ ] Session, CSRF, rate-limit and audit tests pass.
- [ ] UI covers loading, empty, error and permission states.
- [ ] Current task and progress documents are updated.
