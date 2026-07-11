# Browser Profile Auth State Production Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn the existing local JSON browser-profile prototype into a project-scoped, encrypted, restart-safe browser authentication capability that TapNow production runs can redeem through a short-lived internal lease and use in isolated Playwright contexts with complete evidence capture.

**Architecture:** Keep Control API as the business-data and authorization boundary, keep browser processes as local runtime state, and keep Worker database-free. Interactive login uses a persistent per-profile Chromium directory and loopback CDP; login completion exports Storage State, validates the target domain, encrypts it with profile-bound AAD, and persists only the envelope. A Worker Activity redeems the exact immutable snapshot for its RunCase, starts an isolated context, captures artifacts, and never writes runtime cookies back.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, PostgreSQL, AES-GCM, Playwright async/sync CDP, Temporal Python SDK, Pydantic, React/Next.js, TanStack Query, Vitest, pytest.

**Reference:** Lifecycle, loopback CDP, persistent profile, export, lock, and cleanup patterns were reviewed from `xiyao1203/runtest@ac0bfd4d0a81952e05aae837c336b724ade62a7c`. No reference source code is copied; AgentTest retains its own architecture and security model.

---

## Task 1: Establish the database-backed browser profile aggregate

**Files:**

- Create: `apps/control-api/src/agenttest/modules/browser_profiles/domain/entities.py`
- Create: `apps/control-api/src/agenttest/modules/browser_profiles/application/service.py`
- Create: `apps/control-api/src/agenttest/modules/browser_profiles/infrastructure/models.py`
- Create: `apps/control-api/src/agenttest/modules/browser_profiles/infrastructure/repository.py`
- Create: `apps/control-api/migrations/versions/0019_browser_profile_auth_state.py`
- Test: `apps/control-api/tests/unit/browser_profiles/test_browser_profile_domain.py`
- Test: `apps/control-api/tests/integration/test_browser_profile_repository.py`
- Test: `apps/control-api/tests/integration/test_migrations.py`

**Steps:**

1. Add failing domain tests for legal lifecycle transitions, auth-state status, snapshot version increments, project identity, and redacted public projections.
2. Add failing repository tests for CRUD, `(project_id, name)` uniqueness, project-filtered reads, profile lock metadata, and auth-state persistence.
3. Add failing migration assertions for table, foreign key, unique constraint, and required indexes from both an empty database and `0018`.
4. Implement the aggregate, SQLAlchemy model, async repository, and migration without exposing host paths or encrypted data in public projections.
5. Run:

   ```bash
   uv run pytest apps/control-api/tests/unit/browser_profiles/test_browser_profile_domain.py apps/control-api/tests/integration/test_browser_profile_repository.py apps/control-api/tests/integration/test_migrations.py -q
   ```

## Task 2: Encrypt, validate, and version browser authentication snapshots

**Files:**

- Create: `apps/control-api/src/agenttest/modules/browser_profiles/infrastructure/auth_state_cipher.py`
- Create: `apps/control-api/src/agenttest/modules/browser_profiles/application/auth_state.py`
- Test: `apps/control-api/tests/unit/browser_profiles/test_auth_state_cipher.py`
- Test: `apps/control-api/tests/unit/browser_profiles/test_auth_state_service.py`

**Steps:**

1. Add failing tests proving random nonces, no plaintext leakage, AAD binding to both project and profile, tamper rejection, canonical SHA-256 generation, and versioned envelope parsing.
2. Add failing tests that reject empty or wrong-domain snapshots and accept Cookie, LocalStorage, or IndexedDB state for the configured target origin.
3. Implement a dedicated AES-GCM cipher using AAD `agenttest:browser-auth-state:v1:{project_id}:{profile_id}` and canonical compact JSON.
4. Implement the snapshot service that validates, hashes, encrypts, decrypts, and zeroes mutable plaintext buffers where practical.
5. Run:

   ```bash
   uv run pytest apps/control-api/tests/unit/browser_profiles/test_auth_state_cipher.py apps/control-api/tests/unit/browser_profiles/test_auth_state_service.py -q
   ```

## Task 3: Replace JSON CRUD with the repository and harden the browser runtime

**Files:**

- Refactor: `apps/control-api/src/agenttest/modules/browser_profiles/api/router.py`
- Create: `apps/control-api/src/agenttest/modules/browser_profiles/infrastructure/runtime.py`
- Create: `apps/control-api/src/agenttest/modules/browser_profiles/application/legacy_import.py`
- Create: `apps/control-api/src/agenttest/cli/import_browser_profiles.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Test: `apps/control-api/tests/unit/browser_profiles/test_browser_profile_router.py`
- Test: `apps/control-api/tests/unit/browser_profiles/test_browser_profile_runtime.py`
- Test: `apps/control-api/tests/integration/test_browser_profile_api.py`
- Test: `apps/control-api/tests/integration/test_browser_profile_legacy_import.py`

**Steps:**

1. Add failing API tests for authentication, CSRF, project role, project isolation, duplicate names, response redaction, and stable CRUD behavior.
2. Add failing runtime tests for loopback-only CDP, free-port replacement, process reuse, stale-process correction, graceful terminate/kill, Singleton cleanup, and no persistent-directory deletion.
3. Add failing login-complete tests that connect through CDP, export Storage State with IndexedDB, persist an encrypted snapshot, update timestamps, and honor `stop_after_save` only after a successful save.
4. Add failing verify tests that decrypt into a temporary file or in-memory object, launch an isolated context, detect login redirect, update `ready/expired`, and always clean temporary material.
5. Add an explicit idempotent legacy JSON import command; prove list/startup never implicitly writes or imports.
6. Refactor the router to injected application services and return only public metadata (`auth_state_status`, timestamps, runtime status).
7. Run:

   ```bash
   uv run pytest apps/control-api/tests/unit/browser_profiles apps/control-api/tests/integration/test_browser_profile_api.py apps/control-api/tests/integration/test_browser_profile_legacy_import.py -q
   ```

## Task 4: Add scoped Worker leases and immutable execution validation

**Files:**

- Create: `apps/control-api/src/agenttest/modules/browser_profiles/api/lease_router.py`
- Create: `apps/control-api/src/agenttest/modules/browser_profiles/application/leases.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/infrastructure/repository.py`
- Modify: `apps/control-api/src/agenttest/modules/agents/api/router.py`
- Test: `apps/control-api/tests/contract/test_browser_session_lease_api.py`
- Test: `apps/control-api/tests/integration/test_run_execution_snapshot.py`
- Test: `apps/control-api/tests/unit/agents/test_agent_version_phase1.py`

**Steps:**

1. Add failing contract tests for internal token, Run/RunCase/project/profile scope, immutable snapshot profile/version/hash match, missing/expired state, and response redaction.
2. Add failing run snapshot tests ensuring only profile ID, auth-state version, and hash enter run source/history.
3. Add failing Agent-version tests that allow draft save but reject publication or execution when a browser-profile strategy has no same-project ready profile.
4. Implement the lease service/router and wire it through bootstrap without allowing the Worker to access ORM or encrypted envelopes.
5. Run:

   ```bash
   uv run pytest apps/control-api/tests/contract/test_browser_session_lease_api.py apps/control-api/tests/integration/test_run_execution_snapshot.py apps/control-api/tests/unit/agents/test_agent_version_phase1.py -q
   ```

## Task 5: Redeem auth state inside the TapNow Activity and capture production artifacts

**Files:**

- Create: `workers/api-runner/src/agenttest_api_runner/browser_sessions.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/tapnow_activity.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/workflow.py`
- Modify: `workers/api-runner/src/agenttest_api_runner/worker.py`
- Test: `workers/api-runner/tests/test_browser_sessions.py`
- Test: `workers/api-runner/tests/test_tapnow_activity.py`
- Test: `workers/api-runner/tests/test_workflow.py`
- Test: `workers/api-runner/tests/test_tapnow_end_to_end.py`

**Steps:**

1. Add failing client tests for lease URL, internal token, timeout, typed errors, and absence of auth material in exceptions/logging.
2. Extend `TapNowTaskInput` and failing Workflow tests with login strategy and browser-profile snapshot reference only; assert Temporal payloads contain no Cookie, storage state, password, or envelope.
3. Add failing Activity tests for browser-profile versus credential strategies, isolated context injection, authentication-expired classification, cancellation, retry, and cleanup.
4. Add failing artifact tests for final screenshot, video when present, `playwright-trace.zip`, redacted `network-summary.json`, `console-errors.json`, and `canvas.json`, including best-effort upload on failure.
5. Implement tracing, video, console/network collectors, redaction, upload, and memory/temp cleanup; do not write execution cookies back to the profile.
6. Run:

   ```bash
   uv run pytest workers/api-runner/tests/test_browser_sessions.py workers/api-runner/tests/test_tapnow_activity.py workers/api-runner/tests/test_workflow.py workers/api-runner/tests/test_tapnow_end_to_end.py -q
   ```

## Task 6: Correct TapNow completion, confirmation, and target-error semantics

**Files:**

- Modify: `plugins/canvas-agent/src/agenttest_plugin_canvas/tapnow.py`
- Test: `plugins/canvas-agent/tests/test_tapnow_adapter.py`

**Steps:**

1. Add failing tests that `Ask before acting` and confirmation dialogs return `AwaitingConfirmation`, never success.
2. Add failing tests for login redirect, target quota exhaustion, target task failure, explicit completion markers, stable completion, and dangerous-action blocking.
3. Implement typed plugin exceptions/statuses and exact terminal detection while keeping credentials and platform storage outside the plugin.
4. Run:

   ```bash
   uv run pytest plugins/canvas-agent/tests/test_tapnow_adapter.py -q
   ```

## Task 7: Close the browser-profile and Run UX loop

**Files:**

- Modify: `apps/web/src/features/browser-profiles/api.ts`
- Modify: `apps/web/src/features/browser-profiles/browser-profile-list.tsx`
- Modify: `apps/web/src/features/browser-profiles/browser-profile-list-screen.tsx`
- Modify: `apps/web/src/features/agents/agent-version-dialog.tsx`
- Modify: `apps/web/src/features/runs/run-detail.tsx`
- Modify: `apps/web/src/features/runs/run-detail-screen.tsx`
- Test: `apps/web/src/features/browser-profiles/tests/browser-profile-list.test.tsx`
- Test: `apps/web/src/features/agents/tests/agent-version-dialog.test.tsx`
- Test: `apps/web/src/features/runs/tests/run-detail.test.tsx`

**Steps:**

1. Add failing component tests for `missing/ready/expired/error`, start/login/save/verify/stop, pending action states, and actionable failures.
2. Add failing Agent dialog tests for same-project filtering and publication blocking on non-ready state.
3. Add failing Run detail tests for authentication/execution/wait/collection/cleanup stages and distinct expired/confirmation/quota/platform errors plus all artifact entries.
4. Implement the UI using existing design tokens, query invalidation, accessible labels, and no sensitive profile details.
5. Run:

   ```bash
   pnpm --filter @warmy/web exec vitest run src/features/browser-profiles/tests/browser-profile-list.test.tsx src/features/agents/tests/agent-version-dialog.test.tsx src/features/runs/tests/run-detail.test.tsx
   ```

## Task 8: Prove migration, isolation, replay, and a full browser success loop

**Files:**

- Create: `workers/api-runner/tests/fixtures/browser_auth_target.py`
- Extend: `workers/api-runner/tests/test_tapnow_end_to_end.py`
- Modify: `docs/runbooks/tapnow-production-testing.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`

**Steps:**

1. Build a local real HTTP target that performs form login, sets Cookie plus LocalStorage/IndexedDB, restarts the interactive browser, restores in a new context, executes a deterministic Agent task, and exposes completion/confirmation/quota variants.
2. Run the complete success path through real Control API, Worker Activity, artifact uploader, callbacks, and PostgreSQL; assert no auth data in Workflow history, logs, API responses, or artifacts.
3. Run migration checks for empty database and `0018 -> 0019`, then verify constraints/indexes and cross-project denial.
4. Run all quality gates:

   ```bash
   uv run ruff check apps/control-api workers plugins
   uv run mypy apps/control-api/src workers/api-runner/src plugins/canvas-agent/src
   uv run pytest apps/control-api/tests workers/api-runner/tests plugins/canvas-agent/tests -q
   uv run python scripts/check_architecture.py
   make api-check
   pnpm --filter @warmy/web format:check
   pnpm --filter @warmy/web lint
   pnpm --filter @warmy/web typecheck
   pnpm --filter @warmy/web test
   pnpm --filter @warmy/web build
   git diff --check
   ```

5. Execute the real TapNow read-only run when the approved account and quotas are available. Record Run, RunCase, Artifact, score, security, review, and gate IDs. If external access is unavailable, document the exact blocker and keep the task blocked rather than claiming production completion.
6. Update the task ledger with actual files, schema/API/config changes, exact test results, known risks, and next action.

