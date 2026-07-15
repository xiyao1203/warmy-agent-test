# Repository Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate the confirmed high- and medium-risk security, architecture, maintainability, and performance issues while preserving public product behavior.

**Architecture:** Security invariants move into application services and database constraints; HTTP routers become translation-only adapters; bootstrap code becomes per-module composition; frontend features communicate through public exports and split oversized components by responsibility. Every change is introduced through a failing test, followed by the smallest implementation and a focused verification command.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL/SQLite, Pytest, Next.js 16, React 19, TypeScript 6, Vitest, Playwright, pnpm, uv.

---

## File map

### Backend security and data

- `apps/control-api/migrations/versions/0025_artifact_project_scope.py`: add the Artifact-to-Run composite foreign key.
- `apps/control-api/migrations/versions/0026_login_throttles.py`: add persistent hashed login-throttle buckets.
- `apps/control-api/src/agenttest/modules/artifacts/application/service.py`: upload/list/download use cases and typed errors.
- `apps/control-api/src/agenttest/modules/artifacts/domain/models.py`: stream-oriented storage and scoped repository protocols.
- `apps/control-api/src/agenttest/modules/artifacts/infrastructure/repositories.py`: scoped Run lookup and Artifact persistence.
- `apps/control-api/src/agenttest/modules/artifacts/infrastructure/storage.py`: bounded temporary writes, atomic promotion, streamed reads, safe keys.
- `apps/control-api/src/agenttest/modules/artifacts/api/router.py`: HTTP-only adapter using `ArtifactApiDependencies`.
- `apps/control-api/src/agenttest/modules/identity/application/login_throttle.py`: throttle policy, ports, key hashing, and typed decision.
- `apps/control-api/src/agenttest/modules/identity/application/commands/login.py`: source context and throttle orchestration.
- `apps/control-api/src/agenttest/modules/identity/infrastructure/persistence/models.py`: `LoginThrottleModel`.
- `apps/control-api/src/agenttest/modules/identity/infrastructure/persistence/repositories.py`: atomic persistent throttle repository.
- `apps/control-api/src/agenttest/modules/identity/api/client_ip.py`: trusted-proxy source-address resolution.
- `apps/control-api/src/agenttest/modules/identity/api/router.py`: pass source context without changing public error detail.
- `apps/control-api/src/agenttest/bootstrap/settings.py`: upload limits, throttle policy, and trusted proxy CIDRs.

### Backend architecture

- `apps/control-api/src/agenttest/modules/{browser_profiles,environments,experiments,gates,reviews,runs,scorers,security,test_accounts,test_plans}/application/`: use cases and query ports extracted from routers.
- `apps/control-api/src/agenttest/modules/*/api/*.py`: request/response translation only.
- `apps/control-api/src/agenttest/bootstrap/context.py`: shared session, actor, CSRF, project access, settings, and transaction context.
- `apps/control-api/src/agenttest/bootstrap/modules/*.py`: module-specific composition functions.
- `apps/control-api/src/agenttest/bootstrap/app.py`: middleware plus a declarative router registration list.
- `scripts/check_architecture.py`: backend API and frontend Feature boundary checks.
- `apps/control-api/tests/architecture/test_module_boundaries.py`: executable boundary rules.

### Frontend maintainability and performance

- `apps/web/src/features/{browser-profiles,environments,scorers,gates}/index.ts`: public API exports required by other Features.
- `apps/web/src/features/test-agent/chat-effects.ts`, `chat-timeline.tsx`, `chat-workspace.tsx`: extracted effects and presentation.
- `apps/web/src/features/agents/agent-version-form.ts`, `agent-version-target-section.tsx`, `agent-version-advanced-sections.tsx`: extracted mapping and sections.
- `apps/web/src/features/environments/environment-flow.tsx`, `environment-version-panel.tsx`, `environment-credential-section.tsx`, `environment-editor.tsx`: extracted environment responsibilities.
- `apps/web/src/features/datasets/test-case-form-codecs.ts`, `test-case-editors.tsx`: extracted codecs and editors.
- `scripts/report_web_bundles.mjs`, `scripts/check_web_bundle_budget.mjs`, `apps/web/tests/e2e/performance-budget.spec.ts`: reproducible resource and navigation budgets.
- `docs/performance/web-bundle-baseline.json`, `docs/performance/navigation-baseline.json`: approved starting baselines.

## Spec coverage

| Design requirement                                                                   | Implemented by |
| ------------------------------------------------------------------------------------ | -------------- |
| Artifact scope, bounded streaming, safe names, cleanup, constant-time internal token | Tasks 1-2      |
| Persistent login throttle and trusted proxy handling                                 | Task 3         |
| API/Application/Infrastructure boundary                                              | Tasks 4-5      |
| Modular application composition                                                      | Task 6         |
| Public frontend Feature contracts                                                    | Tasks 5 and 7  |
| Four oversized component decompositions and single stream lifecycle                  | Tasks 8-9      |
| Query, bundle, and navigation budgets                                                | Task 10        |
| Dependency security audit                                                            | Task 11        |
| PostgreSQL, E2E, full verification, documentation, and rollback evidence             | Task 12        |

## Task 1: Enforce Artifact project scope in the database

**Files:**

- Create: `apps/control-api/migrations/versions/0025_artifact_project_scope.py`
- Modify: `apps/control-api/src/agenttest/modules/artifacts/infrastructure/repositories.py`
- Modify: `apps/control-api/tests/integration/test_database_constraints.py`
- Modify: `apps/control-api/tests/integration/test_migrations.py`

- [ ] **Step 1: Write failing database-constraint tests**

Add a PostgreSQL test that inserts two projects, a Run in project A, then attempts to insert an Artifact using project B and the Run from A:

```python
async def test_artifact_run_must_belong_to_same_project(postgres_connection) -> None:
    project_a, project_b, run_id = await seed_scoped_run(postgres_connection)
    with pytest.raises(IntegrityError):
        await postgres_connection.execute(
            text(
                "INSERT INTO artifacts "
                "(id, project_id, run_id, filename, content_type, size_bytes, storage_path) "
                "VALUES (:id, :project_id, :run_id, 'evidence.png', 'image/png', 4, 'aa/file')"
            ),
            {"id": uuid4(), "project_id": project_b, "run_id": run_id},
        )
```

Extend the migration test to assert `0024 -> 0025` preserves a valid Artifact row and rejects a mismatched row.

- [ ] **Step 2: Verify the tests fail for the missing composite constraint**

Run: `uv run pytest apps/control-api/tests/integration/test_database_constraints.py::test_artifact_run_must_belong_to_same_project apps/control-api/tests/integration/test_migrations.py -q`

Expected: the mismatched insert succeeds or the migration revision is missing.

- [ ] **Step 3: Add migration `0025` and align ORM metadata**

Use the existing `uq_runs_project_id` unique constraint as the referenced key:

```python
revision: str = "0025"
down_revision: str | None = "0024"

def upgrade() -> None:
    with op.batch_alter_table("artifacts") as batch:
        batch.create_foreign_key(
            "fk_artifacts_project_run",
            "runs",
            ["project_id", "run_id"],
            ["project_id", "id"],
            ondelete="CASCADE",
        )

def downgrade() -> None:
    with op.batch_alter_table("artifacts") as batch:
        batch.drop_constraint("fk_artifacts_project_run", type_="foreignkey")
```

Add the matching `ForeignKeyConstraint` to `ArtifactModel.__table_args__` and retain the existing direct foreign keys only where SQLite/Alembic requires them for historical compatibility.

- [ ] **Step 4: Verify migration and constraint behavior**

Run: `uv run pytest apps/control-api/tests/integration/test_database_constraints.py apps/control-api/tests/integration/test_migrations.py -q`

Expected: all runnable tests pass; PostgreSQL-only tests either pass with the isolated URL or retain their explicit environment skip.

- [ ] **Step 5: Commit the database invariant**

```bash
git add apps/control-api/migrations/versions/0025_artifact_project_scope.py apps/control-api/src/agenttest/modules/artifacts/infrastructure/repositories.py apps/control-api/tests/integration/test_database_constraints.py apps/control-api/tests/integration/test_migrations.py
git commit -m "fix: enforce artifact project scope"
```

## Task 2: Replace unbounded Artifact I/O with an application service

**Files:**

- Create: `apps/control-api/src/agenttest/modules/artifacts/application/__init__.py`
- Create: `apps/control-api/src/agenttest/modules/artifacts/application/service.py`
- Create: `apps/control-api/tests/unit/artifacts/test_artifact_service.py`
- Create: `apps/control-api/tests/contract/test_artifacts_api.py`
- Modify: `apps/control-api/src/agenttest/modules/artifacts/domain/models.py`
- Modify: `apps/control-api/src/agenttest/modules/artifacts/infrastructure/storage.py`
- Modify: `apps/control-api/src/agenttest/modules/artifacts/infrastructure/repositories.py`
- Modify: `apps/control-api/src/agenttest/modules/artifacts/api/router.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/settings.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`

- [ ] **Step 1: Write failing service tests for bounds, sanitization, scope, and cleanup**

Define test doubles implementing the intended ports and assert the public behavior:

```python
@pytest.mark.asyncio
async def test_upload_rejects_cross_project_run_before_reading_content() -> None:
    source = CountingUpload([b"secret"])
    service = ArtifactService(
        repository=FakeArtifacts(run_in_project=False),
        storage=FakeStorage(),
        user_limit_bytes=64 * MIB,
        internal_limit_bytes=256 * MIB,
    )
    with pytest.raises(ArtifactRunNotFound):
        await service.upload(project_id=P1, run_id=R2, source=source, filename="x.png")
    assert source.read_calls == 0

@pytest.mark.asyncio
async def test_upload_stops_after_configured_limit_and_removes_temporary_object() -> None:
    mib = 1024 * 1024
    storage = FakeStorage()
    service = ArtifactService(FakeArtifacts(True), storage, user_limit_bytes=5 * mib, internal_limit_bytes=8 * mib)
    with pytest.raises(ArtifactTooLarge):
        await service.upload(project_id=P1, run_id=R1, source=CountingUpload([b"a" * (5 * mib), b"b"]), filename="../x.png")
    assert storage.aborted == [storage.temporary_key]
```

Also assert `sanitize_filename("../\x00report.png") == "report.png"`, repository failure aborts the temporary object, and download yields chunks rather than one `bytes` object.

- [ ] **Step 2: Run the unit tests and observe the missing application API**

Run: `uv run pytest apps/control-api/tests/unit/artifacts/test_artifact_service.py -q`

Expected: collection fails because `ArtifactService`, typed errors, and stream ports do not exist.

- [ ] **Step 3: Define stream-oriented domain ports and the minimal service**

Use these stable signatures:

```python
class UploadSource(Protocol):
    async def read(self, size: int) -> bytes: ...

class ArtifactStorage(Protocol):
    async def begin(self, *, filename: str) -> str: ...
    async def append(self, temporary_key: str, chunk: bytes) -> None: ...
    async def commit(self, temporary_key: str) -> str: ...
    async def abort(self, temporary_key: str) -> None: ...
    async def iter_chunks(self, storage_path: str, chunk_size: int) -> AsyncIterator[bytes]: ...

class ArtifactRepository(Protocol):
    async def run_exists(self, *, project_id: UUID, run_id: UUID, run_case_id: UUID | None) -> bool: ...
    async def save(self, artifact: Artifact, *, project_id: UUID) -> None: ...
    async def get(self, artifact_id: ArtifactId, *, project_id: UUID) -> Artifact | None: ...
    async def list_by_run(self, run_id: UUID, *, project_id: UUID) -> list[Artifact]: ...
```

`ArtifactService.upload()` must validate scope first, sanitize the basename, read 64 KiB chunks, update SHA-256 incrementally, enforce the selected user/internal limit, and abort on every exception before re-raising.

Add `artifact_user_upload_max_bytes=67108864` and `artifact_internal_upload_max_bytes=268435456` to `Settings`, both constrained to positive integers.

- [ ] **Step 4: Implement atomic filesystem storage**

Generate server-side keys and never concatenate a user path:

```python
async def begin(self, *, filename: str) -> str:
    key = f"tmp/{uuid4().hex}.upload"
    path = self._resolve(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(mode=0o600, exist_ok=False)
    return key

def _resolve(self, key: str) -> Path:
    candidate = (self._base / key).resolve()
    candidate.relative_to(self._base.resolve())
    return candidate
```

`commit()` derives the final content-addressed key from the completed temporary file and uses `Path.replace()`; `iter_chunks()` reads with `asyncio.to_thread` so the event loop is not blocked by large files.

- [ ] **Step 5: Write failing API contract tests**

Cover authenticated upload, CSRF rejection, cross-project Run rejection, `413 application/problem+json`, internal token rejection, filename sanitization, and streamed download. The API dependency object is:

```python
@dataclass(frozen=True, slots=True)
class ArtifactApiDependencies:
    service: ArtifactService
    actor: Callable[[Request], Awaitable[User]]
    csrf: Callable[[Request], None]
    project_access: Callable[[User, UUID, bool], Awaitable[None]]
    internal_token: str
```

- [ ] **Step 6: Convert the router to a translation-only adapter**

Remove SQLAlchemy, Repository, storage, and session imports. Use `secrets.compare_digest()` for the internal token and map `ArtifactTooLarge` to RFC 7807 status 413, `ArtifactRunNotFound` to 404, and permission failures to 403.

- [ ] **Step 7: Verify Artifact behavior and architecture**

Run: `uv run pytest apps/control-api/tests/unit/artifacts apps/control-api/tests/contract/test_artifacts_api.py apps/control-api/tests/integration/test_database_constraints.py -q`

Expected: all tests pass with no unbounded `await file.read()` in the Artifact router.

- [ ] **Step 8: Commit bounded Artifact handling**

```bash
git add apps/control-api/src/agenttest/modules/artifacts apps/control-api/src/agenttest/bootstrap/settings.py apps/control-api/src/agenttest/bootstrap/app.py apps/control-api/tests/unit/artifacts apps/control-api/tests/contract/test_artifacts_api.py
git commit -m "fix: bound and scope artifact transfers"
```

## Task 3: Add persistent login throttling and trusted-proxy resolution

**Files:**

- Create: `apps/control-api/migrations/versions/0026_login_throttles.py`
- Create: `apps/control-api/src/agenttest/modules/identity/application/login_throttle.py`
- Create: `apps/control-api/src/agenttest/modules/identity/api/client_ip.py`
- Create: `apps/control-api/tests/unit/identity/test_login_throttle.py`
- Create: `apps/control-api/tests/unit/identity/test_client_ip.py`
- Modify: `apps/control-api/src/agenttest/modules/identity/application/commands/login.py`
- Modify: `apps/control-api/src/agenttest/modules/identity/application/ports.py`
- Modify: `apps/control-api/src/agenttest/modules/identity/infrastructure/persistence/models.py`
- Modify: `apps/control-api/src/agenttest/modules/identity/infrastructure/persistence/repositories.py`
- Modify: `apps/control-api/src/agenttest/modules/identity/api/router.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/settings.py`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Modify: `apps/control-api/tests/contract/test_auth_api.py`
- Modify: `apps/control-api/tests/integration/test_migrations.py`

- [ ] **Step 1: Write failing policy tests**

Use a FrozenClock and fake repository to prove the exact policy:

```python
POLICY = LoginThrottlePolicy(window=timedelta(minutes=15), max_failures=8, blocked_for=timedelta(minutes=30))

@pytest.mark.asyncio
async def test_eighth_failure_blocks_without_revealing_account_existence() -> None:
    throttle = LoginThrottle(FakeThrottleRepository(), FrozenClock(NOW), POLICY, pepper=b"test-pepper")
    for _ in range(7):
        assert await throttle.record_failure("user@example.com", "203.0.113.9") is False
    assert await throttle.record_failure("user@example.com", "203.0.113.9") is True
    assert await throttle.is_blocked("user@example.com", "203.0.113.9") is True
```

Also prove window reset, block expiry, successful-login clearing, deterministic HMAC-SHA256 keys, and identical handler errors for known and unknown users.

- [ ] **Step 2: Write failing client-address tests**

```python
def test_forwarded_header_is_ignored_for_untrusted_peer() -> None:
    assert resolve_client_ip("198.51.100.4", "203.0.113.9", ()) == "198.51.100.4"

def test_first_forwarded_address_is_used_for_trusted_peer() -> None:
    trusted = (ip_network("10.0.0.0/8"),)
    assert resolve_client_ip("10.1.2.3", "203.0.113.9, 10.1.2.3", trusted) == "203.0.113.9"
```

Invalid forwarded values fall back to the direct peer rather than producing a 500.

- [ ] **Step 3: Verify both new suites fail**

Run: `uv run pytest apps/control-api/tests/unit/identity/test_login_throttle.py apps/control-api/tests/unit/identity/test_client_ip.py -q`

Expected: missing modules and types.

- [ ] **Step 4: Add the persistent model and migration**

Create `login_throttles` with `key_hash` primary key, `failure_count`, `window_started_at`, `blocked_until`, and `updated_at`; add `ix_login_throttles_updated_at`. No raw email or IP column is permitted.

```python
class LoginThrottleModel(Base):
    __tablename__ = "login_throttles"
    key_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    blocked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
```

- [ ] **Step 5: Implement atomic repository and application policy**

The repository exposes `get`, `record_failure`, `clear`, and `delete_expired(cutoff, limit=100)`. PostgreSQL uses `INSERT .. ON CONFLICT DO UPDATE`; SQLite uses a transactionally equivalent select/update path. The application service creates both account and account-plus-IP HMAC keys and blocks if either bucket is blocked.

Add exact settings `login_throttle_window_seconds=900`, `login_throttle_max_failures=8`, `login_throttle_block_seconds=1800`, `login_throttle_pepper`, and `trusted_proxy_cidrs`. `login_throttle_pepper` is required outside local/test, and `trusted_proxy_cidrs` defaults to an empty tuple.

- [ ] **Step 6: Integrate throttle and source context into login**

Extend the command without storing secrets:

```python
@dataclass(frozen=True, slots=True)
class LoginCommand:
    email: Email
    password: str
    source_ip: str
```

Call `is_blocked()` before password verification, `record_failure()` on every public authentication failure including unknown users, and `clear_success()` only after successful password verification. Always raise `InvalidCredentialsError` for blocked requests.

- [ ] **Step 7: Add API contract and migration coverage**

Verify the eighth failed login and the first blocked retry both return the same 401 title/detail as an ordinary wrong password; ensure `X-Forwarded-For` is ignored by default. Verify `0025 -> 0026`, empty upgrade, index existence, and downgrade.

- [ ] **Step 8: Run identity and security tests**

Run: `uv run pytest apps/control-api/tests/unit/identity apps/control-api/tests/contract/test_auth_api.py apps/control-api/tests/security/test_session_security.py apps/control-api/tests/integration/test_migrations.py -q`

Expected: all runnable tests pass and no response distinguishes unknown, wrong-password, locked, or throttled accounts.

- [ ] **Step 9: Commit login hardening**

```bash
git add apps/control-api/migrations/versions/0026_login_throttles.py apps/control-api/src/agenttest/modules/identity apps/control-api/src/agenttest/bootstrap apps/control-api/tests/unit/identity apps/control-api/tests/contract/test_auth_api.py apps/control-api/tests/integration/test_migrations.py
git commit -m "fix: add persistent login throttling"
```

## Task 4: Move all router persistence into Application services

**Files:**

- Create: `apps/control-api/src/agenttest/modules/environments/application/snapshots.py`
- Create: `apps/control-api/src/agenttest/modules/experiments/application/service.py`
- Create: `apps/control-api/src/agenttest/modules/gates/application/service.py`
- Create: `apps/control-api/src/agenttest/modules/reviews/application/service.py`
- Create: `apps/control-api/src/agenttest/modules/runs/application/comparison.py`
- Create: `apps/control-api/src/agenttest/modules/runs/application/event_stream.py`
- Create: `apps/control-api/src/agenttest/modules/scorers/application/service.py`
- Create: `apps/control-api/src/agenttest/modules/security/application/service.py`
- Create: `apps/control-api/src/agenttest/modules/test_accounts/application/service.py`
- Create: `apps/control-api/src/agenttest/modules/test_plans/application/dry_run.py`
- Modify: `apps/control-api/src/agenttest/modules/browser_profiles/application/auth_state.py`
- Modify: `apps/control-api/src/agenttest/modules/browser_profiles/application/publication.py`
- Modify: `apps/control-api/src/agenttest/modules/browser_profiles/api/router.py`
- Modify: `apps/control-api/src/agenttest/modules/environments/api/snapshots.py`
- Modify: `apps/control-api/src/agenttest/modules/experiments/api/router.py`
- Modify: `apps/control-api/src/agenttest/modules/gates/api/router.py`
- Modify: `apps/control-api/src/agenttest/modules/reviews/api/router.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/api/stream.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/api/trace_diff.py`
- Modify: `apps/control-api/src/agenttest/modules/scorers/api/router.py`
- Modify: `apps/control-api/src/agenttest/modules/security/api/scan_router.py`
- Modify: `apps/control-api/src/agenttest/modules/test_accounts/api/router.py`
- Modify: `apps/control-api/src/agenttest/modules/test_plans/api/dry_run.py`
- Modify: `apps/control-api/src/agenttest/modules/browser_profiles/infrastructure/repository.py`
- Modify: `apps/control-api/src/agenttest/modules/environments/infrastructure/persistence/repositories.py`
- Modify: `apps/control-api/src/agenttest/modules/experiments/infrastructure/persistence/repositories.py`
- Modify: `apps/control-api/src/agenttest/modules/gates/infrastructure/persistence/repositories.py`
- Modify: `apps/control-api/src/agenttest/modules/reviews/infrastructure/persistence/repositories.py`
- Modify: `apps/control-api/src/agenttest/modules/runs/infrastructure/persistence/repositories.py`
- Modify: `apps/control-api/src/agenttest/modules/scorers/infrastructure/persistence/repositories.py`
- Modify: `apps/control-api/src/agenttest/modules/security/infrastructure/repositories.py`
- Modify: `apps/control-api/src/agenttest/modules/test_accounts/infrastructure/persistence/repositories.py`
- Modify: `apps/control-api/src/agenttest/modules/test_plans/infrastructure/persistence/repositories.py`
- Create: `apps/control-api/tests/unit/experiments/test_service.py`
- Create: `apps/control-api/tests/unit/gates/test_service.py`
- Create: `apps/control-api/tests/unit/reviews/test_service.py`
- Create: `apps/control-api/tests/unit/runs/test_comparison.py`
- Create: `apps/control-api/tests/unit/runs/test_event_stream.py`
- Create: `apps/control-api/tests/unit/scorers/test_service.py`
- Create: `apps/control-api/tests/unit/security/test_service.py`
- Create: `apps/control-api/tests/unit/test_accounts/test_service.py`
- Create: `apps/control-api/tests/unit/test_plans/test_dry_run.py`
- Modify: `apps/control-api/tests/unit/environments/test_snapshots.py`

- [ ] **Step 1: Add characterization tests for every affected endpoint**

Before moving code, extend the existing contract suites to lock response fields, status codes, project scoping, and mutation idempotency. Add direct Application tests for the new service signatures:

```python
class ExperimentService(Protocol):
    async def list(self, actor: User, project_id: UUID, limit: int, offset: int) -> list[ExperimentDto]: ...
    async def create(self, actor: User, project_id: UUID, command: CreateExperiment) -> ExperimentDto: ...
    async def compare(self, actor: User, project_id: UUID, experiment_id: UUID) -> ExperimentDto: ...

class RunComparisonService(Protocol):
    async def compare(self, actor: User, project_id: UUID, run_a_id: UUID, run_b_id: UUID) -> RunDiffDto: ...

class RunEventReader(Protocol):
    async def events_after(self, actor: User, project_id: UUID, run_id: UUID, cursor: int) -> list[RunEventDto]: ...
```

Equivalent typed services must cover snapshots, gates, reviews, scorers, security scans, test accounts, and dry-run readiness.

- [ ] **Step 2: Run affected contract tests as a green characterization baseline**

Run: `uv run pytest apps/control-api/tests/contract/test_trace_diff_api.py apps/control-api/tests/contract/test_scorer_trial_api.py apps/control-api/tests/contract/test_test_plan_readiness_api.py apps/control-api/tests/integration/test_experiment_review_chain.py apps/control-api/tests/integration/test_security_asset_chain.py -q`

Expected: existing behavior passes before refactoring.

- [ ] **Step 3: Extract read/query ports and DTOs module by module**

For every module, move SQL statements into an Infrastructure reader implementing an Application Protocol. Every project resource method includes `project_id`:

```python
class RunComparisonReader(Protocol):
    async def get_run(self, project_id: UUID, run_id: UUID) -> RunSummaryDto | None: ...
    async def list_cases(self, project_id: UUID, run_id: UUID) -> tuple[RunCaseSummaryDto, ...]: ...
```

Do not expose SQLAlchemy rows, ORM models, sessions, or `dict[str, Any]` from the new ports.

- [ ] **Step 4: Extract command use cases and transaction boundaries**

Routers call one service method per endpoint. Mutation services own repository calls and the Unit of Work; they return immutable DTOs or raise module-specific Application errors such as `ExperimentNotFound`, `DuplicateBrowserProfile`, and `DryRunAssetMissing`.

- [ ] **Step 5: Replace the 11 remaining router infrastructure imports**

After Task 2 removed Artifact imports, update Browser Profiles, Environment Snapshots, Experiments, Gates, Reviews, Run Stream, Trace Diff, Scorers, Security Scan, Test Accounts, and Test Plan Dry Run. Router factories receive dependency dataclasses, for example:

```python
@dataclass(frozen=True, slots=True)
class TraceDiffApiDependencies:
    compare: RunComparisonService
    actor: Callable[[Request], Awaitable[User]]

def create_trace_diff_router(dependencies: TraceDiffApiDependencies) -> APIRouter:
    router = APIRouter(prefix="/projects/{project_id}/runs/{run_a_id}/diff/{run_b_id}")

    @router.get("")
    async def diff_runs(request: Request, project_id: UUID, run_a_id: UUID, run_b_id: UUID):
        actor = await dependencies.actor(request)
        result = await dependencies.compare.compare(actor, project_id, run_a_id, run_b_id)
        return result.to_dict()

    return router
```

- [ ] **Step 6: Run each module suite after its extraction**

Run: `uv run pytest apps/control-api/tests/unit apps/control-api/tests/contract apps/control-api/tests/integration/test_experiment_review_chain.py apps/control-api/tests/integration/test_security_asset_chain.py -q`

Expected: response contracts and project scoping remain unchanged.

- [ ] **Step 7: Confirm the API tree contains no persistence dependency**

Run: `rg -n 'sqlalchemy|\.infrastructure|session\.(execute|scalar)|SqlAlchemy[A-Za-z]+Repository' apps/control-api/src/agenttest/modules/*/api`

Expected: no matches.

- [ ] **Step 8: Commit the Application-boundary refactor**

```bash
git add apps/control-api/src/agenttest/modules apps/control-api/tests/unit apps/control-api/tests/contract apps/control-api/tests/integration
git commit -m "refactor: move persistence behind application services"
```

## Task 5: Make architecture boundaries executable

**Files:**

- Modify: `scripts/check_architecture.py`
- Modify: `apps/control-api/tests/architecture/test_module_boundaries.py`
- Create: `scripts/check_frontend_boundaries.mjs`
- Create: `apps/web/src/test/architecture/feature-boundaries.test.ts`
- Modify: `Makefile`

- [ ] **Step 1: Add failing scanner fixture tests**

```python
def test_api_cannot_import_infrastructure_or_sqlalchemy(tmp_path: Path) -> None:
    write_module(tmp_path, "agenttest/modules/runs/api/router.py", "from sqlalchemy import text\n")
    assert find_violations(tmp_path) == [
        "agenttest/modules/runs/api/router.py: API imports forbidden dependency sqlalchemy"
    ]

def test_api_cannot_call_session_execute(tmp_path: Path) -> None:
    write_module(tmp_path, "agenttest/modules/runs/api/router.py", "async def f(session):\n    await session.execute('x')\n")
    assert find_violations(tmp_path) == [
        "agenttest/modules/runs/api/router.py: API performs persistence call session.execute"
    ]
```

Add a Node/Vitest fixture proving `features/agents` cannot import `@/features/environments/api`, while `@/features/environments` is accepted.

- [ ] **Step 2: Run scanners and observe fixture failures**

Run: `uv run pytest apps/control-api/tests/architecture/test_module_boundaries.py -q && pnpm --filter @warmy/web exec vitest run src/test/architecture/feature-boundaries.test.ts`

Expected: new cases fail because scanners do not enforce the rules.

- [ ] **Step 3: Extend AST checks and add frontend parser**

The Python scanner checks imports and `ast.Call` attributes for `session.execute`/`session.scalar`. The Node scanner walks production and test `.ts/.tsx` files, determines the source Feature from its path, and rejects another Feature’s path when it contains more than the public package segment.

- [ ] **Step 4: Add both checks to the architecture target**

```make
architecture:
	uv run pytest apps/control-api/tests/architecture -v
	uv run python scripts/check_architecture.py
	pnpm --filter @warmy/web exec vitest run src/test/architecture/feature-boundaries.test.ts
	node scripts/check_frontend_boundaries.mjs
```

- [ ] **Step 5: Verify the repository passes the stronger gates**

Run: `make architecture`

Expected: all checks pass and current-source violations are zero.

- [ ] **Step 6: Commit architecture enforcement**

```bash
git add scripts/check_architecture.py scripts/check_frontend_boundaries.mjs apps/control-api/tests/architecture/test_module_boundaries.py apps/web/src/test/architecture/feature-boundaries.test.ts Makefile
git commit -m "test: enforce application and feature boundaries"
```

## Task 6: Split application composition out of `bootstrap/app.py`

**Files:**

- Create: `apps/control-api/src/agenttest/bootstrap/context.py`
- Create: `apps/control-api/src/agenttest/bootstrap/modules/__init__.py`
- Create: module composition files under `apps/control-api/src/agenttest/bootstrap/modules/`
- Modify: `apps/control-api/src/agenttest/bootstrap/app.py`
- Create: `apps/control-api/tests/unit/bootstrap/test_composition.py`
- Modify: `apps/control-api/tests/contract/test_health.py`

- [ ] **Step 1: Write failing composition-shape tests**

```python
def test_app_module_is_only_top_level_composition() -> None:
    path = Path("apps/control-api/src/agenttest/bootstrap/app.py")
    source = path.read_text(encoding="utf-8")
    assert len(source.splitlines()) <= 350
    assert "session.execute" not in source
    assert "def _register_" not in source

def test_each_module_exposes_one_register_function() -> None:
    for name in EXPECTED_MODULES:
        module = import_module(f"agenttest.bootstrap.modules.{name}")
        assert callable(getattr(module, "register"))
```

- [ ] **Step 2: Verify the shape test fails on the 2251-line file**

Run: `uv run pytest apps/control-api/tests/unit/bootstrap/test_composition.py -q`

Expected: line-count and `_register_` assertions fail.

- [ ] **Step 3: Introduce shared composition context**

```python
@dataclass(frozen=True, slots=True)
class BootstrapContext:
    settings: Settings
    session_factory: async_sessionmaker[AsyncSession]
    auth: AuthApiDependencies
    project_access: ProjectAccessAdapter
    uow_factory: UnitOfWorkFactory

@dataclass(frozen=True, slots=True)
class AppOverrides:
    auth: AuthApiDependencies | None = None
    admin: AdminApiDependencies | None = None
    projects: ProjectApiDependencies | None = None
    audit: AuditApiDependencies | None = None
    agents: AgentApiDependencies | None = None
    datasets: DatasetApiDependencies | None = None
    test_plans: TestPlanApiDependencies | None = None
    environments: EnvironmentApiDependencies | None = None
    runs: RunApiDependencies | None = None
    user_settings: UserSettingsApiDependencies | None = None
    feedback: FeedbackApiDependencies | None = None
```

This object contains wiring dependencies only; no business method belongs on it.

- [ ] **Step 4: Move module wiring without moving behavior**

Create one `register(app: FastAPI, context: BootstrapContext) -> None` per cohesive module group. Each file builds Infrastructure implementations, Application services, and API dependencies, then includes routers. Existing test injection parameters remain supported through a small `AppOverrides` dataclass.

- [ ] **Step 5: Reduce `create_app()` to middleware and registration**

```python
def create_app(settings: Settings | None = None, overrides: AppOverrides | None = None) -> FastAPI:
    context = build_context(settings or get_settings(), overrides or AppOverrides())
    app = build_fastapi(context.settings)
    install_middleware(app, context.settings)
    for register in MODULE_REGISTRARS:
        register(app, context)
    return app
```

- [ ] **Step 6: Run bootstrap, contract, and architecture suites**

Run: `uv run pytest apps/control-api/tests/unit/bootstrap apps/control-api/tests/contract apps/control-api/tests/architecture -q`

Expected: all pass; `bootstrap/app.py` is at most 350 lines and contains no endpoint business logic.

- [ ] **Step 7: Commit composition cleanup**

```bash
git add apps/control-api/src/agenttest/bootstrap apps/control-api/tests/unit/bootstrap apps/control-api/tests/contract/test_health.py
git commit -m "refactor: modularize control api composition"
```

## Task 7: Route all frontend Feature dependencies through public exports

**Files:**

- Modify: `apps/web/src/features/browser-profiles/index.ts`
- Modify: `apps/web/src/features/environments/index.ts`
- Modify: `apps/web/src/features/scorers/index.ts`
- Modify: `apps/web/src/features/gates/index.ts`
- Modify: `apps/web/src/features/agents/agent-version-dialog.tsx`
- Modify: `apps/web/src/features/agents/tests/agent-version-dialog.test.tsx`
- Modify: `apps/web/src/features/test-agent/target-chat-screen.tsx`
- Modify: `apps/web/src/features/test-plans/test-plan-detail-screen.tsx`
- Modify: `apps/web/src/features/test-plans/test-plan-version-dialog.tsx`
- Modify: `apps/web/src/features/test-plans/tests/test-plan-version-dialog.test.tsx`

- [ ] **Step 1: Run the boundary scanner to capture the exact violation list**

Run: `node scripts/check_frontend_boundaries.mjs`

Expected: violations include Agent Version Dialog, Target Chat, and Test Plan consumers importing another Feature’s `/api` path.

- [ ] **Step 2: Export only the required public symbols**

For example:

```typescript
// features/browser-profiles/index.ts
export {
  BrowserProfileList,
  BrowserProfileListScreen,
} from "./browser-profile-list";
export { listBrowserProfiles } from "./api";
export type { BrowserProfile } from "./api";

// features/environments/index.ts
export {
  createCredentialBinding,
  listCredentialBindings,
  listEnvironmentTemplates,
} from "./api";
export type { CredentialBinding } from "./api";
```

- [ ] **Step 3: Replace imports and mocks with public module paths**

Use `@/features/browser-profiles`, `@/features/environments`, `@/features/scorers`, and `@/features/gates`. Update `vi.mock()` paths to match the import path exactly.

- [ ] **Step 4: Verify boundary, type, and affected component tests**

Run: `node scripts/check_frontend_boundaries.mjs && pnpm --filter @warmy/web exec vitest run src/features/agents/tests/agent-version-dialog.test.tsx src/features/test-plans/tests/test-plan-version-dialog.test.tsx && pnpm --filter @warmy/web typecheck`

Expected: no boundary violations and all tests pass.

- [ ] **Step 5: Commit public Feature contracts**

```bash
git add apps/web/src/features
git commit -m "refactor: use public frontend feature contracts"
```

## Task 8: Split Test Agent chat effects and presentation

**Files:**

- Create: `apps/web/src/features/test-agent/chat-effects.ts`
- Create: `apps/web/src/features/test-agent/chat-timeline.tsx`
- Create: `apps/web/src/features/test-agent/chat-workspace.tsx`
- Create: `apps/web/src/features/test-agent/tests/chat-effects.test.ts`
- Modify: `apps/web/src/features/test-agent/chat-screen.tsx`
- Modify: `apps/web/src/features/test-agent/tests/conversation-timeline.test.tsx`
- Modify: `apps/web/src/features/test-agent/tests/session-history.test.tsx`
- Modify: `apps/web/src/features/test-agent/tests/timeline-projection.test.ts`

- [ ] **Step 1: Write failing effect-lifecycle tests**

Extract a controller whose observable contract is one stream per active generation:

```typescript
it("opens one event stream and closes it when generation changes", () => {
  const first = createFakeEventSource();
  const second = createFakeEventSource();
  const controller = createGenerationStreamController(
    () => [first, second].shift()!,
  );
  controller.connect("generation-1", vi.fn());
  controller.connect("generation-1", vi.fn());
  expect(first.openCount).toBe(1);
  controller.connect("generation-2", vi.fn());
  expect(first.close).toHaveBeenCalledOnce();
  expect(second.openCount).toBe(1);
});
```

Also test retry timer cleanup and cursor preservation.

- [ ] **Step 2: Verify the tests fail before extraction**

Run: `pnpm --filter @warmy/web exec vitest run src/features/test-agent/tests/chat-effects.test.ts`

Expected: missing controller module.

- [ ] **Step 3: Extract stream/timer effects and pure timeline helpers**

Move generation subscription and retry scheduling to `chat-effects.ts`; move `buildTaskStates`, relative-date formatting, and message timeline rendering to `chat-timeline.tsx`; move workspace tabs and loading bar to `chat-workspace.tsx`.

- [ ] **Step 4: Keep `TestAgentChat` as the orchestration shell**

It owns reducer state, selected session, input submission, and composition only. Remove the two existing exhaustive-deps suppressions by using stable callbacks and explicit controller lifecycle.

- [ ] **Step 5: Run Test Agent tests, lint, and line-count check**

Run: `pnpm --filter @warmy/web exec vitest run src/features/test-agent && pnpm --filter @warmy/web exec eslint src/features/test-agent && test $(wc -l < apps/web/src/features/test-agent/chat-screen.tsx) -lt 800`

Expected: tests and lint pass; `chat-screen.tsx` is below 800 lines.

- [ ] **Step 6: Commit the chat split**

```bash
git add apps/web/src/features/test-agent
git commit -m "refactor: split test agent chat responsibilities"
```

## Task 9: Split Agent Version, Environment, and Test Case editors

**Files:**

- Create: `apps/web/src/features/agents/agent-version-form.ts`
- Create: `apps/web/src/features/agents/agent-version-target-section.tsx`
- Create: `apps/web/src/features/agents/agent-version-advanced-sections.tsx`
- Modify: `apps/web/src/features/agents/agent-version-dialog.tsx`
- Create: `apps/web/src/features/environments/environment-flow.tsx`
- Create: `apps/web/src/features/environments/environment-version-panel.tsx`
- Create: `apps/web/src/features/environments/environment-credential-section.tsx`
- Create: `apps/web/src/features/environments/environment-editor.tsx`
- Modify: `apps/web/src/features/environments/environment-list.tsx`
- Create: `apps/web/src/features/datasets/test-case-form-codecs.ts`
- Create: `apps/web/src/features/datasets/test-case-editors.tsx`
- Create: `apps/web/src/features/datasets/tests/test-case-form-codecs.test.ts`
- Create: `apps/web/src/features/datasets/tests/test-case-editor.test.tsx`
- Modify: `apps/web/src/features/datasets/test-case-editor.tsx`
- Modify: `apps/web/src/features/agents/tests/agent-version-dialog.test.tsx`
- Modify: `apps/web/src/features/environments/tests/environment-list.test.tsx`

- [ ] **Step 1: Add failing pure-codec tests**

Lock the form transformations before moving them:

```typescript
it("round-trips typed test case values without stringifying booleans", () => {
  const rows = recordToRows({ enabled: true, retries: 2, label: "x" });
  expect(rowsToRecord(rows)).toEqual({ enabled: true, retries: 2, label: "x" });
});

it("builds target config without plaintext login values", () => {
  const payload = buildAgentVersionPayload(formWithCredential("credential-1"));
  expect(JSON.stringify(payload)).not.toContain("secret-password-123");
  expect(payload.config.credential_binding_ids).toEqual(["credential-1"]);
});
```

- [ ] **Step 2: Run codec and existing UI tests**

Run: `pnpm --filter @warmy/web exec vitest run src/features/agents/tests/agent-version-dialog.test.tsx src/features/environments/tests/environment-list.test.tsx src/features/datasets/tests`

Expected: existing tests pass; new codec imports fail until extraction.

- [ ] **Step 3: Extract Agent Version mapping and sections**

Move `asRecord`, value parsers, template selection, default blocked actions, and submit payload construction to `agent-version-form.ts`. Move `TargetSection` and advanced groups to the two section files. Keep the Dialog component responsible for open state, top-level form state, credential save orchestration, and submit.

- [ ] **Step 4: Extract Environment flow, panels, and editor**

Move `FlowCard`, `VersionPanel`, and `CredentialSection` to focused files. Move `KeyValueRow`, codecs, `KeyValueEditor`, and create-template dialog to `environment-editor.tsx`. Keep `EnvironmentList` responsible for list composition and selected template/version IDs.

- [ ] **Step 5: Extract Test Case codecs and editors**

Move all row conversion functions to `test-case-form-codecs.ts` and the four editors plus accessible icon button to `test-case-editors.tsx`. `TestCaseEditor` retains form submission and top-level field layout.

- [ ] **Step 6: Verify behavior, lint, types, and size threshold**

Run: `pnpm --filter @warmy/web test && pnpm --filter @warmy/web lint && pnpm --filter @warmy/web typecheck && test $(wc -l < apps/web/src/features/agents/agent-version-dialog.tsx) -lt 800 && test $(wc -l < apps/web/src/features/environments/environment-list.tsx) -lt 800 && test $(wc -l < apps/web/src/features/datasets/test-case-editor.tsx) -lt 800`

Expected: all checks pass and every original hotspot is below 800 lines.

- [ ] **Step 7: Commit component decomposition**

```bash
git add apps/web/src/features/agents apps/web/src/features/environments apps/web/src/features/datasets
git commit -m "refactor: decompose oversized feature components"
```

## Task 10: Add measurable web and API performance budgets

**Files:**

- Create: `scripts/report_web_bundles.mjs`
- Create: `scripts/check_web_bundle_budget.mjs`
- Create: `scripts/tests/web_bundle_budget.test.mjs`
- Create: `docs/performance/web-bundle-baseline.json`
- Create: `docs/performance/navigation-baseline.json`
- Create: `apps/web/tests/e2e/performance-budget.spec.ts`
- Create: `apps/control-api/tests/performance/test_query_bounds.py`
- Modify: `apps/web/package.json`
- Modify: `Makefile`

- [ ] **Step 1: Write failing bundle-report tests**

The script reads `.next/build-manifest.json`, resolves route chunks, computes raw and gzip bytes, and emits deterministic sorted JSON:

```javascript
assert.deepEqual(report.routes["/login"], {
  gzipBytes: 120,
  rawBytes: 300,
  chunks: ["static/chunks/a.js"],
});
```

Budget checking fails when route gzip bytes exceed baseline by more than 5% or a new synchronous chunk exceeds 256000 gzip bytes.

- [ ] **Step 2: Verify report tests fail before scripts exist**

Run: `node --test scripts/tests/web_bundle_budget.test.mjs`

Expected: missing script/module.

- [ ] **Step 3: Implement report and budget commands**

Add package scripts:

```json
"perf:bundle-report": "node ../../scripts/report_web_bundles.mjs .next",
"perf:bundle-check": "node ../../scripts/check_web_bundle_budget.mjs .next ../../docs/performance/web-bundle-baseline.json"
```

Generate the baseline from the already recorded clean-main build; keep route names `/login`, `/projects`, `/projects/[projectId]/test-agent`, and `/projects/[projectId]/runs`.

- [ ] **Step 4: Add navigation sampling without flaky absolute limits**

The Playwright test records three `performance.getEntriesByType('navigation')` samples per route, uses the median `domInteractive`, and compares candidate values with `docs/performance/navigation-baseline.json`; failure threshold is 10% regression on the same local setup. It must skip with an explicit reason when authenticated services are unavailable.

- [ ] **Step 5: Add query-bound tests**

Instrument the SQLAlchemy engine for Run comparison, Experiment statistics, and project lists; assert fixed query ceilings independent of result count. Example:

```python
assert await count_queries(lambda: service.compare(actor, project_id, run_a, run_b)) <= 4
```

- [ ] **Step 6: Add repeatable Make targets**

```make
performance: build
	pnpm --filter @warmy/web run perf:bundle-check
	uv run pytest apps/control-api/tests/performance -q
```

Keep navigation sampling as `performance-e2e` because it requires running services.

- [ ] **Step 7: Verify budgets**

Run: `make performance`

Expected: bundle and query budgets pass against the committed baseline.

- [ ] **Step 8: Commit performance evidence**

```bash
git add scripts apps/web/package.json apps/web/tests/e2e/performance-budget.spec.ts apps/control-api/tests/performance docs/performance Makefile
git commit -m "perf: add reproducible performance budgets"
```

## Task 11: Add supply-chain audit commands and record findings

**Files:**

- Create: `scripts/audit_dependencies.sh`
- Create: `docs/security/dependency-audit.md`
- Modify: `Makefile`
- Modify: dependency manifests and lockfiles only if a direct vulnerable dependency requires a compatible patch upgrade

- [ ] **Step 1: Create a deterministic audit command**

```bash
#!/usr/bin/env bash
set -euo pipefail
pnpm audit --prod --audit-level high
uv export --all-packages --frozen --no-dev -o /tmp/agenttest-requirements.txt
uvx --from pip-audit pip-audit -r /tmp/agenttest-requirements.txt
```

The script writes no credentials and deletes the temporary export with a trap.

- [ ] **Step 2: Run the audit before dependency changes**

Run: `bash scripts/audit_dependencies.sh`

Expected: exit 0 when no high/critical issue exists; otherwise capture exact package, advisory, installed version, fixed version, and dependency path.

- [ ] **Step 3: Patch compatible direct dependencies only**

Use exact stable versions, regenerate `pnpm-lock.yaml` or `uv.lock`, and run the owning package’s tests. Do not use broad major upgrades or overrides that hide an unresolved transitive advisory.

- [ ] **Step 4: Record the audit**

`docs/security/dependency-audit.md` records date, commands, results, upgrades, remaining advisories, exploitability, mitigation, and review date. The production audit must have zero unmitigated high/critical findings.

- [ ] **Step 5: Add audit target and verify**

```make
security-audit:
	bash scripts/audit_dependencies.sh
```

Run: `make security-audit`

Expected: success or a documented upstream-only advisory whose mitigation is enforced elsewhere and whose audit command is configured not to suppress unrelated failures.

- [ ] **Step 6: Commit supply-chain controls**

```bash
git add scripts/audit_dependencies.sh docs/security/dependency-audit.md Makefile package.json pnpm-lock.yaml pyproject.toml uv.lock
git commit -m "chore: add dependency security audit"
```

## Task 12: Final verification, documentation, and task closure

**Files:**

- Modify: `README.md`
- Modify: `docs/Agent测试平台技术架构与开发规范.md`
- Modify: `docs/当前任务.md`
- Modify: `docs/开发进度与变更记录.md`
- Modify: relevant runbooks if configuration or operations changed

- [ ] **Step 1: Update architecture and operations documentation**

Document Artifact limits/streaming, login throttle settings and trusted proxy behavior, Application-only router boundary, modular bootstrap composition, frontend public Feature imports, performance commands, and dependency audit commands. Correct README’s stale project-stage statement.

- [ ] **Step 2: Run focused security and architecture verification**

Run: `uv run pytest apps/control-api/tests/security apps/control-api/tests/architecture apps/control-api/tests/contract/test_auth_api.py apps/control-api/tests/contract/test_artifacts_api.py -q && make architecture`

Expected: all pass with zero API persistence and cross-Feature boundary violations.

- [ ] **Step 3: Run database verification**

Start the repository PostgreSQL service, create a disposable database, run every PostgreSQL-only gate, and delete it even when a test fails:

```bash
docker compose --env-file infra/compose/.env -f infra/compose/compose.yaml up -d postgresql
db="agenttest_hardening_$(date +%s)"
docker compose --env-file infra/compose/.env -f infra/compose/compose.yaml exec -T postgresql createdb -U agenttest "$db"
export AGENTTEST_TEST_DATABASE_URL="postgresql+asyncpg://agenttest:agenttest-local@localhost:5432/$db"
uv run pytest apps/control-api/tests/integration/test_migrations.py apps/control-api/tests/integration/test_database_constraints.py apps/control-api/tests/integration/projects/test_project_isolation.py apps/control-api/tests/integration/audit/test_audit_logging.py apps/control-api/tests/integration/test_executable_asset_migration.py -q
docker compose --env-file infra/compose/.env -f infra/compose/compose.yaml exec -T postgresql dropdb -U agenttest --if-exists "$db"
unset AGENTTEST_TEST_DATABASE_URL
```

Expected: empty upgrade, historical upgrade, constraints, project isolation, audit, and executable-asset migration tests all execute and pass; the disposable database is removed afterward.

- [ ] **Step 4: Run frontend and performance verification**

Run: `pnpm --filter @warmy/web exec playwright test tests/e2e/login.spec.ts tests/e2e/test-mission.spec.ts tests/e2e/performance-budget.spec.ts && make performance`

Expected: critical E2E and budgets pass; authenticated navigation sampling may only skip with the documented missing-service condition.

- [ ] **Step 5: Run full repository verification**

Run: `make verify && make security-audit && git diff --check`

Expected: all gates pass. Record exact test counts and any environment-conditioned skips.

- [ ] **Step 6: Scan for secrets and review the final diff**

Run: `rg -n '(BEGIN (RSA|OPENSSH|EC) PRIVATE KEY|sk-[A-Za-z0-9]{20,}|Authorization: Bearer [A-Za-z0-9._-]{16,}|password\s*=\s*["'"'][^"'"']+["'"'])' --glob '!*.lock' --glob '!docs/superpowers/plans/*.md' . && git diff --stat && git status --short`

Expected: no real secret match; only intended files are modified.

- [ ] **Step 7: Close the repository task records**

Move `TASK-20260715-001` to completed with actual files, migrations/API/config changes, exact command results, remaining low-risk debt, and next steps. Set `docs/当前任务.md` to no active task while preserving the independent `TASK-20260712-002` external validation note.

- [ ] **Step 8: Commit final documentation**

```bash
git add README.md docs
git commit -m "docs: close repository hardening task"
```

- [ ] **Step 9: Verify the branch is ready for review**

Run: `git status --short --branch && git log --oneline main..HEAD`

Expected: clean branch with focused commits for design, database scope, Artifact security, login throttling, Application boundaries, bootstrap composition, frontend contracts/components, performance, supply chain, and closure documentation.
