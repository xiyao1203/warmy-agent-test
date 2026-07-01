"""Contract tests for test plan readiness API.

Covers:
- GET readiness returns blocking issues for missing assets
- Observation-only bypasses scorer requirement
- Ready plan returns empty blocking_issues
- Published plan readiness reflects current state
- Non-existent plan/version returns 404
"""

from __future__ import annotations

from uuid import uuid4

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.test_plans.api.router import (
    TestPlanApiDependencies,
    create_test_plan_router,
)
from agenttest.modules.test_plans.application.commands import (
    CreateTestPlanHandler,
    CreateTestPlanVersionHandler,
    PublishTestPlanVersionHandler,
    UpdateTestPlanHandler,
    UpdateTestPlanVersionHandler,
)
from agenttest.modules.test_plans.application.queries import (
    GetTestPlanHandler,
    GetTestPlanVersionHandler,
    ListTestPlansHandler,
    ListTestPlanVersionsHandler,
)
from agenttest.modules.test_plans.domain.entities import (
    TestPlan,
    TestPlanId,
    TestPlanVersion,
    TestPlanVersionId,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ── In-memory test doubles ──────────────────────────────────────────────────


class InMemPlans:
    def __init__(self) -> None:
        self.items: dict[TestPlanId, TestPlan] = {}

    async def get_by_id(self, pid: TestPlanId) -> TestPlan | None:
        return self.items.get(pid)

    async def list_by_project(
        self, pid: ProjectId, *, limit: int = 50, cursor: str | None = None
    ) -> tuple[list[TestPlan], str | None]:
        items = [p for p in self.items.values() if p.project_id == pid]
        return items[:limit], None

    async def add(self, p: TestPlan) -> None:
        self.items[p.test_plan_id] = p

    async def save(self, p: TestPlan) -> None:
        self.items[p.test_plan_id] = p

    async def delete(self, pid: TestPlanId) -> None:
        self.items.pop(pid, None)


class InMemVersions:
    def __init__(self) -> None:
        self.items: dict[TestPlanVersionId, TestPlanVersion] = {}

    async def get_by_id(self, vid: TestPlanVersionId) -> TestPlanVersion | None:
        return self.items.get(vid)

    async def list_by_test_plan(self, pid: TestPlanId) -> list[TestPlanVersion]:
        return [v for v in self.items.values() if v.test_plan_id == pid]

    async def get_next_version_number(self, pid: TestPlanId) -> int:
        versions = await self.list_by_test_plan(pid)
        return max((v.version_number for v in versions), default=0) + 1

    async def add(self, v: TestPlanVersion) -> None:
        self.items[v.version_id] = v

    async def save(self, v: TestPlanVersion) -> None:
        self.items[v.version_id] = v


class StubAccess:
    def __init__(self, pid: ProjectId, *, member: bool = True) -> None:
        self.project_id = pid
        self.member = member

    async def ensure_member(self, _actor: User, pid: ProjectId) -> None:
        if not self.member or pid != self.project_id:
            raise ProjectNotFoundError

    async def ensure_editor(self, actor: User, pid: ProjectId) -> None:
        await self.ensure_member(actor, pid)
        if actor.role not in {SystemRole.SUPER_ADMIN, SystemRole.DEVELOPER, SystemRole.TESTER}:
            raise PermissionError


class StubUser:
    def __init__(self, actor: User) -> None:
        self.actor = actor

    async def execute(self, _token: str) -> User:
        return self.actor


class StubCsrfOp:
    async def execute(self, *_args: object) -> None:
        return None


# ── Helpers ────────────────────────────────────────────────────────────────


def mkuser(role: SystemRole) -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email(f"plan-{role.value}@example.com"),
        display_name=role.value,
        role=role,
    )


def _uow():
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def null_uow():
        yield

    return null_uow


def deps(pid: ProjectId, *, member: bool = True) -> TestPlanApiDependencies:
    plans = InMemPlans()
    versions = InMemVersions()
    ac = StubAccess(pid, member=member)
    return TestPlanApiDependencies(
        list_plans=ListTestPlansHandler(test_plans=plans, project_access=ac),
        get_plan=GetTestPlanHandler(test_plans=plans, project_access=ac),
        create_plan=CreateTestPlanHandler(test_plans=plans, project_access=ac),
        update_plan=UpdateTestPlanHandler(test_plans=plans, project_access=ac),
        list_versions=ListTestPlanVersionsHandler(
            test_plans=plans, versions=versions, project_access=ac
        ),
        get_version=GetTestPlanVersionHandler(
            test_plans=plans, versions=versions, project_access=ac
        ),
        create_version=CreateTestPlanVersionHandler(
            test_plans=plans, versions=versions, project_access=ac
        ),
        update_version=UpdateTestPlanVersionHandler(
            test_plans=plans, versions=versions, project_access=ac
        ),
        publish_version=PublishTestPlanVersionHandler(
            test_plans=plans, versions=versions, project_access=ac
        ),
        uow_factory=_uow(),
    )


def client(actor: User, *, member: bool = True) -> tuple[TestClient, ProjectId]:
    pid = ProjectId.new()
    app = FastAPI()
    app.include_router(
        create_test_plan_router(
            deps(pid, member=member),
            current_user=StubUser(actor),
            csrf=StubCsrfOp(),
            settings=Settings(),
        ),
        prefix="/api/v1",
    )
    c = TestClient(app, base_url="https://testserver")
    c.cookies.set("agenttest_session", "session-token")
    c.cookies.set("agenttest_csrf", "csrf-token")
    return c, pid


def create_plan(c: TestClient, pid: ProjectId, name: str = "My Plan") -> str:
    csrf = {"X-CSRF-Token": "csrf-token"}
    r = c.post(
        f"/api/v1/projects/{pid.value}/test-plans",
        headers=csrf,
        json={"name": name},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def create_version(
    c: TestClient,
    pid: ProjectId,
    plan_id: str,
    *,
    observation_only: bool = False,
) -> str:
    csrf = {"X-CSRF-Token": "csrf-token"}
    r = c.post(
        f"/api/v1/projects/{pid.value}/test-plans/{plan_id}/versions",
        headers=csrf,
        json={
            "config": {
                "observation_only": observation_only,
            },
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


# ── Tests ──────────────────────────────────────────────────────────────────


def test_readiness_missing_agent_and_dataset() -> None:
    """Readiness check returns blocking issues for missing agent and dataset."""
    c, pid = client(mkuser(SystemRole.DEVELOPER))
    plan_id = create_plan(c, pid)
    version_id = create_version(c, pid, plan_id)

    r = c.get(
        f"/api/v1/projects/{pid.value}/test-plans/{plan_id}/versions/{version_id}/readiness"
    )
    assert r.status_code == 200
    body = r.json()
    assert body["ready"] is False
    issues = body["blocking_issues"]
    assert any("Agent" in i for i in issues)
    assert any("数据集" in i for i in issues)


def test_readiness_missing_scorer_when_not_observation_only() -> None:
    """Readiness flags missing scorer when observation_only is disabled."""
    c, pid = client(mkuser(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    plan_id = create_plan(c, pid)

    r = c.post(
        f"/api/v1/projects/{pid.value}/test-plans/{plan_id}/versions",
        headers=csrf,
        json={
            "config": {
                "observation_only": False,
                "scorer_ids": [],
            },
            "agent_version_id": str(uuid4()),
            "dataset_version_id": str(uuid4()),
        },
    )
    assert r.status_code == 201, r.text
    version_id = r.json()["id"]

    resp = c.get(
        f"/api/v1/projects/{pid.value}/test-plans/{plan_id}/versions/{version_id}/readiness"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ready"] is False
    assert any("评分器" in i for i in body["blocking_issues"])


def test_readiness_observation_only_bypasses_scorer() -> None:
    """Observation-only bypasses the scorer requirement."""
    c, pid = client(mkuser(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    plan_id = create_plan(c, pid)

    r = c.post(
        f"/api/v1/projects/{pid.value}/test-plans/{plan_id}/versions",
        headers=csrf,
        json={
            "config": {
                "observation_only": True,
                "scorer_ids": [],
            },
            "agent_version_id": str(uuid4()),
            "dataset_version_id": str(uuid4()),
        },
    )
    assert r.status_code == 201, r.text
    version_id = r.json()["id"]

    resp = c.get(
        f"/api/v1/projects/{pid.value}/test-plans/{plan_id}/versions/{version_id}/readiness"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ready"] is True
    assert body["blocking_issues"] == []


def test_readiness_ready_plan_returns_empty_issues() -> None:
    """A fully configured plan returns ready with no blocking issues."""
    c, pid = client(mkuser(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    plan_id = create_plan(c, pid)

    r = c.post(
        f"/api/v1/projects/{pid.value}/test-plans/{plan_id}/versions",
        headers=csrf,
        json={
            "config": {
                "scorer_ids": [str(uuid4())],
            },
            "agent_version_id": str(uuid4()),
            "dataset_version_id": str(uuid4()),
        },
    )
    assert r.status_code == 201, r.text
    version_id = r.json()["id"]

    resp = c.get(
        f"/api/v1/projects/{pid.value}/test-plans/{plan_id}/versions/{version_id}/readiness"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ready"] is True
    assert body["blocking_issues"] == []


def test_readiness_published_plan_reflects_status() -> None:
    """Readiness for published version includes status field."""
    c, pid = client(mkuser(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    plan_id = create_plan(c, pid)

    r = c.post(
        f"/api/v1/projects/{pid.value}/test-plans/{plan_id}/versions",
        headers=csrf,
        json={
            "config": {
                "scorer_ids": [str(uuid4())],
            },
            "agent_version_id": str(uuid4()),
            "dataset_version_id": str(uuid4()),
        },
    )
    version_id = r.json()["id"]

    # Publish the version
    pub = c.post(
        f"/api/v1/projects/{pid.value}/test-plans/{plan_id}/versions/{version_id}/publish",
        headers=csrf,
    )
    assert pub.status_code == 200, pub.text

    resp = c.get(
        f"/api/v1/projects/{pid.value}/test-plans/{plan_id}/versions/{version_id}/readiness"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ready"] is True
    assert body["status"] == "published"


def test_readiness_nonexistent_plan_returns_404() -> None:
    """Readiness for non-existent plan returns 404."""
    c, pid = client(mkuser(SystemRole.DEVELOPER))
    fake_plan = uuid4()
    fake_version = uuid4()

    r = c.get(
        f"/api/v1/projects/{pid.value}/test-plans/{fake_plan}/versions/{fake_version}/readiness"
    )
    assert r.status_code == 404


def test_readiness_nonexistent_version_returns_404() -> None:
    """Readiness for non-existent version returns 404."""
    c, pid = client(mkuser(SystemRole.DEVELOPER))
    plan_id = create_plan(c, pid)
    fake_version = uuid4()

    r = c.get(
        f"/api/v1/projects/{pid.value}/test-plans/{plan_id}/versions/{fake_version}/readiness"
    )
    assert r.status_code == 404
