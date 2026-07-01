# Agent Test Asset Contract and Execution Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every professional test module independently usable and connect all versioned assets into a real Agent execution, evaluation, review, security, experiment, and release-gate loop.

**Architecture:** Introduce typed versioned contracts for Agent invocation, environments, scorer bindings, review policies, and release decisions. Build one immutable `RunExecutionSnapshot` in the Control API composition root; API Runner consumes only that contract and returns normalized case results, while evaluation and downstream quality modules consume persisted results through public application services.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy 2, Alembic, PostgreSQL, Temporal Python SDK, httpx, Next.js 16, React 19, TypeScript 6, Vitest, pytest.

---

### Task 1: Freeze the executable asset contracts

**Files:**
- Create: `apps/control-api/src/agenttest/modules/agents/domain/invocation.py`
- Create: `apps/control-api/src/agenttest/modules/environments/domain/runtime.py`
- Create: `apps/control-api/src/agenttest/modules/runs/application/execution_snapshot.py`
- Modify: `apps/control-api/src/agenttest/modules/agents/api/schemas.py`
- Test: `apps/control-api/tests/unit/agents/test_invocation_contract.py`
- Test: `apps/control-api/tests/unit/runs/test_execution_snapshot.py`

- [x] **Step 1: Write failing contract tests** proving endpoint/protocol/request mapping/response mapping are validated, credentials remain references, and a Run snapshot rejects missing agent, cases, or evaluation policy.
- [x] **Step 2: Run** `uv run pytest apps/control-api/tests/unit/agents/test_invocation_contract.py apps/control-api/tests/unit/runs/test_execution_snapshot.py -q` and verify missing types fail collection.
- [x] **Step 3: Implement typed contracts** with `extra="forbid"`:

```python
class InvocationProtocol(StrEnum):
    SYNC_JSON = "sync_json"
    OPENAI_CHAT = "openai_chat"
    SSE = "sse"
    ASYNC_POLL = "async_poll"

class AgentInvocationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    endpoint_url: AnyHttpUrl
    protocol: InvocationProtocol = InvocationProtocol.SYNC_JSON
    request_template: dict[str, object] = {"input": "{{ input }}"}
    response_path: str = "output"
    timeout_seconds: int = Field(default=30, ge=1, le=600)
    credential_binding_ids: list[UUID] = Field(default_factory=list)
```

Define `EnvironmentRuntimeSnapshot`, `CaseExecutionSnapshot`, `ScorerBindingSnapshot`, `SecurityBindingSnapshot`, and `RunExecutionSnapshot` with explicit fields.
- [x] **Step 4: Re-run focused tests, Ruff, and mypy.**
- [x] **Step 5: Commit** `feat: define executable asset contracts`.

### Task 2: Expand versioned persistence and migrate legacy Agent configuration

**Files:**
- Create: `apps/control-api/migrations/versions/0013_executable_asset_contracts.py`
- Modify: `apps/control-api/src/agenttest/modules/agents/infrastructure/persistence/models.py`
- Modify: `apps/control-api/src/agenttest/modules/environments/infrastructure/persistence/models.py`
- Modify: `apps/control-api/src/agenttest/modules/scorers/infrastructure/persistence/models.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/infrastructure/persistence/models.py`
- Test: `apps/control-api/tests/integration/test_executable_asset_migration.py`

- [ ] **Step 1: Write a failing PostgreSQL migration test** for `environment_versions`, `credential_bindings`, `scorer_versions`, `run_evaluations`, `scores`, `security_profiles`, `review_policies`, and `release_decisions`, including project composite keys and reverse-reference indexes.
- [ ] **Step 2: Run the test against an isolated database** and verify revision `0013` is absent.
- [ ] **Step 3: Implement an Expand migration.** Add `schema_version` and `invocation_config` to AgentVersion, map legacy `api_url` to `endpoint_url`, and mark configurations that cannot be inferred as `needs_configuration`; never invent credentials or publish missing fields.
- [ ] **Step 4: Verify offline SQL, empty upgrade, `0012 -> 0013`, downgrade, and constraint enforcement.**
- [ ] **Step 5: Commit** `feat: persist executable asset versions`.

### Task 3: Agent configuration, connection validation, and publish readiness

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/agents/application/commands.py`
- Create: `apps/control-api/src/agenttest/modules/agents/application/validate_connection.py`
- Modify: `apps/control-api/src/agenttest/modules/agents/api/router.py`
- Replace: `apps/web/src/features/agents/agent-version-dialog.tsx`
- Create: `apps/web/src/features/agents/connection-test-panel.tsx`
- Test: `apps/control-api/tests/contract/test_agent_connection_api.py`
- Test: `apps/web/src/features/agents/tests/agent-version-config.test.tsx`

- [ ] **Step 1: Write failing API and component tests** for all protocol fields, conditional polling fields, request/response preview, real connection failure, and publish rejection when readiness fails.
- [ ] **Step 2: Run focused tests and verify the existing three-field form fails.**
- [ ] **Step 3: Implement `POST .../versions/{id}/validate-connection`** through the real API Runner adapter using a user-supplied safe probe payload and masked credential resolution.
- [ ] **Step 4: Build a four-section version editor** for connection, mappings, limits, and metadata; label metadata fields as trace-only and persist all supported fields.
- [ ] **Step 5: Verify tests, TypeScript, browser create/edit/validate/publish flow, then commit** `feat: make agent versions executable`.

### Task 4: Environment versions and encrypted credential bindings

**Files:**
- Create: `apps/control-api/src/agenttest/modules/environments/domain/credentials.py`
- Create: `apps/control-api/src/agenttest/modules/environments/application/versions.py`
- Modify: `apps/control-api/src/agenttest/modules/environments/api/schemas.py`
- Modify: `apps/control-api/src/agenttest/modules/environments/api/router.py`
- Replace: `apps/web/src/features/environments/environment-list.tsx`
- Create: `apps/web/src/features/environments/environment-editor.tsx`
- Test: `apps/control-api/tests/contract/test_environment_versions_api.py`
- Test: `apps/web/src/features/environments/tests/environment-editor.test.tsx`

- [ ] **Step 1: Write failing tests** for variables, public headers, credential injection location, encryption/redaction, version immutability, validation, and cross-project rejection.
- [ ] **Step 2: Verify current name-only form and untyped config fail.**
- [ ] **Step 3: Implement version and credential services.** Credential responses expose only `id`, `alias`, `kind`, `masked_hint`, and `updated_at`; runtime resolution happens only in Worker-bound application code.
- [ ] **Step 4: Build environment list/readiness/editor UI** with Variables, Headers, Credentials, Initial State, and Sandbox sections plus validate action.
- [ ] **Step 5: Run focused tests and commit** `feat: add versioned environments and credential bindings`.

### Task 5: Strict test-case import contract and usable import wizard

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/datasets/application/import_export.py`
- Modify: `apps/control-api/src/agenttest/modules/datasets/api/router.py`
- Modify: `apps/control-api/src/agenttest/modules/datasets/api/schemas.py`
- Create: `docs/test-case-import-format.md`
- Replace: `apps/web/src/features/datasets/import-wizard.tsx`
- Modify: `apps/web/src/features/datasets/dataset-detail.tsx`
- Test: `apps/control-api/tests/unit/datasets/test_import_contract.py`
- Test: `apps/control-api/tests/contract/test_dataset_import_preview_api.py`
- Test: `apps/web/src/features/datasets/tests/import-wizard.test.tsx`

- [ ] **Step 1: Write failing tests** for selection of a draft version, 10MB enforcement, strict object/list types, enum errors, JSON/JSONL/CSV parity, dry-run, line/field errors, and atomic import.
- [ ] **Step 2: Verify malformed `input` currently becomes `{}` and the global wizard cannot import.**
- [ ] **Step 3: Implement `POST .../versions/{id}/imports:preview` and strict parsing** returning `{valid_count, errors:[{line,field,code,message}], preview}`.
- [ ] **Step 4: Move import into Dataset detail, add template downloads and examples, require preview before import, and show imported count.**
- [ ] **Step 5: Prove an imported case is published, snapshotted, and executable in the core-chain integration test; commit** `feat: make test case imports executable`.

### Task 6: Typed scorer versions and independent trial evaluation

**Files:**
- Create: `apps/control-api/src/agenttest/modules/scorers/domain/config.py`
- Create: `apps/control-api/src/agenttest/modules/scorers/application/evaluate.py`
- Modify: `apps/control-api/src/agenttest/modules/scorers/api/router.py`
- Replace: `apps/web/src/features/scorers/scorer-editor.tsx`
- Test: `apps/control-api/tests/unit/scorers/test_scorer_configs.py`
- Test: `apps/control-api/tests/contract/test_scorer_trial_api.py`
- Test: `apps/web/src/features/scorers/tests/scorer-editor.test.tsx`

- [ ] **Step 1: Write failing tests** for Rule, Reference, and Model Judge discriminated configs and real trial results.
- [ ] **Step 2: Verify the existing editor cannot configure evaluator behavior.**
- [ ] **Step 3: Implement scorer configs and public evaluator**; Model Judge resolves a project ModelConfig and calls Model Runner with typed JSON output.
- [ ] **Step 4: Build type-specific editor and “试评” panel with sample input/output/reference.**
- [ ] **Step 5: Verify and commit** `feat: add executable scorer versions`.

### Task 7: Test-plan asset graph, readiness, and typed execution policy

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/test_plans/domain/value_objects.py`
- Modify: `apps/control-api/src/agenttest/modules/test_plans/domain/entities.py`
- Modify: `apps/control-api/src/agenttest/modules/test_plans/application/commands.py`
- Modify: `apps/control-api/src/agenttest/modules/test_plans/api/schemas.py`
- Replace: `apps/web/src/features/test-plans/test-plan-version-dialog.tsx`
- Test: `apps/control-api/tests/unit/test_plans/test_asset_graph.py`
- Test: `apps/control-api/tests/contract/test_test_plan_readiness_api.py`
- Test: `apps/web/src/features/test-plans/tests/test-plan-version-dialog.test.tsx`

- [ ] **Step 1: Write failing tests** requiring published Agent/Dataset/Environment, typed scorer/security/review/gate IDs, explicit observation-only mode, and project-compatible references.
- [ ] **Step 2: Verify free-text baseline and untyped scorer/gate JSON fail.**
- [ ] **Step 3: Replace JSON lists with ID bindings and `ExecutionPolicy`.** Add readiness endpoint returning blocking issues and estimated cases.
- [ ] **Step 4: Build a four-step plan editor** using searchable asset selectors and clear “used at runtime” descriptions.
- [ ] **Step 5: Verify and commit** `feat: connect test plan asset graph`.

### Task 8: Correct immutable Run snapshots and Worker protocol execution

**Files:**
- Replace: `apps/control-api/src/agenttest/bootstrap/run_source.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/infrastructure/temporal_orchestrator.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/contracts.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/adapter.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/activities.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/workflow.py`
- Test: `apps/control-api/tests/integration/test_run_execution_snapshot.py`
- Test: `workers/api-runner/tests/test_protocol_execution.py`
- Test: `workers/api-runner/tests/test_workflow.py`

- [x] **Step 1: Write the regression test** proving plan config can no longer be passed as Agent config and that environment/case/evaluator fields survive serialization.
- [x] **Step 2: Run it and observe the current missing `url`/wrong nesting failure.**
- [ ] **Step 3: Build `RunExecutionSnapshot` from published assets**, resolve credential references only for the Activity, render request templates, support sync/OpenAI/SSE/poll, extract response paths, and redact Trace.
- [ ] **Step 4: Apply concurrency, retries, timeout, cancellation, idempotency, and budget checks deterministically in Workflow.**
- [ ] **Step 5: Run Worker tests including replay and commit** `fix: execute immutable run snapshots`.

### Task 9: Persist scores and aggregate real evaluations

**Files:**
- Create: `apps/control-api/src/agenttest/modules/evaluations/`
- Modify: `apps/control-api/src/agenttest/modules/runs/application/result_handler.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/workflow.py`
- Create: `apps/control-api/tests/integration/test_run_evaluation_chain.py`
- Create: `workers/api-runner/tests/test_scorer_activities.py`

- [ ] **Step 1: Write failing tests** for deterministic assertions, rule/reference/model scores, weighted aggregate, threshold, confidence, cost, token usage, and explicit scorer failure.
- [ ] **Step 2: Verify Run currently records only status/output/trace.**
- [ ] **Step 3: Add Score/Evaluation domain and repositories**, run scoring Activities after each target result, and apply results idempotently through protected callbacks.
- [ ] **Step 4: Expose Evaluation in Run detail API/UI and link scorer versions.**
- [ ] **Step 5: Verify and commit** `feat: persist multidimensional evaluations`.

### Task 10: Connect experiments and automatic human review

**Files:**
- Create: `apps/control-api/src/agenttest/modules/experiments/application/service.py`
- Create: `apps/control-api/src/agenttest/modules/reviews/application/collector.py`
- Modify: `apps/control-api/src/agenttest/modules/experiments/api/router.py`
- Modify: `apps/control-api/src/agenttest/modules/reviews/api/router.py`
- Replace: `apps/web/src/features/experiments/experiment-list.tsx`
- Modify: `apps/web/src/features/reviews/review-workbench.tsx`
- Test: `apps/control-api/tests/integration/test_experiment_review_chain.py`
- Test: `apps/web/src/features/experiments/tests/experiment-create.test.tsx`

- [ ] **Step 1: Write failing tests** for compatible Run selection, score/cost/security diffs, review auto-collection, deduplication, and source links.
- [ ] **Step 2: Verify free-text Run UUID and unused `AutoCollector` fail the tests.**
- [ ] **Step 3: Extract application services**, query compatible runs, compare Evaluations, and create ReviewTask after Evaluation/Security events.
- [ ] **Step 4: Replace UUID inputs with searchable run selectors and show review source/evidence.**
- [ ] **Step 5: Verify and commit** `feat: connect experiments and review collection`.

### Task 11: Connect security profiles, findings, and regression conversion

**Files:**
- Create: `apps/control-api/src/agenttest/modules/security/application/service.py`
- Modify: `apps/control-api/src/agenttest/modules/security/api/scan_router.py`
- Modify: `apps/web/src/features/security/security-scan.tsx`
- Create: `apps/control-api/tests/integration/test_security_asset_chain.py`
- Create: `apps/web/src/features/security/tests/security-scan-config.test.tsx`

- [ ] **Step 1: Write failing tests** for Agent/Environment/Profile selection, Promptfoo real failure semantics, Finding persistence, project isolation, and conversion to TestCase.
- [ ] **Step 2: Verify raw URL scanning and pending-only records fail.**
- [ ] **Step 3: Implement public security service** resolving published assets and environment credentials without returning secrets; persist completed/failed state and findings.
- [ ] **Step 4: Build asset selectors, profile editor, progress/error states, and finding-to-regression action.**
- [ ] **Step 5: Verify and commit** `feat: connect security testing assets`.

### Task 12: Replace hard-coded gates with real release decisions

**Files:**
- Create: `apps/control-api/src/agenttest/modules/gates/application/evaluate.py`
- Modify: `apps/control-api/src/agenttest/modules/gates/api/router.py`
- Replace: `apps/web/src/features/gates/gate-list.tsx`
- Create: `apps/control-api/tests/integration/test_release_decision_chain.py`
- Create: `apps/web/src/features/gates/tests/gate-evaluation.test.tsx`

- [ ] **Step 1: Write a failing test** rejecting client-submitted pass-rate/security facts and aggregating actual Run Evaluation, critical cases, cost, SecurityFindings, Experiment, and pending ReviewTasks.
- [ ] **Step 2: Prove the existing `0.85` and `critical_passed=true` UI path fails.**
- [ ] **Step 3: Change evaluate API input to `{run_id, experiment_id?}`**, compute server-side facts, persist ReleaseDecision with evidence links, and audit exemptions.
- [ ] **Step 4: Replace manual metric submission with Run/Experiment selectors and evidence display.**
- [ ] **Step 5: Verify and commit** `fix: evaluate release gates from real evidence`.

### Task 13: Super-Agent capability alignment and standalone/full-chain UI guidance

**Files:**
- Modify: `apps/control-api/src/agenttest/modules/test_agent/application/platform_catalog.py`
- Modify: `apps/control-api/src/agenttest/modules/test_agent/adapters/platform.py`
- Modify: `apps/web/src/features/test-agent/context-panel.tsx`
- Modify: module list/detail pages under `apps/web/src/features/`
- Test: `apps/control-api/tests/integration/test_super_agent_complete_asset_chain.py`
- Test: `apps/web/src/features/test-agent/tests/asset-readiness.test.tsx`

- [ ] **Step 1: Write failing tests** proving Agent-created assets use the same typed services and produce the same Run/Evaluation/ReleaseDecision records as console actions.
- [ ] **Step 2: Verify legacy untyped capability inputs fail.**
- [ ] **Step 3: Update capability schemas, previews, confirmations, and artifact links.**
- [ ] **Step 4: Add module readiness badges, reference counts, field help, actionable empty states, and narrow-viewport header/sidebar behavior.**
- [ ] **Step 5: Verify and commit** `feat: align super agent with executable asset graph`.

### Task 14: Contracts, documentation, migrations, browser E2E, and final verification

**Files:**
- Modify: `docs/api/openapi.json`
- Regenerate: `packages/generated-api-client/src/client/`
- Modify: `README.md`
- Create: `docs/runbooks/agent-test-complete-flow.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`
- Create: `apps/web/playwright/agent-test-complete-flow.spec.ts`

- [ ] **Step 1: Document exact field purposes and import templates** and add a runbook from Agent through ReleaseDecision.
- [ ] **Step 2: Regenerate OpenAPI/client and verify zero drift.**
- [ ] **Step 3: Run isolated PostgreSQL migration/constraints/project-isolation tests.**
- [ ] **Step 4: Run Worker protocol, retry, cancellation, callback, and Temporal replay tests.**
- [ ] **Step 5: Run browser E2E** covering standalone Agent validation, environment validation, import preview/import, scorer trial, plan readiness, Run, experiment, security, review, and gate evidence.
- [ ] **Step 6: Run `make verify`, truthfulness scan, `git diff --check`, and secret scan.**
- [ ] **Step 7: Update ledgers with exact evidence and commit** `docs: complete executable agent testing loop`.
