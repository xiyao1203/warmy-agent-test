# Conversational Agent Test Mission Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-grade conversational test mission that recognizes a target Agent test request, asks only for missing required data, performs read-only discovery, obtains one execution confirmation, automatically creates or reuses platform assets, runs the full API/browser/security/evaluation/review/gate chain, and persists every result in existing platform modules.

**Architecture:** Add a project-scoped `test_missions` aggregate and immutable revisions beneath the existing SuperAgent. The model extracts candidate facts, deterministic application services resolve assets and validate completeness, and a Temporal `TestMissionWorkflow` performs idempotent provisioning and delegates case execution to the existing `RunWorkflow`. Existing Agent, dataset, scorer, run, artifact, review, experiment, report and gate modules remain the source of truth.

**Tech Stack:** Python 3.13, FastAPI, Pydantic, SQLAlchemy 2, Alembic, PostgreSQL, Temporal Python SDK, PydanticAI, React 19, Next.js, TypeScript, TanStack Query, Vitest, Testing Library and Playwright.

## Global Constraints

- All mission data and repository operations are project-scoped; cross-project asset references fail closed.
- A model may propose facts and cases but may not start a Run, bypass confirmation, expand the action allowlist or change a confirmed revision.
- Passwords, tokens, cookies and plaintext browser auth state never enter chat messages, mission snapshots, logs, Trace or Temporal history.
- Ordinary execution uses one immutable preview confirmation; delete, payment, publish, permission and external-send actions retain separate high-impact confirmation.
- API execution is the preferred bulk channel when available; browser execution covers critical paths; security, evaluation, evidence, review and gate stages are part of the same mission.
- Workers do not connect to the business database and mutate platform state only through authenticated internal Control API endpoints.
- All new behavior is developed red-green-refactor; generated client output is regenerated, not hand-edited.
- The real-target gate cannot be declared passed without a successful read-only Run against an accessible target account with sufficient quota.

---

### Task 1: Mission Domain, Completeness and Immutable Revision

**Files:**
- Create: `apps/control-api/src/agenttest/modules/test_missions/__init__.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/public.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/domain/__init__.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/domain/entities.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/domain/value_objects.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/domain/completeness.py`
- Test: `apps/control-api/tests/unit/test_missions/test_domain.py`
- Test: `apps/control-api/tests/unit/test_missions/test_completeness.py`

**Interfaces:**
- Produces: `TestMission`, `MissionFact`, `MissionRevision`, `MissionStatus`, `FactSource`, `MissionCompleteness`, `compile_revision()`.
- Consumes: UUID and timezone-aware datetime only; domain code imports no framework or infrastructure package.

- [ ] **Step 1: Write failing domain state tests**

```python
def test_mission_requires_target_access_goal_and_safety_scope():
    mission = TestMission.create(project_id=PROJECT_ID, session_id=SESSION_ID, created_by=USER_ID)
    result = evaluate_completeness(mission.facts)
    assert result.missing == ("target", "access", "test_goal", "safety_scope")

def test_confirmation_freezes_hash_and_rejects_mutation():
    mission = complete_mission()
    revision = mission.confirm(confirmed_by=USER_ID)
    assert revision.content_hash == canonical_snapshot_hash(revision.snapshot)
    with pytest.raises(ConfirmedMissionMutationError):
        mission.merge_fact(MissionFact.user("test_goal", "changed"))
```

- [ ] **Step 2: Run tests and verify RED**

Run: `uv run pytest apps/control-api/tests/unit/test_missions/test_domain.py apps/control-api/tests/unit/test_missions/test_completeness.py -q`

Expected: collection fails because `agenttest.modules.test_missions` does not exist.

- [ ] **Step 3: Implement explicit domain types and transitions**

```python
class MissionStatus(StrEnum):
    COLLECTING = "collecting"
    NEEDS_INPUT = "needs_input"
    DISCOVERING = "discovering"
    READY_FOR_CONFIRMATION = "ready_for_confirmation"
    CONFIRMED = "confirmed"
    PROVISIONING = "provisioning"
    RUNNING = "running"
    NEEDS_ATTENTION = "needs_attention"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass(frozen=True, slots=True)
class MissionFact:
    key: str
    value: object
    source: FactSource
    confidence: float
    verified: bool
    sensitive: bool = False
```

Use canonical JSON with sorted keys and compact separators for `content_hash`. The snapshot contains secret-free references, inferred-case provenance, execution channels, budget, action allowlist and asset decisions.

- [ ] **Step 4: Run domain tests and static checks**

Run: `uv run pytest apps/control-api/tests/unit/test_missions -q && uv run ruff check apps/control-api/src/agenttest/modules/test_missions apps/control-api/tests/unit/test_missions && uv run mypy apps/control-api/src/agenttest/modules/test_missions`

Expected: all pass.

- [ ] **Step 5: Commit the domain slice**

```bash
git add apps/control-api/src/agenttest/modules/test_missions apps/control-api/tests/unit/test_missions
git commit -m "feat: model conversational test missions"
```

### Task 2: PostgreSQL Schema, Repository and Migration Safety

**Files:**
- Create: `apps/control-api/migrations/versions/0020_test_missions.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/application/ports.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/infrastructure/__init__.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/infrastructure/models.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/infrastructure/repositories.py`
- Modify: `apps/control-api/src/agenttest/shared/infrastructure/database.py`
- Test: `apps/control-api/tests/unit/test_missions/test_repository.py`
- Modify: `apps/control-api/tests/integration/test_migrations.py`
- Modify: `apps/control-api/tests/integration/test_database_constraints.py`

**Interfaces:**
- Produces: `MissionRepository.get(project_id, mission_id)`, `get_for_session(project_id, session_id)`, `save(mission, expected_lock_version)`, `append_event(...)`, `list_events(..., after)` and `link_asset(...)`.
- Consumes: domain entities from Task 1 and existing SQLAlchemy session factory/UoW conventions.

- [ ] **Step 1: Write failing repository and migration tests**

```python
async def test_repository_never_returns_a_cross_project_mission(repository):
    mission = await repository.get(OTHER_PROJECT_ID, MISSION_ID)
    assert mission is None

def test_0019_upgrades_to_0020_with_mission_constraints(alembic_connection):
    upgrade_to("0019")
    upgrade_to("0020")
    assert unique_columns("test_mission_facts", "uq_mission_facts_project_mission_key") == {
        "project_id", "mission_id", "field_key"
    }
```

Also assert project/session composite foreign keys, revision immutability constraints, asset reverse index, event sequence uniqueness and allowed status/source checks.

- [ ] **Step 2: Run migration/repository tests and verify RED**

Run: `uv run pytest apps/control-api/tests/unit/test_missions/test_repository.py apps/control-api/tests/integration/test_migrations.py apps/control-api/tests/integration/test_database_constraints.py -q`

Expected: failures for missing migration, tables and repository.

- [ ] **Step 3: Implement migration, ORM models and project-scoped repository**

Create `test_missions`, `test_mission_facts`, `test_mission_revisions`, `test_mission_assets` and `test_mission_events`. Use composite project foreign keys, explicit check constraints and indexes described in the design. Repository updates use `WHERE project_id = :project_id AND id = :id AND lock_version = :expected` and raise `MissionConcurrentUpdateError` when zero rows update.

- [ ] **Step 4: Verify empty and previous-revision upgrades**

Run: `uv run pytest apps/control-api/tests/unit/test_missions/test_repository.py apps/control-api/tests/integration/test_migrations.py apps/control-api/tests/integration/test_database_constraints.py -q`

Expected: all pass against SQLite-compatible tests and configured PostgreSQL tests.

- [ ] **Step 5: Commit persistence**

```bash
git add apps/control-api/migrations/versions/0020_test_missions.py apps/control-api/src/agenttest/modules/test_missions apps/control-api/tests/unit/test_missions apps/control-api/tests/integration
git commit -m "feat: persist project-scoped test missions"
```

### Task 3: Structured Intake, Asset Resolution and Read-Only Discovery

**Files:**
- Create: `apps/control-api/src/agenttest/modules/test_missions/application/intake.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/application/resolution.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/application/discovery.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/application/preflight.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/infrastructure/model_intake.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/infrastructure/platform_resolver.py`
- Test: `apps/control-api/tests/unit/test_missions/test_intake.py`
- Test: `apps/control-api/tests/unit/test_missions/test_resolution.py`
- Test: `apps/control-api/tests/unit/test_missions/test_preflight.py`
- Test: `apps/control-api/tests/contract/test_mission_discovery_api.py`

**Interfaces:**
- Produces: `MissionIntake.extract(history, current_facts) -> FactProposal`, `PlatformAssetResolver.resolve(project_id, facts) -> ResolutionResult`, `MissionDiscovery.discover(...) -> DiscoveryResult`, `MissionPreflight.evaluate(...) -> MissionPreview`.
- Consumes: existing model resolver/invoker, Agent queries, browser profile public reader, dataset/scorer/environment/gate public readers, plugin registry and URL policy.

- [ ] **Step 1: Write failing intake and preflight tests**

```python
async def test_intake_keeps_user_fact_over_lower_confidence_inference():
    result = await intake.extract([("user", "只读测试 https://target.test")], existing)
    assert result.facts["safety_scope"].source is FactSource.USER_PROVIDED

async def test_preflight_asks_only_for_invalid_login_when_other_facts_resolve():
    preview = await preflight.evaluate(complete_except_expired_profile())
    assert preview.missing == (MissingInput("access", "浏览器登录态已失效"),)
```

Add URL tests for HTTP(S)-only, redirect validation, loopback/private/link-local/metadata-IP rejection, Unicode host normalization and allowed explicit local Fake Target in test settings.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `uv run pytest apps/control-api/tests/unit/test_missions/test_intake.py apps/control-api/tests/unit/test_missions/test_resolution.py apps/control-api/tests/unit/test_missions/test_preflight.py apps/control-api/tests/contract/test_mission_discovery_api.py -q`

Expected: missing application services.

- [ ] **Step 3: Implement model-bounded extraction and deterministic merge**

Use a strict Pydantic schema:

```python
class FactProposal(BaseModel):
    target_url: AnyHttpUrl | None = None
    agent_version_id: UUID | None = None
    browser_profile_id: UUID | None = None
    test_goal: str | None = Field(default=None, max_length=4000)
    safety_scope: Literal["read_only", "draft_write"] | None = None
    scenario_hints: list[str] = Field(default_factory=list, max_length=20)
```

Ignore unknown fields; never accept credentials, action-allowlist expansion or project IDs from model output. Merge precedence is verified user fact > verified platform resolution > target discovery > system inference.

- [ ] **Step 4: Implement resolution, discovery and preflight**

Resolve same-project assets first. Discovery invokes existing endpoint analysis and Browser Profile verification through ports, uses read-only action policy and returns evidence with source/confidence. Preflight emits a preview only when target, access, goal and safety facts are verified; inferred cases and scorers remain visibly marked.

- [ ] **Step 5: Verify focused tests and commit**

Run: `uv run pytest apps/control-api/tests/unit/test_missions apps/control-api/tests/contract/test_mission_discovery_api.py -q`

```bash
git add apps/control-api/src/agenttest/modules/test_missions apps/control-api/tests/unit/test_missions apps/control-api/tests/contract/test_mission_discovery_api.py
git commit -m "feat: resolve conversational mission requirements"
```

### Task 4: Mission API, One-Time Confirmation and Audit

**Files:**
- Create: `apps/control-api/src/agenttest/modules/test_missions/application/commands.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/application/queries.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/api/__init__.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/api/schemas.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/api/router.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Test: `apps/control-api/tests/contract/test_test_missions_api.py`
- Test: `apps/control-api/tests/unit/test_missions/test_commands.py`

**Interfaces:**
- Produces REST endpoints under `/api/v1/projects/{project_id}/test-missions`: create/update, discover, preview, confirm-start, status, resume, cancel and event stream.
- Produces internal endpoints under `/internal/test-missions/{mission_id}/stages/{stage}` authenticated by `X-Internal-Token` and scoped by project/revision/hash.
- Consumes identity writer policy, project membership policy, audit recorder, repository and Task 3 services.

- [ ] **Step 1: Write failing authorization, confirmation and idempotency contracts**

```python
def test_confirm_rejects_stale_preview_hash(client, mission):
    response = client.post(confirm_url, json={"revision_hash": "stale", "idempotency_key": "k"})
    assert response.status_code == 409

def test_internal_stage_rejects_wrong_project_and_token(client):
    assert client.post(stage_url, headers={"X-Internal-Token": "bad"}).status_code == 401
```

Cover reader/writer roles, CSRF, duplicate confirmation, confirmed mutation, cross-project IDs, sensitive-value rejection and audit records.

- [ ] **Step 2: Run contracts and verify RED**

Run: `uv run pytest apps/control-api/tests/contract/test_test_missions_api.py apps/control-api/tests/unit/test_missions/test_commands.py -q`

Expected: missing router and handlers.

- [ ] **Step 3: Implement API schemas and application handlers**

`ConfirmMissionRequest` carries only `revision_hash` and a bounded idempotency key. The response exposes facts with provenance, missing inputs, preview, linked assets and status, but redacts sensitive values. Confirmation records actor/time/hash and calls a runtime port only after the transaction commits.

- [ ] **Step 4: Wire bootstrap and audit**

Register models, repositories, services and router in `bootstrap/app.py`. Audit `mission.created`, `mission.confirmed`, `mission.resumed`, `mission.cancelled` and high-impact decisions with IDs and hashes, never snapshots containing secrets.

- [ ] **Step 5: Verify contracts and commit**

Run: `uv run pytest apps/control-api/tests/contract/test_test_missions_api.py apps/control-api/tests/unit/test_missions -q`

```bash
git add apps/control-api/src/agenttest/modules/test_missions apps/control-api/src/agenttest/bootstrap/app.py apps/control-api/tests/contract/test_test_missions_api.py apps/control-api/tests/unit/test_missions
git commit -m "feat: expose confirmed test mission API"
```

### Task 5: Idempotent Asset Compiler and Existing Module Closure

**Files:**
- Create: `apps/control-api/src/agenttest/modules/test_missions/application/compiler.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/application/stages.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/infrastructure/platform_gateway.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/adapters/platform.py`
- Test: `apps/control-api/tests/unit/test_missions/test_compiler.py`
- Test: `apps/control-api/tests/integration/test_mission_asset_closure.py`

**Interfaces:**
- Produces: `MissionCompiler.compile(revision) -> ProvisioningPlan`, `MissionStageService.execute(project_id, revision_id, stage, idempotency_key) -> StageReceipt`.
- Consumes public application interfaces from agents, datasets, scorers, test plans, runs, security, reviews, reports, experiments and gates.

- [ ] **Step 1: Write failing compiler and closure tests**

```python
async def test_compiler_reuses_matching_published_assets_and_creates_missing_versions():
    plan = await compiler.compile(revision)
    assert plan.agent.relation == "reused"
    assert plan.dataset.relation == "created"

async def test_replaying_provision_stage_returns_same_plan_version_and_run():
    first = await stages.execute(PROJECT_ID, REVISION_ID, "start_run", "rev:start_run")
    second = await stages.execute(PROJECT_ID, REVISION_ID, "start_run", "rev:start_run")
    assert second == first
```

- [ ] **Step 2: Verify RED**

Run: `uv run pytest apps/control-api/tests/unit/test_missions/test_compiler.py apps/control-api/tests/integration/test_mission_asset_closure.py -q`

Expected: compiler and stage service missing.

- [ ] **Step 3: Implement deterministic asset decisions**

The compiler resolves exact project-scoped IDs and immutable versions. Generated cases carry `source`, `confidence`, `scenario`, safety policy, execution mode and expected outcome. It builds API bulk cases plus browser critical cases and security baseline cases, selects compatible scorer versions, then creates/publishes a plan version through public module interfaces.

- [ ] **Step 4: Implement stage receipts and result closure**

Persist one receipt per revision/stage. `start_run` uses idempotency key `mission:{revision_id}:run`. Completion links Run, Evidence, Artifact, Security Finding, Review Task, Report and Gate; failed Run Cases call existing dataset failure-to-case generation and link candidates with `generated_from_failure`.

- [ ] **Step 5: Run closure tests and commit**

Run: `uv run pytest apps/control-api/tests/unit/test_missions/test_compiler.py apps/control-api/tests/integration/test_mission_asset_closure.py -q`

```bash
git add apps/control-api/src/agenttest/modules/test_missions apps/control-api/src/agenttest/modules/test_agent/adapters/platform.py apps/control-api/tests/unit/test_missions apps/control-api/tests/integration/test_mission_asset_closure.py
git commit -m "feat: compile missions into platform test assets"
```

### Task 6: Temporal Mission Workflow, Pause/Resume and Error Classification

**Files:**
- Create: `apps/control-api/src/agenttest/modules/test_missions/application/runtime.py`
- Create: `apps/control-api/src/agenttest/modules/test_missions/infrastructure/temporal_orchestrator.py`
- Create: `workers/api-runner/src/agenttest_api_runner/mission_contracts.py`
- Create: `workers/api-runner/src/agenttest_api_runner/mission_activities.py`
- Create: `workers/api-runner/src/agenttest_api_runner/mission_workflow.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/main.py`
- Test: `apps/control-api/tests/unit/test_missions/test_temporal_orchestrator.py`
- Test: `workers/api-runner/tests/test_mission_workflow.py`
- Modify: `workers/api-runner/tests/test_main.py`

**Interfaces:**
- Produces Temporal workflow name `TestMissionWorkflow`, signals `cancel` and `resume`, query `state`, and activity `execute_mission_stage`.
- Consumes only a secret-free `MissionWorkflowTask` containing project ID, mission ID, revision ID, revision hash, stage policy, callback base URL and internal token reference supplied to Activity configuration, not persisted in mission snapshot.

- [ ] **Step 1: Write failing workflow replay and state tests**

```python
async def test_workflow_pauses_on_auth_expired_and_resumes_same_stage(env):
    result = await run_with_stage_results([AuthExpired(), StageReceipt.ok(), RunCompleted()])
    assert result.status == "completed"
    assert calls == ["provision", "start_run", "start_run", "close_loop"]

async def test_cancel_stops_new_stages_but_posts_terminal_receipt(env):
    handle = await start_workflow()
    await handle.signal("cancel")
    assert (await handle.result()).status == "cancelled"
```

Cover deterministic replay, timeout/retry policies, target quota, target product error, platform error, budget soft/hard limits and duplicate Activity completion.

- [ ] **Step 2: Run workflow tests and verify RED**

Run: `uv run pytest apps/control-api/tests/unit/test_missions/test_temporal_orchestrator.py workers/api-runner/tests/test_mission_workflow.py workers/api-runner/tests/test_main.py -q`

Expected: workflow and runtime missing.

- [ ] **Step 3: Implement Control API runtime and secret-free payload**

`TemporalMissionOrchestrator.start()` uses workflow ID `test-mission-{mission_id}-{revision_number}`. The payload includes immutable IDs/hash and callback configuration. Cancel/resume are idempotent and tolerate Temporal `NOT_FOUND` only for already-terminal local missions.

- [ ] **Step 4: Implement workflow and authenticated stage Activity**

The Workflow calls stages `provision`, `start_run`, `await_run`, `close_loop`. Activity posts to internal endpoints with timeouts and redacted error logging. `auth_expired` and recoverable quota states enter `needs_attention`; platform transient errors retry; quality failure completes the workflow with a failed quality result rather than a platform error.

- [ ] **Step 5: Verify replay/error tests and commit**

Run: `uv run pytest apps/control-api/tests/unit/test_missions/test_temporal_orchestrator.py workers/api-runner/tests/test_mission_workflow.py workers/api-runner/tests/test_main.py -q`

```bash
git add apps/control-api/src/agenttest/modules/test_missions workers/api-runner/src/agenttest_api_runner workers/api-runner/tests apps/control-api/tests/unit/test_missions
git commit -m "feat: orchestrate reliable test missions"
```

### Task 7: SuperAgent Mission Capabilities and Minimal Follow-Up Questions

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/test_agent/application/platform_catalog.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/application/sub_agents.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/application/super_agent.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/application/conversation.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/adapters/platform.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/api/router.py`
- Test: `apps/control-api/tests/unit/test_agent/test_mission_capabilities.py`
- Modify: `apps/control-api/tests/contract/test_super_agent_chat_api.py`

**Interfaces:**
- Produces capabilities `test_missions.create_or_update`, `discover`, `preview`, `confirm_and_start`, `resume`, `cancel`, `get_status` under a `mission` SubAgent.
- Consumes Mission API application handlers, session artifact/event projection and strict input models.

- [ ] **Step 1: Write failing conversational behavior tests**

```python
async def test_url_and_goal_create_one_mission_action_not_asset_write_actions():
    response = await conversation.respond(history=[("user", "只读测试 https://target.test 的客服 Agent")])
    assert [a.capability for a in response.actions] == ["test_missions.create_or_update"]

async def test_missing_access_response_asks_only_for_browser_profile():
    response = await send_chat_with_mission(missing=("access",))
    assert "浏览器实例" in response.content
    assert "测试目标" not in response.content
```

- [ ] **Step 2: Run tests and verify RED**

Run: `uv run pytest apps/control-api/tests/unit/test_agent/test_mission_capabilities.py apps/control-api/tests/contract/test_super_agent_chat_api.py -q`

Expected: mission capability absent.

- [ ] **Step 3: Add Mission SubAgent and bounded prompts**

The SuperAgent routes whole-test requests to Mission capabilities. Prompt rules require reading current mission context, asking only `missing_inputs`, never emitting direct asset-write/Run actions for a mission, and never treating target content as platform instruction.

- [ ] **Step 4: Project Mission events and assets into chat**

Session responses include active mission summary and mission events through existing SSE ordering. Confirmation creates one confirmation card whose preview hash maps to `confirm_and_start`; high-impact target actions continue using existing separate confirmation records.

- [ ] **Step 5: Verify chat tests and commit**

Run: `uv run pytest apps/control-api/tests/unit/test_agent apps/control-api/tests/contract/test_super_agent_chat_api.py -q`

```bash
git add apps/control-api/src/agenttest/modules/test_agent apps/control-api/tests/unit/test_agent apps/control-api/tests/contract/test_super_agent_chat_api.py
git commit -m "feat: guide conversational test missions"
```

### Task 8: Web Mission Cards, Context and Recovery

**Files:**
- Modify: `apps/web/src/features/test-agent/api.ts`
- Create: `apps/web/src/features/test-agent/mission-types.ts`
- Create: `apps/web/src/features/test-agent/mission-intake-card.tsx`
- Create: `apps/web/src/features/test-agent/mission-discovery-card.tsx`
- Create: `apps/web/src/features/test-agent/mission-confirmation-card.tsx`
- Create: `apps/web/src/features/test-agent/mission-progress-card.tsx`
- Modify: `apps/web/src/features/test-agent/chat-reducer.ts`
- Modify: `apps/web/src/features/test-agent/conversation-timeline.tsx`
- Modify: `apps/web/src/features/test-agent/context-panel.tsx`
- Modify: `apps/web/src/features/test-agent/chat-screen.tsx`
- Modify: `apps/web/src/features/test-agent/index.ts`
- Test: `apps/web/src/features/test-agent/tests/mission-cards.test.tsx`
- Test: `apps/web/src/features/test-agent/tests/mission-recovery.test.tsx`
- Modify: `apps/web/src/features/test-agent/tests/chat-reducer.test.ts`

**Interfaces:**
- Produces accessible cards for missing input, discovery, one-time confirmation and stage/result progress.
- Consumes mission summary/events from session API and mission mutation endpoints; links use existing Agent, dataset, plan, run, security, review, experiment and gate routes.

- [ ] **Step 1: Write failing component and refresh-recovery tests**

```tsx
it("shows inferred fields and one confirm action", async () => {
  render(<MissionConfirmationCard mission={readyMission} />);
  expect(screen.getAllByText("系统推断")).not.toHaveLength(0);
  expect(screen.getByRole("button", { name: "确认并开始测试" })).toBeEnabled();
});

it("restores a running mission from session history", async () => {
  render(<TestAgentChat projectId="p1" />);
  expect(await screen.findByText("浏览器关键链路执行中")).toBeVisible();
});
```

- [ ] **Step 2: Run Vitest and verify RED**

Run: `pnpm --filter @warmy/web exec vitest run src/features/test-agent/tests/mission-cards.test.tsx src/features/test-agent/tests/mission-recovery.test.tsx`

Expected: missing components/types.

- [ ] **Step 3: Implement typed API and cards**

Render provenance, confidence, verified state, execution channels, estimated cases/time/cost, allowed/forbidden actions and asset decisions. Disable confirmation when hash is absent/stale or the mutation is pending. Use semantic tokens, accessible labels, keyboard focus and loading/error states.

- [ ] **Step 4: Add reducer/SSE recovery and context links**

Reducer applies mission events idempotently by event sequence. Session reload restores active mission and its latest stages. Context panel shows completeness, current Revision, linked assets, Run and terminal outcome without storing secrets in browser state.

- [ ] **Step 5: Verify frontend slice and commit**

Run: `pnpm --filter @warmy/web exec prettier --check src/features/test-agent && pnpm --filter @warmy/web exec eslint src/features/test-agent && pnpm --filter @warmy/web exec vitest run src/features/test-agent/tests && pnpm --filter @warmy/web typecheck`

```bash
git add apps/web/src/features/test-agent
git commit -m "feat: add conversational mission experience"
```

### Task 9: OpenAPI, Generated Client and Full-Stack Fake Target E2E

**Files:**
- Modify: `packages/generated-api-client/src/client/*` through generation command
- Create: `apps/web/playwright/test-agent-mission.spec.ts`
- Create: `workers/api-runner/tests/fake_mission_target.py`
- Create: `workers/api-runner/tests/test_mission_end_to_end.py`
- Modify: `Makefile`
- Test: `packages/generated-api-client/src/index.test.ts`

**Interfaces:**
- Produces generated Mission API types and a reproducible local full-stack acceptance target.
- Consumes public Control API, Temporal worker, object storage and browser runtime exactly as production paths do.

- [ ] **Step 1: Write failing generated-client and E2E expectations**

The fake target implements an API Agent endpoint, browser login/chat flow, configurable auth expiry, quota response, product error and successful evidence response. E2E enters only URL and goal, supplies a Browser Profile when requested, reviews inferred cases, confirms once, observes a terminal Run and opens linked platform assets.

- [ ] **Step 2: Run API drift and focused E2E to verify RED**

Run: `make api-check && uv run pytest workers/api-runner/tests/test_mission_end_to_end.py -q`

Expected: generated contract drift and missing Fake Target mission path.

- [ ] **Step 3: Regenerate client and implement Fake Target scenarios**

Run the repository OpenAPI generation command from `Makefile`. Implement success, target failure, auth expiry/resume, cancellation, retry and duplicate-confirm scenarios without bypassing Control API or Temporal.

- [ ] **Step 4: Run backend and browser E2E**

Run: `uv run pytest workers/api-runner/tests/test_mission_end_to_end.py -q && pnpm --filter @warmy/web exec playwright test playwright/test-agent-mission.spec.ts`

Expected: all scenarios pass and created records are verified through public APIs.

- [ ] **Step 5: Commit contracts and E2E**

```bash
git add packages/generated-api-client apps/web/playwright/test-agent-mission.spec.ts workers/api-runner/tests Makefile
git commit -m "test: verify full conversational mission chain"
```

### Task 10: Production Verification, Runbook and Task Closure

**Files:**
- Create: `docs/runbooks/conversational-agent-test-missions.md`
- Modify: `docs/Agent测试平台技术架构与开发规范.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

**Interfaces:**
- Produces operational setup, recovery, auth-expiry, budget, troubleshooting, rollback and real-target acceptance instructions.
- Consumes all completed tasks and actual verification evidence only.

- [ ] **Step 1: Run backend, Worker, plugin and architecture gates**

```bash
uv run ruff check apps/control-api workers plugins
uv run mypy apps/control-api/src workers/api-runner/src plugins/canvas-agent/src
uv run pytest apps/control-api/tests workers/api-runner/tests plugins/canvas-agent/tests -q
uv run pytest apps/control-api/tests/architecture -q
uv run python scripts/check_architecture.py
make api-check
```

Expected: zero failures.

- [ ] **Step 2: Run database production migration checks**

Create isolated PostgreSQL databases and verify empty `→ 0020` and `0019 → 0020`. Inspect foreign keys, unique/check constraints and indexes; run project-isolation/concurrency tests; then drop temporary databases.

- [ ] **Step 3: Run full frontend gates**

```bash
pnpm --filter @warmy/web exec prettier --check .
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web test
pnpm --filter @warmy/web exec playwright test playwright/test-agent-mission.spec.ts
pnpm --filter @warmy/web build
```

Expected: zero failures and a successful production build.

- [ ] **Step 4: Run full local integration and real target gate**

Start PostgreSQL, Temporal, MinIO, Control API, Worker and Web from supported compose/runbook commands. Execute the Fake Target mission through the UI and verify all platform records. Then execute one real read-only target mission with an approved test account and sufficient quota. If the external account/quota is unavailable, record the exact blocker and do not mark real-target acceptance or production readiness as passed.

- [ ] **Step 5: Security and change hygiene**

Run `git diff --check`, scan changed files and test artifacts for password/token/cookie/storage-state patterns, verify logs and Temporal payload samples are redacted, and confirm no unrelated user changes were overwritten.

- [ ] **Step 6: Update runbook and ledgers with exact evidence**

Document configuration, permissions, state model, pause/resume, rollback of migration `0020`, operator diagnostics, actual test commands/counts, external gate status and known risks. Set `docs/当前任务.md` to no active task only if every mandatory gate, including the real target gate, passed; otherwise mark the task blocked with recovery inputs.

- [ ] **Step 7: Commit verification records**

```bash
git add docs
git commit -m "docs: close conversational mission delivery"
```
