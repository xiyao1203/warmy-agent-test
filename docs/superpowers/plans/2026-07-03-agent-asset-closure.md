# Agent Asset Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the Agent asset lifecycle and connect it to plans, runs, artifacts, experiments, security scans, and release gates with real persisted APIs and a fully interactive frontend.

**Architecture:** Keep Agent and AgentVersion as the aggregate boundary. Add application commands for lifecycle mutations, a bootstrap-owned cross-module relationship reader, and project-scoped HTTP contracts. The frontend consumes generated APIs for mutations and a focused relationship summary for related modules.

**Tech Stack:** FastAPI, SQLAlchemy async, Pydantic, React/Next.js, TanStack Query, Vitest/Testing Library, pytest, OpenAPI generated client.

---

### Task 1: Persisted Agent lifecycle

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/agents/application/commands.py`
- Modify: `apps/control-api/src/agenttest/modules/agents/api/router.py`
- Modify: `apps/control-api/src/agenttest/modules/agents/infrastructure/persistence/repositories.py`
- Test: `apps/control-api/tests/contract/test_agents_api.py`
- Test: `apps/control-api/tests/unit/agents/test_agent_domain.py`

- [ ] Add failing tests for editing Agent metadata, first-publish current version, setting published current/baseline versions, rejecting drafts/cross-Agent versions, persistence after reload, and delete conflict/success.
- [ ] Run the targeted tests and confirm failures are caused by missing lifecycle behavior.
- [ ] Add `DeleteAgent`, `SetCurrentVersion`, and `SetBaselineVersion` commands/handlers; save pointer fields in `AgentRepository`; make first publish set current.
- [ ] Add project-scoped PATCH/DELETE routes with audit and conflict responses; fix diff/current/baseline paths.
- [ ] Run targeted unit and contract tests until green.

### Task 2: Cross-module relationship summary

**Files:**
- Create: `apps/control-api/src/agenttest/bootstrap/agent_relationships.py`
- Modify: `apps/control-api/src/agenttest/modules/agents/api/router.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Test: `apps/control-api/tests/integration/test_agent_relationships.py`

- [ ] Add a failing integration test with two projects proving the summary returns only same-project plan versions, runs, artifacts, experiments, security scans, and gates.
- [ ] Add an `AgentRelationshipsReader` API port and response schemas.
- [ ] Implement the bootstrap SQL reader using version IDs and project-scoped joins; expose `GET /relationships`.
- [ ] Use the same reader for delete blockers so referenced Agents return `409` with counts.
- [ ] Run integration and architecture tests until green.

### Task 3: Complete version configuration contract

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/agents/api/schemas.py`
- Modify: `apps/control-api/src/agenttest/modules/agents/domain/value_objects.py`
- Modify: `apps/control-api/src/agenttest/modules/agents/domain/invocation.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/run_source.py`
- Test: `apps/control-api/tests/unit/agents/test_invocation_contract.py`
- Test: `apps/control-api/tests/integration/test_run_execution_snapshot.py`

- [ ] Add failing round-trip and run-snapshot tests for model parameters, tools, credential binding IDs, knowledge version, adapter/plugin identity, and Web URL.
- [ ] Extend `AgentConfig` and API schema without exposing credential values.
- [ ] Preserve all fields in stored config, version diff, invocation snapshot, and Worker payload.
- [ ] Run targeted tests until green.

### Task 4: Frontend APIs and Agent management flow

**Files:**
- Modify: `apps/web/src/features/agents/api.ts`
- Modify: `apps/web/src/features/agents/agent-list.tsx`
- Modify: `apps/web/src/features/agents/agent-list-screen.tsx`
- Modify: `apps/web/src/features/agents/agent-detail-screen.tsx`
- Modify: `apps/web/src/features/agents/agent-detail.tsx`
- Create: `apps/web/src/features/agents/agent-relationships.tsx`
- Test: `apps/web/src/features/agents/tests/agent-list.test.tsx`
- Create: `apps/web/src/features/agents/tests/agent-detail.test.tsx`

- [ ] Add failing component tests for “管理”, row navigation, create-and-open, overview default, onboarding empty state, edit metadata, current/baseline wiring, diff, deletion blockers, and real relationship tabs.
- [ ] Implement generated-client lifecycle calls and relationship query.
- [ ] Change list semantics and navigate after creation.
- [ ] Split detail presentation into overview/version/relationship sections with localized errors and links.
- [ ] Run Agent component tests until green.

### Task 5: Complete version editor

**Files:**
- Modify: `apps/web/src/features/agents/agent-version-dialog.tsx`
- Modify: `apps/web/src/features/agents/version-detail-drawer.tsx`
- Modify: `apps/web/src/features/agents/version-diff-view.tsx`
- Test: `apps/web/src/features/agents/tests/agent-version-dialog.test.tsx`

- [ ] Add failing tests for full config editing, credential binding IDs, JSON validation, connection-test state, and accessible version selection labels.
- [ ] Add form sections for runtime metadata, tools/model params, credentials, knowledge, adapter/plugin, and Web endpoint.
- [ ] Wire diff and detail rendering for every supported field.
- [ ] Run targeted tests until green.

### Task 6: Contract generation and complete verification

**Files:**
- Modify: `docs/api/openapi.json`
- Modify: `packages/generated-api-client/src/client/**`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [ ] Export OpenAPI and regenerate the TypeScript client.
- [ ] Run backend format, Ruff, change-scope mypy, unit/contract/integration/architecture tests.
- [ ] Run frontend Prettier, ESLint, TypeScript, Agent tests, critical E2E, and production build.
- [ ] Run OpenAPI/client drift checks and `git diff --check`.
- [ ] Perform browser acceptance for create → configure → validate → publish → current/baseline → plan → run → related detail.
- [ ] Record exact evidence and remaining environment-only risks in both progress documents.
