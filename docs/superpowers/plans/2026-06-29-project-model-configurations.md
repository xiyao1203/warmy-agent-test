# Project Model Configurations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build secure project-scoped OpenAI-Compatible model configuration and use it for real Test Agent, text-judge, and vision-judge calls without Mock or placeholder fallback.

**Architecture:** A new `model_configs` DDD module owns configuration, defaults, encryption-at-write, permissions, and immutable invocation snapshots. Control API resolves the project default and starts a Temporal workflow; a database-free Model Runner decrypts the credential only inside an Activity and performs the HTTP call. The Web feature consumes generated OpenAPI types and follows the existing project list/dialog patterns.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy/Alembic, AES-GCM, Temporal Python SDK, HTTPX, Next.js/React, generated OpenAPI client, Vitest/Testing Library.

---

### Task 1: Record architecture and establish a clean baseline

**Files:**
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`
- Create: `docs/superpowers/specs/2026-06-29-project-model-configurations-design.md`
- Create: `docs/adr/0009-project-model-credentials-and-runtime.md`
- Modify: `docs/Agent测试平台产品需求文档-PRD.md`
- Modify: `docs/Agent测试平台技术架构与开发规范.md`

- [ ] Confirm the branch, worktree, recent commits, and existing known failures.
- [ ] Record the project model configuration requirement in the PRD data model and acceptance criteria.
- [ ] Record the Model Runner, encryption boundary, and no-fallback rule in the architecture document and ADR.
- [ ] Run document format checks and inspect the diff for conflicts or secrets.

### Task 2: Create security and domain behavior with TDD

**Files:**
- Create: `apps/control-api/src/agenttest/modules/model_configs/domain/entities.py`
- Create: `apps/control-api/src/agenttest/modules/model_configs/domain/value_objects.py`
- Create: `apps/control-api/src/agenttest/modules/model_configs/domain/repositories.py`
- Create: `apps/control-api/src/agenttest/modules/model_configs/domain/errors.py`
- Create: `apps/control-api/src/agenttest/modules/model_configs/application/ports.py`
- Create: `apps/control-api/src/agenttest/modules/model_configs/infrastructure/credentials.py`
- Test: `apps/control-api/tests/unit/model_configs/test_domain.py`
- Test: `apps/control-api/tests/unit/model_configs/test_credentials.py`

- [ ] Write failing tests for normalized OpenAI-Compatible URLs, mandatory text capability, write-only API-key hints, enabled/default invariants, and vision-purpose compatibility.
- [ ] Run `uv run pytest apps/control-api/tests/unit/model_configs/test_domain.py -q` and verify the missing module/behavior is the reason for failure.
- [ ] Implement `ProviderType`, `ModelPurpose`, `ModelConfiguration`, `ProjectModelDefault`, repository protocols, and explicit domain errors.
- [ ] Run the domain tests and verify they pass.
- [ ] Write failing AES-GCM tests proving round-trip, random nonce, tamper rejection, and no plaintext in ciphertext.
- [ ] Add the pinned encryption dependency, implement versioned AES-GCM credential envelopes, and run the tests green.

### Task 3: Add project-isolated persistence and migration

**Files:**
- Create: `apps/control-api/src/agenttest/modules/model_configs/infrastructure/persistence/models.py`
- Create: `apps/control-api/src/agenttest/modules/model_configs/infrastructure/persistence/repositories.py`
- Create: `apps/control-api/migrations/versions/0009_project_model_configurations.py`
- Modify: `apps/control-api/src/agenttest/shared/infrastructure/database.py`
- Test: `apps/control-api/tests/integration/test_model_config_repository.py`
- Test: `apps/control-api/tests/integration/test_database_constraints.py`
- Test: `apps/control-api/tests/integration/test_migrations.py`

- [ ] Write failing repository tests for project-filtered get/list, `(project_id, name)` uniqueness, three default purposes, composite project/model foreign key, and delete protection.
- [ ] Run the focused tests and verify the schema/repository absence causes failure.
- [ ] Implement the two ORM models, mappers, repository methods, and Alembic upgrade/downgrade.
- [ ] Run focused repository and migration tests green on SQLite-compatible tests and PostgreSQL integration when available.

### Task 4: Implement application use cases and secure API

**Files:**
- Create: `apps/control-api/src/agenttest/modules/model_configs/application/commands.py`
- Create: `apps/control-api/src/agenttest/modules/model_configs/application/queries.py`
- Create: `apps/control-api/src/agenttest/modules/model_configs/application/dto.py`
- Create: `apps/control-api/src/agenttest/modules/model_configs/api/schemas.py`
- Create: `apps/control-api/src/agenttest/modules/model_configs/api/router.py`
- Create: `apps/control-api/src/agenttest/modules/model_configs/public.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/settings.py`
- Test: `apps/control-api/tests/unit/model_configs/test_handlers.py`
- Test: `apps/control-api/tests/contract/test_model_configs_api.py`

- [ ] Write failing handler tests for membership/editor policy, create/update with retained key, enable/disable, default assignment, and deletion while referenced.
- [ ] Implement commands/queries through repository and project-access ports; never expose encrypted or plaintext keys in DTOs.
- [ ] Write failing API tests for authentication, CSRF, cross-project 404, RFC 7807 errors, masked key metadata, and all CRUD/default routes.
- [ ] Wire the router through explicit dependencies in `bootstrap/app.py`, then run focused tests green.

### Task 5: Build the real Model Runner protocol and Worker

**Files:**
- Create: `workers/model-runner/pyproject.toml`
- Create: `workers/model-runner/src/agenttest_model_runner/contracts.py`
- Create: `workers/model-runner/src/agenttest_model_runner/adapter.py`
- Create: `workers/model-runner/src/agenttest_model_runner/activities.py`
- Create: `workers/model-runner/src/agenttest_model_runner/workflow.py`
- Create: `workers/model-runner/src/agenttest_model_runner/main.py`
- Modify: `pyproject.toml`
- Test: `workers/model-runner/tests/test_adapter.py`
- Test: `workers/model-runner/tests/test_workflow.py`

- [ ] Write failing adapter tests against a local HTTP server for Authorization, text/vision request shape, structured response, usage/latency, 401, 429, 5xx, timeout, invalid JSON, and secret redaction.
- [ ] Implement the OpenAI-Compatible adapter using HTTPX; no SDK-specific global configuration and no fallback output.
- [ ] Write failing workflow replay and activity error-mapping tests.
- [ ] Implement deterministic workflow orchestration and short-lived Activity decryption with explicit retry policy and timeout.
- [ ] Run all Model Runner tests green and verify no database import or model API-key environment lookup exists.

### Task 6: Connect Control API to Temporal and expose connection testing

**Files:**
- Create: `apps/control-api/src/agenttest/modules/model_configs/infrastructure/temporal_invoker.py`
- Modify: `apps/control-api/src/agenttest/modules/model_configs/api/router.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/settings.py`
- Test: `apps/control-api/tests/unit/model_configs/test_temporal_invoker.py`
- Test: `apps/control-api/tests/contract/test_model_configs_api.py`

- [ ] Write failing tests proving the invocation snapshot contains only project/config metadata plus encrypted credential, uses a unique workflow ID, and maps Temporal/upstream errors without exposing secrets.
- [ ] Implement `TemporalModelInvoker` and `POST .../{id}/test-connection` using a minimal real request.
- [ ] Run the focused tests green; when Temporal is absent return an explicit 503 instead of a fake success.

### Task 7: Replace Test Agent Mock behavior with configured real calls

**Files:**
- Delete: `apps/control-api/src/agenttest/modules/test_agent/llm_adapters.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/application/model_planner.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/api/router.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Test: `apps/control-api/tests/unit/test_agent/test_model_planner.py`
- Test: `apps/control-api/tests/contract/test_agent_chat.py`

- [ ] Write failing tests for 409 without `test_agent_chat`, real invocation with configured default, schema validation, upstream error mapping, and preserved project isolation.
- [ ] Implement a structured-output prompt and strict Pydantic plan parser through the model invocation port.
- [ ] Inject the planner into the router, remove environment selection and all Mock/static plan code, then run focused tests green.

### Task 8: Add real text and vision judge entry points

**Files:**
- Create: `apps/control-api/src/agenttest/modules/scorers/application/model_judge.py`
- Modify: `apps/control-api/src/agenttest/modules/scorers/api/router.py`
- Modify: `apps/control-api/src/agenttest/modules/scorers/domain/entities.py`
- Test: `apps/control-api/tests/unit/scorers/test_model_judge.py`
- Test: `apps/control-api/tests/contract/test_scorer_model_judge.py`

- [ ] Write failing tests for purpose resolution, vision capability enforcement, strict score schema, model snapshot metadata, Token/latency recording, and no fallback score.
- [ ] Implement text and vision judge commands using the shared invocation port and immutable model metadata.
- [ ] Expose authenticated project-scoped judge test routes and run focused tests green.

### Task 9: Generate OpenAPI client and build the model configuration UI

**Files:**
- Modify: `docs/api/openapi.json`
- Modify: `packages/generated-api-client/src/client/**`
- Create: `apps/web/src/features/model-configs/api.ts`
- Create: `apps/web/src/features/model-configs/model-config-list.tsx`
- Create: `apps/web/src/features/model-configs/model-config-dialog.tsx`
- Create: `apps/web/src/features/model-configs/model-defaults.tsx`
- Create: `apps/web/src/features/model-configs/index.ts`
- Create: `apps/web/src/app/(platform)/projects/[projectId]/models/page.tsx`
- Modify: `apps/web/src/components/layout/app-shell.tsx`
- Test: `apps/web/src/features/model-configs/tests/model-configs.test.tsx`

- [ ] Export a fresh OpenAPI document and regenerate the client; verify generated types include no key/ciphertext response field.
- [ ] Write failing component tests for loading, empty, error, list, create/edit retained key, defaults, connection result, vision incompatibility, and delete protection.
- [ ] Implement the fully interactive feature using existing Button/Dialog/Input/Badge/Table patterns and semantic tokens.
- [ ] Add the project route and navigation link, then run focused tests, typecheck, and build green.

### Task 10: Improve Test Agent missing-model and upstream-error UX

**Files:**
- Modify: `apps/web/src/features/test-agent/api.ts`
- Modify: `apps/web/src/features/test-agent/chat-screen.tsx`
- Test: `apps/web/src/features/test-agent/tests/chat-screen.test.tsx`

- [ ] Write failing tests for a persistent “configure model” action on 409 and a non-message inline error for upstream failures.
- [ ] Parse API Problem Details, add the configuration link, and preserve user input for retry.
- [ ] Run focused tests and keyboard/accessibility checks green.

### Task 11: Verify architecture, security, migrations, and user flow

**Files:**
- Modify: `apps/control-api/tests/architecture/test_module_boundaries.py`
- Modify: `docs/开发进度与变更记录.md`
- Modify: `docs/当前任务.md`

- [ ] Add an architecture test that rejects `MockLLMAdapter`, placeholder model returns, supplier API-key environment lookup, Control API supplier SDK calls, and Worker database imports.
- [ ] Run backend format/lint/mypy/unit/integration/contract/architecture tests.
- [ ] Run empty and previous-version migration verification, recording unavailable PostgreSQL checks explicitly.
- [ ] Run Model Runner format/lint/mypy/unit/replay tests.
- [ ] Run Web format/lint/typecheck/component tests/critical E2E/build and inspect desktop/narrow layouts in the existing product shell.
- [ ] Scan tracked changes for secrets and inspect the final diff for unrelated edits.
- [ ] Move the task to completed only if required evidence passes; otherwise record exact failures as `待验证` or `阻塞`.
