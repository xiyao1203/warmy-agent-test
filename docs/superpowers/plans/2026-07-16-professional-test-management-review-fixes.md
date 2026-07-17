# Professional Test Management Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Close every submission-blocking review finding in the professional test management branch without weakening the shared platform contract.

**Architecture:** Keep project scoping at the Test Agent adapter boundary in addition to module membership checks; compile only recursively sanitized snapshots into Runs; preserve unknown professional rule configuration through editable UI rows; represent deterministic browser automation as an explicit typed operation rather than overloading human-readable test data. Trial idempotency uses a canonical request fingerprint plus repository-level unique-conflict recovery, and Project owns the Lead membership invariant.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, PostgreSQL, Temporal, pytest, Next.js 16.2.9, TypeScript, Vitest, Playwright.

---

## File map

- `apps/control-api/src/agenttest/modules/test_agent/adapters/platform.py`: context-project scope guards and trial fallback key.
- `apps/control-api/src/agenttest/modules/datasets/application/contracts.py`: typed browser operation and recursively sanitized immutable snapshot.
- `apps/control-api/src/agenttest/modules/datasets/application/trial_runs.py`: canonical trial fingerprint and race recovery.
- `apps/control-api/src/agenttest/modules/runs/{application,domain,infrastructure}`: repository conflict contract and persistence translation.
- `apps/control-api/src/agenttest/modules/projects/{domain,application}`: Lead/member invariant.
- `workers/api-runner/src/agenttest_api_runner/{contracts,workflow,playwright_activity}.py`: consume explicit browser operations only.
- `apps/web/src/features/datasets/{test-case-form-codecs,test-case-professional-fields,test-case-step-editor}.ts(x)`: lossless rule round trip and typed browser operation editor.
- Existing unit, contract, integration, Worker, Vitest and Playwright suites: regression evidence.

## Task 1: Enforce Test Agent project scope

- [x] Add failing tests where one actor belongs to projects A and B but an A-scoped Agent context passes a B dataset version/case ID to list/get/create/update/validate/mark-ready/trial-run.
- [x] Run the new Test Agent tests and verify each capability currently reaches the delegated Dataset handler.
- [x] Add adapter helpers that resolve version → dataset and case → version → dataset, then compare `dataset.project_id` with `context.project_id` before every Dataset capability.
- [x] Use a project-safe not-found error and build links only after scope validation.
- [x] Run Test Agent unit and architecture tests.

## Task 2: Make professional snapshots recursively secret-safe

- [x] Add failing tests with password, authorization, cookie, API-key and nested token values in input, initial state, step test data, expected outcome and rule configuration.
- [x] Add one recursive sanitizer with exact/suffix sensitive-key matching; remove credential binding values and replace all other sensitive-key values with a redaction marker while preserving references and non-sensitive keys such as `token_usage`.
- [x] Apply the sanitizer to every arbitrary JSON carrier in `build_case_spec_snapshot` and assert Temporal/API projections never contain the literals.
- [x] Make Worker snapshot validation reject any unsanitized sensitive key so externally supplied payloads fail closed.
- [x] Run Dataset, Run and Worker security-focused tests.

## Task 3: Preserve professional rule configuration through the form

- [x] Add a failing Vitest round-trip covering `canvas_schema`, `node_count`, `node_types`, `required_connection`, no-path assertions, scorer config without a name, security policy extensions and step assertions.
- [x] Store each source rule as `raw` on its editable row; merge edited known fields over the raw object and delete only known fields explicitly cleared by the user.
- [x] Ensure newly added rows start with an empty raw object and no existing row is filtered solely because it lacks the simplified UI fields.
- [x] Run professional form, Dataset list and codec tests.

## Task 4: Align browser execution with the platform contract

- [x] Add failing contract/Worker/form tests proving a professional browser step carries an explicit operation `{action,target,value}` and that natural-language `action` is never treated as a Playwright opcode.
- [x] Add `BrowserOperationV1` to `TestStepV1`; require it for ready deterministic browser cases while keeping human-readable action/test-data/expected-result fields.
- [x] Add operation controls to the manual editor and preserve them in form codecs, API responses, snapshots and Agent generation instructions.
- [x] Compile Worker Playwright steps exclusively from `step.operation`; fail closed with a clear readiness/contract error when it is missing.
- [x] Run generated-client sync, Worker protocol tests and the professional Playwright journey.

## Task 5: Make case-trial idempotency request-exact and race-safe

- [x] Add failing unit tests for same key/different target, same key/edited snapshot and two concurrent same-key requests; add an isolated PostgreSQL unique-conflict test.
- [x] Compute a SHA-256 fingerprint over project, case, Agent version, environment and canonical sanitized case snapshot; persist it inside the immutable trial config snapshot.
- [x] Reuse an existing Run only when its fingerprint matches; otherwise return an idempotency conflict.
- [x] Translate only the `(project_id,idempotency_key)` unique violation to a public repository conflict, then refetch and apply the same fingerprint comparison after a concurrent insert.
- [x] Include Agent/environment/case update identity in the Test Agent fallback key while preserving explicit orchestration idempotency keys.
- [x] Run trial, repository, contract and isolated PostgreSQL concurrency tests.

## Task 6: Enforce the Project Lead invariant

- [x] Add failing domain/handler tests for project creation with a non-creator Lead, assigning a non-member Lead and removing the active Lead.
- [x] Make Project creation add a non-creator Lead as a project member; make Lead changes accept only creator/current member; reject removal of the active Lead.
- [x] Verify repository add/save persist the invariant and update contract/integration coverage.
- [x] Run Project unit, contract and PostgreSQL isolation/constraint tests.

## Task 7: Repair migration and PATCH invariants

- [x] Add failing migration tests proving legacy cases without any oracle become `draft`, while oracle-bearing cases become `ready`, including published legacy versions.
- [x] Change the 0027 backfill to derive status from assertions/scorers/security policies; strengthen the project key CHECK for both SQLite and PostgreSQL.
- [x] Add failing PATCH tests for explicit null clearing, rejecting a ready case that loses its oracle and rejecting an empty step-by-step case.
- [x] Merge `UpdateTestCaseRequest.model_fields_set` over the stored case, validate the complete `PlatformTestCaseV1`, and carry an explicit provided-field set into the handler so nullable values can be cleared.
- [x] Run migration, Dataset domain and contract tests.

## Task 8: Bound latest-summary reads by requested resources

- [x] Extend performance fixtures with multiple historical Runs, versions, environment uses and gate decisions for every requested resource.
- [x] Add assertions that summary methods return only one latest row per requested resource while query count stays constant for small and large lists.
- [x] Replace Python-side `seen` scans with SQL window-ranked subqueries for Projects, Agents, Datasets, Plans, Environments, Scorers and Gates.
- [x] Run all Summary contract, Test Agent list and performance tests.

## Task 9: Normalize Test Agent resource results

- [x] Add failing schema tests requiring `resource_ref` on test-case list/get/create/update/mark-ready results.
- [x] Reuse the shared `ResourceReference` builder after project scope validation while retaining existing artifact relations for orchestration compatibility.
- [x] Run Test Agent capability and list-summary tests.

## Task 10: Final verification and records

- [x] Regenerate OpenAPI/client and update PRD, architecture, API/import/runbook documentation for typed browser operations, redaction semantics, exact idempotency and Lead invariants.
- [x] Run `make verify`, isolated PostgreSQL integration, `make performance`, `make security-audit`, and full Playwright.
- [x] Run `git diff --check`, inspect the complete diff, move this task to completed and reset `docs/当前任务.md` to no active task.
- [x] Commit the reviewed working tree on `codex/professional-test-management`; do not push without an explicit user request.

## Task 11: Close final independent-review findings

- [x] Derive formal-plan input, assertions and case spec from one recursively sanitized snapshot; cover camelCase secrets in both Control API and Worker.
- [x] Make formal-plan Run idempotency request-exact and map same-key/different-plan requests to 409.
- [x] Wrap Run/RunCase insertion in a SQLAlchemy nested transaction so a uniqueness race does not poison the route UoW; prove winner recovery with two concurrent PostgreSQL requests.
- [x] Make PostgreSQL professional JSON columns JSONB, add latest-summary compound indexes and prove query bounds with deep Run/Gate history.
- [x] Replace the flaky development E2E server with an isolated production build/start harness and restore five-worker parallelism.
- [x] Sanitize `secret_free_dump`, complete a second independent review with no Important/Minor findings, and rerun every final verification gate.
