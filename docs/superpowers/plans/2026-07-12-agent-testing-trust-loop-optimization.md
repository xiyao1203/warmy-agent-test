# Agent Testing Trust Loop Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-isomorphic Agent testing loop whose execution, evaluation, diagnosis, regression assets and release decisions are reproducible, evidence-backed and safe.

**Architecture:** Extend the existing Test Mission and Run modules instead of adding a second orchestration or asset system. A standalone deterministic Fake Target exercises the public Control API → Temporal → Worker path; RunCase stores independent execution/assertion/quality/security outcomes and immutable Evidence references; deterministic classifiers and gates own decisions while Agent models produce evidence-bounded proposals and explanations.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic, SQLAlchemy 2, Alembic, PostgreSQL 17, Temporal Python SDK, PydanticAI, DeepEval, Promptfoo, React 19, Next.js 16, TypeScript, Vitest and Playwright.

## Global Constraints

- All business records and reads are scoped by `project_id`; cross-project references fail closed.
- Workers do not connect to the business database and use authenticated internal Control API endpoints only.
- Passwords, tokens, cookies and plaintext browser auth state never enter chat, snapshots, logs, Trace, Artifact metadata or Temporal history.
- Models cannot mutate original Evidence, expand action allowlists, bypass confirmation or directly decide release status.
- A green retry never overwrites an earlier failure; every attempt remains auditable.
- Generated regression cases are publishable only after reproducing the original failure under the same immutable snapshot and safety boundary.
- Critical-path failures, high/critical security findings and incomplete Evidence cannot be offset by aggregate quality scores.
- All behavior changes follow red-green-refactor; generated API clients are regenerated rather than hand-edited.

---

### Task 1: Production-Isomorphic Fake Target Service

**Files:**
- Create: `tests/fake-agent-target/app.py`
- Create: `tests/fake-agent-target/scenarios.py`
- Create: `tests/fake-agent-target/state.py`
- Create: `tests/fake-agent-target/README.md`
- Create: `tests/fake-agent-target/tests/test_fake_target.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces `create_fake_target_app(state: FakeTargetState) -> FastAPI`.
- Provides `POST /api/agent/invoke`, `GET /chat`, `POST /chat/messages`, `POST /control/scenario` and `GET /control/observations`.
- Scenario names are `success`, `stream_success`, `product_error`, `protocol_error`, `auth_expired`, `quota_exceeded`, `timeout`, `transient_failure`, `incomplete_artifact`, `prompt_injection`, `data_leak_attempt` and `privilege_escalation`.

- [ ] **Step 1: Write failing scenario contracts**

```python
async def test_transient_failure_is_deterministic(client, state):
    await client.post("/control/scenario", json={"name": "transient_failure", "failures": 1})
    assert (await client.post("/api/agent/invoke", json={"input": "hello"})).status_code == 503
    response = await client.post("/api/agent/invoke", json={"input": "hello"})
    assert response.status_code == 200
    assert response.json()["evidence"]["scenario"] == "transient_failure"
```

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/fake-agent-target/tests/test_fake_target.py -q`
Expected: collection fails because `fake_agent_target` does not exist.

- [ ] **Step 3: Implement the standalone state machine and HTTP/browser routes**

Use an `asyncio.Lock` around attempt counters. Every response includes `scenario`, `request_id`, `attempt`, observable tool calls and artifact metadata; secret-leak scenarios return synthetic markers only.

- [ ] **Step 4: Verify GREEN**

Run: `uv run pytest tests/fake-agent-target/tests/test_fake_target.py -q`
Expected: all scenario contracts pass.

- [ ] **Step 5: Commit**

```bash
git add tests/fake-agent-target pyproject.toml
git commit -m "test: add deterministic fake agent target"
```

### Task 2: Public-Path Mission Acceptance Harness

**Files:**
- Create: `tests/acceptance/test_mission_public_path.py`
- Create: `tests/acceptance/conftest.py`
- Create: `scripts/run_mission_acceptance.py`
- Modify: `Makefile`

**Interfaces:**
- Consumes only public browser/API endpoints plus supported process entrypoints.
- Produces `make mission-acceptance`, which starts an isolated Fake Target and verifies Control API → Temporal → Worker → callback → PostgreSQL records.

- [ ] **Step 1: Write failing success and duplicate-confirm acceptance tests**

```python
async def test_public_mission_success_and_duplicate_confirm(platform, fake_target):
    mission = await platform.create_mission(fake_target.url, "verify chat success")
    preview = await platform.preview(mission)
    first = await platform.confirm(mission, preview["revision_hash"], "acceptance-1")
    second = await platform.confirm(mission, preview["revision_hash"], "acceptance-1")
    assert first["workflow_id"] == second["workflow_id"]
    terminal = await platform.wait_for_terminal(mission)
    assert terminal["status"] == "completed"
    assert len([a for a in terminal["assets"] if a["type"] == "run"]) == 1
```

- [ ] **Step 2: Verify RED**

Run: `uv run pytest tests/acceptance/test_mission_public_path.py -q`
Expected: fails because the public-path harness is missing.

- [ ] **Step 3: Implement isolated service orchestration and public API client**

Start Fake Target on an ephemeral port, use a temporary PostgreSQL database and a dedicated Temporal task queue, and invoke existing Control API/Worker entrypoints. Do not import repositories into assertions.

- [ ] **Step 4: Add failure, retry, auth-resume and cancellation scenarios**

Assert persisted stage events, attempts, RunCase evidence, error classification and absence of duplicate assets.

- [ ] **Step 5: Verify GREEN and commit**

Run: `make mission-acceptance`
Expected: success, target failure, transient retry, auth resume, cancellation and duplicate confirmation pass.

```bash
git add tests/acceptance scripts/run_mission_acceptance.py Makefile
git commit -m "test: verify mission production path"
```

### Task 3: Four-Dimension Outcome Contract

**Files:**
- Create: `apps/control-api/migrations/versions/0021_run_case_outcomes.py`
- Create: `apps/control-api/src/agenttest/modules/runs/domain/outcomes.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/domain/entities.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/infrastructure/persistence/models.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/infrastructure/persistence/repositories.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/api/schemas.py`
- Test: `apps/control-api/tests/unit/runs/test_outcomes.py`
- Modify: `apps/control-api/tests/integration/test_migrations.py`
- Modify: `apps/control-api/tests/integration/test_database_constraints.py`

**Interfaces:**
- Produces `Outcome(status, code, reason, evidence_ids, evaluated_at)` and `RunCaseOutcomes(execution, assertion, quality, security)`.
- Status values are `not_evaluated`, `passed`, `failed`, `error` and `needs_review`.

- [ ] **Step 1: Write failing domain and migration tests**

```python
def test_technical_success_does_not_override_security_failure():
    outcomes = RunCaseOutcomes.started().with_execution(Outcome.passed()).with_security(
        Outcome.failed("critical_finding", evidence_ids=(EVIDENCE_ID,))
    )
    assert outcomes.execution.status == "passed"
    assert outcomes.security.status == "failed"
    assert outcomes.release_eligible is False
```

- [ ] **Step 2: Verify RED**

Run: `uv run pytest apps/control-api/tests/unit/runs/test_outcomes.py apps/control-api/tests/integration/test_migrations.py -q`
Expected: fails for missing outcome types and migration `0021`.

- [ ] **Step 3: Implement domain types, persistence and API schema**

Persist four JSON outcome documents with check constraints on status and GIN/index support for failure codes; preserve existing summary fields as read compatibility projections.

- [ ] **Step 4: Verify migration and project isolation**

Run: `uv run pytest apps/control-api/tests/unit/runs/test_outcomes.py apps/control-api/tests/integration/test_migrations.py apps/control-api/tests/integration/test_database_constraints.py -q`
Expected: all pass on empty and `0020 → 0021` upgrades.

- [ ] **Step 5: Commit**

```bash
git add apps/control-api/migrations/versions/0021_run_case_outcomes.py apps/control-api/src/agenttest/modules/runs apps/control-api/tests
git commit -m "feat: separate run case outcomes"
```

### Task 4: Immutable Evidence Integrity and Redaction

**Files:**
- Create: `apps/control-api/src/agenttest/modules/runs/domain/evidence.py`
- Create: `apps/control-api/src/agenttest/modules/runs/application/evidence_service.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/infrastructure/persistence/models.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/infrastructure/persistence/repositories.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/contracts.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/callback.py`
- Test: `apps/control-api/tests/unit/runs/test_evidence_integrity.py`
- Test: `workers/api-runner/tests/test_evidence_contract.py`

**Interfaces:**
- Produces `EvidenceEnvelope.create(kind, producer, scope, payload, artifact_refs)`, `content_hash` and `RedactionStatus`.
- `EvidenceService.accept()` rejects invalid hashes, scope mismatches and unredacted sensitive keys.

- [ ] **Step 1: Write failing integrity and redaction tests**

```python
def test_evidence_rejects_unredacted_secret():
    envelope = EvidenceEnvelope.create("http", "api-runner", scope, {"authorization": "synthetic-secret"})
    with pytest.raises(UnredactedEvidenceError):
        service.accept(envelope)
```

- [ ] **Step 2: Verify RED**

Run: `uv run pytest apps/control-api/tests/unit/runs/test_evidence_integrity.py workers/api-runner/tests/test_evidence_contract.py -q`
Expected: missing envelope and service.

- [ ] **Step 3: Implement canonical hashing, scope validation and redaction gate**

Use sorted compact JSON, SHA-256, explicit producer/version fields and allowlisted payload schemas. Large payloads remain Artifact references.

- [ ] **Step 4: Verify GREEN and commit**

Run: `uv run pytest apps/control-api/tests/unit/runs/test_evidence_integrity.py workers/api-runner/tests/test_evidence_contract.py -q`

```bash
git add apps/control-api/src/agenttest/modules/runs workers/api-runner
git commit -m "feat: enforce evidence integrity"
```

### Task 5: Deterministic Failure Classification

**Files:**
- Create: `apps/control-api/src/agenttest/modules/runs/domain/failure_classification.py`
- Create: `apps/control-api/src/agenttest/modules/runs/application/failure_classifier.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/application/result_handler.py`
- Test: `apps/control-api/tests/unit/runs/test_failure_classifier.py`
- Modify: `tests/acceptance/test_mission_public_path.py`

**Interfaces:**
- Produces `FailureClass`: `target_failure`, `test_failure`, `environment_failure`, `platform_failure`, `evaluation_failure`.
- `FailureClassifier.classify(outcomes, evidence) -> FailureClassification` returns class, code, confidence and evidence IDs without model calls.

- [ ] **Step 1: Write a failing classification matrix**

```python
@pytest.mark.parametrize(("code", "expected"), [
    ("auth_expired", FailureClass.ENVIRONMENT),
    ("assertion_mismatch", FailureClass.TEST),
    ("target_5xx", FailureClass.TARGET),
    ("artifact_upload_failed", FailureClass.PLATFORM),
    ("scorer_unavailable", FailureClass.EVALUATION),
])
def test_failure_codes_are_stably_classified(code, expected):
    assert classifier.classify_code(code).failure_class is expected
```

- [ ] **Step 2: Verify RED, implement ordered rules and verify GREEN**

Run before and after: `uv run pytest apps/control-api/tests/unit/runs/test_failure_classifier.py -q`

- [ ] **Step 3: Persist classification and expose it through Run APIs**

Do not overwrite an existing higher-confidence deterministic classification with a model proposal.

- [ ] **Step 4: Extend Fake Target acceptance assertions and commit**

```bash
git add apps/control-api/src/agenttest/modules/runs apps/control-api/tests/unit/runs tests/acceptance
git commit -m "feat: classify agent test failures"
```

### Task 6: Evidence-Bounded Diagnostic Agent

**Files:**
- Create: `apps/control-api/src/agenttest/modules/diagnostics/__init__.py`
- Create: `apps/control-api/src/agenttest/modules/diagnostics/domain.py`
- Create: `apps/control-api/src/agenttest/modules/diagnostics/application.py`
- Create: `apps/control-api/src/agenttest/modules/diagnostics/model_adapter.py`
- Create: `apps/control-api/src/agenttest/modules/diagnostics/api/router.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Test: `apps/control-api/tests/unit/diagnostics/test_diagnostic_service.py`
- Test: `apps/control-api/tests/contract/test_diagnostics_api.py`

**Interfaces:**
- Produces `DiagnosticHypothesis(summary, failure_class, confidence, evidence_ids, counterevidence, verification_steps)`.
- `DiagnosticService.diagnose(project_id, run_case_id)` receives an allowlisted, redacted Evidence view and returns `inconclusive` when citations are insufficient.

- [ ] **Step 1: Write failing evidence-boundary tests**

```python
async def test_diagnosis_without_citations_is_inconclusive(service):
    result = await service.diagnose(PROJECT_ID, RUN_CASE_ID)
    assert result.status == "inconclusive"
    assert result.hypotheses == ()
```

- [ ] **Step 2: Verify RED**

Run: `uv run pytest apps/control-api/tests/unit/diagnostics apps/control-api/tests/contract/test_diagnostics_api.py -q`

- [ ] **Step 3: Implement strict schemas, citation validation and project-scoped API**

Discard hallucinated Evidence IDs and confidence outside `[0, 1]`; diagnostic records append analysis without mutating Run/Evidence.

- [ ] **Step 4: Verify GREEN and commit**

```bash
git add apps/control-api/src/agenttest/modules/diagnostics apps/control-api/src/agenttest/bootstrap/app.py apps/control-api/tests
git commit -m "feat: add evidence-bound diagnostics"
```

### Task 7: Failure Fingerprints, Minimization and Regression Publication

**Files:**
- Create: `apps/control-api/src/agenttest/modules/regressions/__init__.py`
- Create: `apps/control-api/src/agenttest/modules/regressions/domain.py`
- Create: `apps/control-api/src/agenttest/modules/regressions/application.py`
- Create: `apps/control-api/src/agenttest/modules/regressions/fingerprints.py`
- Create: `apps/control-api/src/agenttest/modules/regressions/minimizer.py`
- Modify: `apps/control-api/src/agenttest/modules/test_missions/application/stages.py`
- Test: `apps/control-api/tests/unit/regressions/test_fingerprints.py`
- Test: `apps/control-api/tests/unit/regressions/test_minimizer.py`
- Test: `apps/control-api/tests/unit/regressions/test_publication.py`

**Interfaces:**
- Produces `FailureFingerprint`, `RegressionCandidate`, `ReproductionResult` and `QuarantineStatus`.
- A candidate transitions `draft → reproducing → verified → published`; failed or flaky reproduction transitions to `quarantined`.

- [ ] **Step 1: Write failing fingerprint and publication state tests**

```python
def test_candidate_cannot_publish_before_reproduction():
    candidate = RegressionCandidate.draft(failure_snapshot())
    with pytest.raises(ReproductionRequiredError):
        candidate.publish()
```

- [ ] **Step 2: Verify RED and implement canonical fingerprints**

Run: `uv run pytest apps/control-api/tests/unit/regressions -q`

- [ ] **Step 3: Implement delta-debugging minimizer with budget bounds**

Remove one scenario step/input field at a time, execute through the existing Run path, stop at the configured attempt/time budget, and retain only reductions that reproduce the same fingerprint.

- [ ] **Step 4: Implement verified publication and Quarantine**

Publishing creates a dataset version through its public application port and records source RunCase, fingerprint and reproduction Evidence.

- [ ] **Step 5: Verify GREEN and commit**

```bash
git add apps/control-api/src/agenttest/modules/regressions apps/control-api/src/agenttest/modules/test_missions apps/control-api/tests/unit/regressions
git commit -m "feat: verify generated regression cases"
```

### Task 8: Evaluation Calibration and Conflict Arbitration

**Files:**
- Create: `apps/control-api/src/agenttest/modules/scorers/domain/calibration.py`
- Create: `apps/control-api/src/agenttest/modules/scorers/application/calibration_service.py`
- Modify: `apps/control-api/src/agenttest/modules/scorers/domain/entities.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/application/evaluation.py`
- Test: `apps/control-api/tests/unit/scorers/test_calibration.py`
- Test: `apps/control-api/tests/unit/runs/test_evaluation_arbitration.py`

**Interfaces:**
- Produces `CalibrationMetrics(accuracy, false_positive_rate, false_negative_rate, agreement)` and `EvaluationDecision`.
- Uncalibrated model-only failures resolve to `needs_review`, never `failed` release status by themselves.

- [ ] **Step 1: Write failing calibration and arbitration tests**

```python
def test_uncalibrated_model_failure_requires_review():
    decision = arbiter.decide(rule=None, domain=None, model=model_failure(calibrated=False))
    assert decision.status == "needs_review"
```

- [ ] **Step 2: Verify RED, implement metrics and precedence rules, verify GREEN**

Run: `uv run pytest apps/control-api/tests/unit/scorers/test_calibration.py apps/control-api/tests/unit/runs/test_evaluation_arbitration.py -q`

- [ ] **Step 3: Commit**

```bash
git add apps/control-api/src/agenttest/modules/scorers apps/control-api/src/agenttest/modules/runs apps/control-api/tests
git commit -m "feat: calibrate agent evaluations"
```

### Task 9: Baseline Comparison and Explainable Joint Gate

**Files:**
- Create: `apps/control-api/src/agenttest/modules/release_gates/domain/baselines.py`
- Create: `apps/control-api/src/agenttest/modules/release_gates/application/joint_gate.py`
- Modify: `apps/control-api/src/agenttest/modules/release_gates/domain/entities.py`
- Modify: `apps/control-api/src/agenttest/modules/release_gates/api/schemas.py`
- Test: `apps/control-api/tests/unit/release_gates/test_joint_gate.py`
- Test: `apps/control-api/tests/contract/test_release_gate_explanations.py`

**Interfaces:**
- Produces `JointGateDecision(status, rules, baseline_id)` where each rule includes threshold, actual value, reason and Evidence/Review references.
- Inputs include critical success rate, baseline deltas, security severity, novel failure clusters, flake/quarantine rate, Evidence completeness, calibration and cost/latency budgets.

- [ ] **Step 1: Write failing non-compensation tests**

```python
def test_high_quality_score_cannot_offset_critical_security_finding():
    decision = gate.evaluate(metrics(quality=0.99, critical_security=1))
    assert decision.status == "block"
    assert "critical_security" in {rule.code for rule in decision.rules if rule.blocking}
```

- [ ] **Step 2: Verify RED and implement ordered deterministic rules**

Run: `uv run pytest apps/control-api/tests/unit/release_gates/test_joint_gate.py apps/control-api/tests/contract/test_release_gate_explanations.py -q`

- [ ] **Step 3: Verify GREEN and commit**

```bash
git add apps/control-api/src/agenttest/modules/release_gates apps/control-api/tests
git commit -m "feat: evaluate explainable joint gates"
```

### Task 10: Test Agent Product Closure

**Files:**
- Create: `apps/web/src/features/test-agent/outcome-grid.tsx`
- Create: `apps/web/src/features/test-agent/diagnostic-panel.tsx`
- Create: `apps/web/src/features/test-agent/regression-panel.tsx`
- Create: `apps/web/src/features/test-agent/gate-decision-card.tsx`
- Modify: `apps/web/src/features/test-agent/mission-progress-card.tsx`
- Modify: `apps/web/src/features/test-agent/context-panel.tsx`
- Modify: `apps/web/src/features/test-agent/api.ts`
- Modify: `apps/web/src/features/test-agent/mission-types.ts`
- Test: `apps/web/src/features/test-agent/tests/trust-loop.test.tsx`
- Modify: `apps/web/tests/e2e/test-mission.spec.ts`

**Interfaces:**
- Consumes typed RunCase outcomes, Evidence links, diagnostics, regression candidates/Quarantine and joint gate decisions.
- Produces accessible, refresh-safe Mission trust-loop views without client-derived conclusions.

- [ ] **Step 1: Write failing component tests**

```tsx
it("shows independent outcomes and the evidence-backed blocking rule", () => {
  render(<TrustLoopResult result={blockedResult} />);
  expect(screen.getByText("执行通过")).toBeVisible();
  expect(screen.getByText("安全阻断")).toBeVisible();
  expect(screen.getByRole("link", { name: "查看证据" })).toHaveAttribute("href", evidenceHref);
});
```

- [ ] **Step 2: Verify RED**

Run: `pnpm --filter @warmy/web exec vitest run src/features/test-agent/tests/trust-loop.test.tsx`

- [ ] **Step 3: Implement components and typed API projections**

Use server facts only. Render `needs_review` separately from pass/fail and show exact gate rule thresholds/actuals.

- [ ] **Step 4: Extend Playwright recovery and navigation coverage**

Verify refresh after Worker completion, Evidence navigation, Quarantine state and gate explanation.

- [ ] **Step 5: Verify GREEN and commit**

Run: `pnpm --filter @warmy/web exec vitest run src/features/test-agent && pnpm --filter @warmy/web exec playwright test tests/e2e/test-mission.spec.ts`

```bash
git add apps/web/src/features/test-agent apps/web/tests/e2e/test-mission.spec.ts
git commit -m "feat: show agent testing trust loop"
```

### Task 11: OpenAPI, Generated Client and Operational Documentation

**Files:**
- Modify: `docs/api/openapi.json`
- Modify: `packages/generated-api-client/src/client/*` through generation
- Modify: `docs/Agent测试平台技术架构与开发规范.md`
- Create: `docs/runbooks/agent-testing-trust-loop.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

**Interfaces:**
- Produces reproducible client contracts, operator diagnostics, rollback instructions and exact task evidence.

- [ ] **Step 1: Regenerate and verify the API client**

Run: `make api-generate && make api-check`
Expected: generation succeeds; after committing generated files `api-check` reports no drift.

- [ ] **Step 2: Document operations and rollback**

Document Fake Target scenarios, temporary database/task queue isolation, Evidence redaction failures, diagnostic inconclusive state, Quarantine, baseline selection, gate rule inspection and migration `0021` rollback.

- [ ] **Step 3: Update architecture and ledgers with actual evidence**

Do not mark complete until public-path acceptance and real-target gates satisfy the spec.

- [ ] **Step 4: Commit**

```bash
git add docs packages/generated-api-client
git commit -m "docs: operate agent testing trust loop"
```

### Task 12: Full Verification and Real-Target Gate

**Files:**
- Modify only defects found by the verification commands.

**Interfaces:**
- Produces final verification evidence and a clean branch; completion requires every mandatory gate.

- [ ] **Step 1: Run Python and architecture gates**

```bash
uv run ruff check apps/control-api workers plugins tests
uv run mypy apps/control-api/src workers/api-runner/src plugins/canvas-agent/src
uv run pytest apps/control-api/tests workers/api-runner/tests plugins/canvas-agent/tests tests/fake-agent-target/tests -q
uv run pytest apps/control-api/tests/architecture -q
uv run python scripts/check_architecture.py
```

- [ ] **Step 2: Run isolated PostgreSQL migration and isolation gates**

Verify empty database → head, `0020 → 0021`, constraints, indexes, project isolation and concurrency, then delete temporary databases.

- [ ] **Step 3: Run public-path fault matrix**

Run: `make mission-acceptance`
Expected: success, product failure, auth expiry/resume, transient retry, timeout, cancellation, duplicate confirm, injection and evidence-redaction scenarios pass.

- [ ] **Step 4: Run frontend and API gates**

```bash
pnpm --filter @warmy/web exec prettier --check .
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web test
pnpm --filter @warmy/web exec playwright test tests/e2e/test-mission.spec.ts
pnpm --filter @warmy/web build
make api-check
git diff --check
```

- [ ] **Step 5: Run one approved real target read-only mission**

Require an accessible dedicated account and sufficient quota. Verify Run/RunCase outcomes, Evidence/Artifact hashes, diagnostic citations, regression state, report and joint gate decision. If unavailable, mark the task blocked with exact recovery inputs and do not claim production completion.

- [ ] **Step 6: Commit verification-only fixes and records**

```bash
git add -A
git commit -m "test: verify agent testing trust loop"
```
