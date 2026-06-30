# Super Test Agent Platform Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the fixed test-plan chat demo with a persistent, streaming super test agent that delegates to typed child agents and operates the platform's real project-scoped assets from target agents through release gates.

**Architecture:** The `test_agent` module owns conversation, task, event, confirmation, and provenance orchestration facts. A capability registry delegates only to public application ports for existing modules; long-running orchestration and model streaming use Temporal workers and durable callbacks. The professional console remains the source of truth, while domain changes are reflected back into conversations through persisted artifact links and events.

**Tech Stack:** FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Temporal Python SDK, httpx streaming, Pydantic, Next.js, React, TypeScript, SSE, pytest, Vitest.

---

### Task 1: Stable model-configuration conflict behavior

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/model_configs/domain/errors.py`
- Modify: `apps/control-api/src/agenttest/modules/model_configs/domain/repositories.py`
- Modify: `apps/control-api/src/agenttest/modules/model_configs/infrastructure/persistence/repositories.py`
- Modify: `apps/control-api/src/agenttest/modules/model_configs/api/router.py`
- Modify: `apps/control-api/tests/contract/test_model_configs_api.py`

- [x] **Step 1: Write a failing contract test** that creates two configurations named `xiaomi` in one project and asserts the second response is RFC 7807 status 409 with `detail == "Model configuration name already exists"` while another project may use the same name.
- [x] **Step 2: Run** `uv run pytest apps/control-api/tests/contract/test_model_configs_api.py -q` and verify the duplicate case currently returns the wrong 400 status.
- [x] **Step 3: Add and map a domain error**:

```python
class ModelConfigNameConflictError(Exception):
    pass
```

Catch PostgreSQL/SQLite `IntegrityError` only around repository insertion, inspect the named project/name constraint, raise `ModelConfigNameConflictError`, and map it to status 409 without returning database text.
- [x] **Step 4: Re-run the contract tests** and verify project scoping plus secret redaction.

### Task 2: Expand the durable orchestration schema

**Files:**
- Create: `apps/control-api/migrations/versions/0012_super_test_agent_orchestration.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/infrastructure/models.py`
- Create: `apps/control-api/tests/integration/test_super_agent_migration.py`

- [ ] **Step 1: Write a failing migration integration test** asserting upgrade creates the following project-scoped tables and constraints:

```text
test_agent_tasks(project_id, id, session_id, parent_task_id, child_agent, capability,
                 status, risk_level, idempotency_key, input, output, error, timestamps)
test_agent_events(project_id, session_id, sequence, event_type, payload, created_at)
test_agent_confirmations(project_id, id, task_id, status, preview, decided_by, decided_at)
test_agent_artifact_links(project_id, id, session_id, task_id, artifact_type,
                          artifact_id, relation, created_at)
target_agent_chat_sessions(project_id, id, agent_version_id, environment_template_id,
                           status, created_by, timestamps)
target_agent_chat_turns(project_id, id, session_id, sequence, input, output, trace,
                        scores, duration_ms, token_usage, error, created_at)
```

Require unique event sequence per session, unique task idempotency key per project, unique artifact relation per task, composite project foreign keys, and indexes for session/event and artifact reverse lookup.
- [ ] **Step 2: Run the migration test** and verify it fails because revision `0012` is absent.
- [ ] **Step 3: Implement an Expand-only Alembic migration and matching SQLAlchemy models.** Add `title`, `archived_at`, and `protocol_version` to `test_agent_sessions`; retain `plan_draft` for read-only legacy compatibility.
- [ ] **Step 4: Verify empty-database upgrade, 0011-to-0012 upgrade, downgrade, constraints, and indexes** with the migration integration test and offline PostgreSQL SQL generation.

### Task 3: Conversation, task, event, confirmation, and provenance domain

**Files:**
- Replace: `apps/control-api/src/agenttest/modules/test_agent/domain/entities.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/application/ports.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/domain/capabilities.py`
- Replace: `apps/control-api/src/agenttest/modules/test_agent/infrastructure/repositories.py`
- Modify: `apps/control-api/tests/unit/test_agent/test_chat_domain.py`
- Modify: `apps/control-api/tests/unit/test_agent/test_session_repository.py`
- Create: `apps/control-api/tests/unit/test_agent/test_orchestration_repository.py`

- [ ] **Step 1: Write failing domain tests** for title creation, ordered messages, task dependency transitions, confirmation decisions, monotonic events, artifact links, archive behavior, idempotency, and cross-project rejection.
- [ ] **Step 2: Run the focused tests** and verify missing task/event types fail.
- [ ] **Step 3: Implement explicit types**:

```python
class TaskStatus(StrEnum):
    PENDING = "pending"
    WAITING_CONFIRMATION = "waiting_confirmation"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RiskLevel(StrEnum):
    READ = "read"
    DRAFT_WRITE = "draft_write"
    HIGH_IMPACT = "high_impact"
```

Add `AgentTask`, `AgentEvent`, `AgentConfirmation`, `ArtifactLink`, repositories with mandatory `ProjectId`, and atomic `append_event()` sequence allocation.
- [ ] **Step 4: Re-run domain/repository tests** against SQLite and PostgreSQL integration fixtures.

### Task 4: True conversational model protocol and streaming Model Runner

**Files:**
- Replace: `apps/control-api/src/agenttest/modules/test_agent/application/model_planner.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/application/conversation.py`
- Modify: `workers/model-runner/src/agenttest_model_runner/contracts.py`
- Modify: `workers/model-runner/src/agenttest_model_runner/adapter.py`
- Modify: `workers/model-runner/src/agenttest_model_runner/activities.py`
- Modify: `workers/model-runner/src/agenttest_model_runner/workflow.py`
- Modify: `workers/model-runner/tests/test_adapter.py`
- Create: `workers/model-runner/tests/test_streaming_conversation.py`
- Replace: `apps/control-api/tests/unit/test_agent/test_model_planner.py`

- [ ] **Step 1: Write failing tests** proving `你好` yields provider text instead of a fabricated plan, prior messages are sent as context, structured action intents are separately validated, and provider chunks preserve order.
- [ ] **Step 2: Run Model Runner and conversation tests** and verify the current JSON-only planner fails them.
- [ ] **Step 3: Introduce a versioned response contract**:

```python
class ConversationTurn(BaseModel):
    content: str
    actions: list[ActionIntent] = []

class ActionIntent(BaseModel):
    capability: str
    arguments: dict[str, object]
    rationale: str
```

The system prompt permits normal conversation and emits tool intents only when useful. Provider streaming uses `httpx.AsyncClient.stream()`, parses OpenAI-compatible deltas, and sends durable chunk callbacks without logging prompts, credentials, or raw authorization headers.
- [ ] **Step 4: Re-run tests** for normal text, reasoning-content providers, JSON tool intents, malformed chunks, timeout, cancellation, and credential redaction.

### Task 5: Session history, durable SSE, and reconnectable chat API

**Files:**
- Replace: `apps/control-api/src/agenttest/modules/test_agent/api/router.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/api/schemas.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/api/stream.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Create: `apps/control-api/tests/contract/test_super_agent_chat_api.py`
- Create: `apps/control-api/tests/contract/test_super_agent_stream_api.py`

- [ ] **Step 1: Write failing API tests** for list/create/get/archive sessions, send message, resume by URL ID, project isolation, cursor pagination, CSRF, and SSE reconnect with `Last-Event-ID`.
- [ ] **Step 2: Run tests** and verify list/history/stream routes are absent.
- [ ] **Step 3: Implement these endpoints**:

```text
GET    /projects/{project_id}/test-agent/sessions
POST   /projects/{project_id}/test-agent/sessions
GET    /projects/{project_id}/test-agent/sessions/{session_id}
DELETE /projects/{project_id}/test-agent/sessions/{session_id}
POST   /projects/{project_id}/test-agent/sessions/{session_id}/messages
GET    /projects/{project_id}/test-agent/sessions/{session_id}/events
```

The message command first persists the user message and `message.started`, invokes the real model runtime, persists deltas/actions/completion, then returns 202 with session/task identifiers. SSE reads only persisted events and emits heartbeats without inventing domain progress.
- [ ] **Step 4: Re-run contract tests** including application restart/repository reconstruction and SSE reconnection.

### Task 6: Capability registry, child-agent policy, and confirmations

**Files:**
- Create: `apps/control-api/src/agenttest/modules/test_agent/application/registry.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/application/orchestrator.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/application/policy.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/api/confirmations.py`
- Create: `apps/control-api/tests/unit/test_agent/test_capability_registry.py`
- Create: `apps/control-api/tests/unit/test_agent/test_orchestrator.py`
- Create: `apps/control-api/tests/contract/test_super_agent_confirmations_api.py`

- [ ] **Step 1: Write failing tests** for child-agent allowlists, unknown capability rejection, actor/project propagation, read auto-execution, draft batch confirmation, high-impact individual confirmation, prompt-injection resistance, and idempotent replay.
- [ ] **Step 2: Run tests** and verify registry/orchestrator types are absent.
- [ ] **Step 3: Implement the capability contract**:

```python
@dataclass(frozen=True, slots=True)
class Capability:
    name: str
    version: str
    child_agent: str
    risk: RiskLevel
    input_model: type[BaseModel]
    execute: CapabilityExecutor
```

Register immutable names, validate input before execution, persist previews, require a signed-in actor to decide confirmations, and re-check authorization at execution time.
- [ ] **Step 4: Re-run tests** and add architecture assertions preventing capability adapters from importing infrastructure persistence modules.

### Task 7: Core child agents and real asset chain

**Files:**
- Create: `apps/control-api/src/agenttest/modules/test_agent/adapters/agents.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/adapters/environments.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/adapters/datasets.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/adapters/test_plans.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/adapters/runs.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/adapters/scorers.py`
- Modify: corresponding module `public.py` files to expose application ports rather than repositories
- Create: `apps/control-api/tests/integration/test_super_agent_core_asset_chain.py`

- [ ] **Step 1: Write a failing integration test** that asks the orchestrator to select an AgentVersion/environment, create a DatasetVersion with TestCases, create and publish a TestPlanVersion, start a Run, and link every real ID to the originating session/task.
- [ ] **Step 2: Run the test** and verify no capability adapters exist.
- [ ] **Step 3: Implement adapters using only public handlers.** Credential capabilities return IDs plus masked hints; they never return ciphertext/plaintext. Draft creation is confirmed in one batch; publish and run are separate high-impact confirmations. Emit `asset.created`, `asset.updated`, and `run.progress` events with links.
- [ ] **Step 4: Re-run the chain test** and independently query professional-console repositories to prove the assets are the same records, not chat copies.

### Task 8: Experiment, security, review, and release-gate child agents

**Files:**
- Add public application facades under `apps/control-api/src/agenttest/modules/{experiments,security,reviews,gates}/public.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/adapters/experiments.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/adapters/security.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/adapters/reviews.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/adapters/gates.py`
- Create: `apps/control-api/tests/integration/test_super_agent_quality_asset_chain.py`

- [ ] **Step 1: Write a failing integration test** that creates a baseline/candidate experiment from real Runs, starts a real configured security scan, creates review tasks for low-confidence cases, evaluates a real release gate, and links all assets to the session.
- [ ] **Step 2: Run the test** and verify public application facades/adapters are absent.
- [ ] **Step 3: Extract existing API-router business operations into public application facades** with actor/project checks and audit writing, then register typed capabilities. Review decisions, security execution, and gate policy changes always require individual confirmation; the Agent may recommend but cannot impersonate a human decision.
- [ ] **Step 4: Re-run integration tests** with unavailable Promptfoo/runtime cases proving explicit failure and no placeholder findings.

### Task 9: Temporal super-agent workflow

**Files:**
- Create: `workers/api-runner/src/agenttest_api_runner/super_agent_contracts.py`
- Create: `workers/api-runner/src/agenttest_api_runner/super_agent_workflow.py`
- Create: `workers/api-runner/src/agenttest_api_runner/super_agent_activities.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/main.py`
- Create: `workers/api-runner/tests/test_super_agent_workflow.py`
- Create: `workers/api-runner/tests/test_super_agent_replay.py`

- [ ] **Step 1: Write failing workflow tests** for dependency ordering, parallel independent reads, confirmation signals, cancellation, activity retry classification, idempotency, and replay.
- [ ] **Step 2: Run tests** and verify workflow registration is absent.
- [ ] **Step 3: Implement deterministic orchestration.** The workflow holds only validated snapshots and task state; activities call protected Control API capability/callback endpoints. Confirmation arrives as a Temporal signal, and workflow IDs use `super-agent:{project_id}:{session_id}:{root_task_id}`.
- [ ] **Step 4: Register the workflow/activities and run workflow plus replay tests.**

### Task 10: Direct target-Agent conversation testing

**Files:**
- Create: `apps/control-api/src/agenttest/modules/test_agent/application/target_chat.py`
- Create: `apps/control-api/src/agenttest/modules/test_agent/api/target_chat.py`
- Create: `workers/api-runner/src/agenttest_api_runner/target_chat_activity.py`
- Create: `apps/control-api/tests/contract/test_target_agent_chat_api.py`
- Create: `workers/api-runner/tests/test_target_chat_activity.py`

- [ ] **Step 1: Write failing tests** for selecting published AgentVersion/environment/account references, multi-turn sync/SSE/async protocols, persisted output/trace/timing/token usage, scoring, project isolation, and conversion to a real TestCase.
- [ ] **Step 2: Run tests** and verify target-chat routes/activity are absent.
- [ ] **Step 3: Implement target chat through the existing Generic HTTP Agent Adapter.** Persist every completed/failed turn, redact headers and traces, invoke configured real scorers, and use Dataset public handlers for “convert to regression”.
- [ ] **Step 4: Re-run tests** against the repository fake HTTP target for protocol correctness and against a user-supplied real Agent for final E2E.

### Task 11: Three-column streaming workspace and target-chat UI

**Files:**
- Replace: `apps/web/src/features/test-agent/api.ts`
- Replace: `apps/web/src/features/test-agent/chat-screen.tsx`
- Create: `apps/web/src/features/test-agent/session-list.tsx`
- Create: `apps/web/src/features/test-agent/task-timeline.tsx`
- Create: `apps/web/src/features/test-agent/context-panel.tsx`
- Create: `apps/web/src/features/test-agent/confirmation-card.tsx`
- Create: `apps/web/src/features/test-agent/artifact-card.tsx`
- Create: `apps/web/src/features/test-agent/target-chat-screen.tsx`
- Modify: Test Agent route files under `apps/web/src/app/(platform)/projects/[projectId]/`
- Replace: `apps/web/src/features/test-agent/tests/chat-screen.test.tsx`
- Create: `apps/web/src/features/test-agent/tests/session-history.test.tsx`
- Create: `apps/web/src/features/test-agent/tests/streaming-workspace.test.tsx`
- Create: `apps/web/src/features/test-agent/tests/target-chat.test.tsx`

- [ ] **Step 1: Write failing component tests** for session history/resume, URL session IDs, incremental deltas, reconnect, child-agent progress, confirmation previews, asset links, responsive panels, errors, and target-chat trace/score display.
- [ ] **Step 2: Run focused Vitest** and verify the current in-memory screen fails persistence/stream requirements.
- [ ] **Step 3: Implement the three-column workspace using existing design tokens/components.** Use one `EventSource` per active session, reduce events by sequence, store no business truth in local storage, provide keyboard/accessibility states, and link artifacts to their professional-console routes.
- [ ] **Step 4: Run focused tests, ESLint, TypeScript, production build, and browser verification at desktop plus narrow viewport.**

### Task 12: Contracts, truthfulness gates, documentation, and full E2E

**Files:**
- Modify: `docs/api/openapi.json`
- Regenerate: `packages/generated-api-client/src/client/`
- Modify: `scripts/check_production_truthfulness.py`
- Modify: `apps/control-api/tests/architecture/test_production_truthfulness.py`
- Modify: `README.md`
- Modify: `docs/Agent测试平台产品需求文档-PRD.md`
- Modify: `docs/Agent测试平台技术架构与开发规范.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

- [ ] **Step 1: Extend truthfulness tests** to reject fixed assistant templates, unconditional plan generation, process-memory conversation/event stores, unlinked `plan_draft` execution, fake child-agent success, and plaintext credential exposure.
- [ ] **Step 2: Generate OpenAPI/client and run drift checks.** Document SSE event types, confirmation behavior, capability versioning, asset provenance, startup commands, and operational recovery.
- [ ] **Step 3: Run complete verification:** backend format/Ruff/mypy/unit/contract/integration/architecture tests; all migrations from empty and 0011; API Runner and Model Runner tests/replay; Web format/lint/typecheck/Vitest/build; OpenAPI drift; production truthfulness; `git diff --check` and secret scan.
- [ ] **Step 4: Run real local E2E** with Temporal, API Runner, Model Runner, PostgreSQL, a newly rotated provider key, and a user-supplied target Agent. Verify greeting, stream, refresh/history, core asset chain, execution/result, experiment, security, review, gate, target chat, and regression conversion without Mock or placeholders.
- [ ] **Step 5: Record exact commands/results and remaining environment limitations** in the progress ledger; mark complete only if every required acceptance criterion has evidence.
