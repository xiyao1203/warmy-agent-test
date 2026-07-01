from __future__ import annotations

from uuid import uuid4

from agenttest.bootstrap.app import create_app
from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.api.router import AuthApiDependencies
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.test_plans.api.router import (
    TestPlanApiDependencies as PlanApiDependencies,
)
from agenttest.modules.test_plans.api.router import (
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
    TestPlan as Plan,
)
from agenttest.modules.test_plans.domain.entities import (
    TestPlanId as PlanId,
)
from agenttest.modules.test_plans.domain.entities import (
    TestPlanVersion as PlanVersion,
)
from agenttest.modules.test_plans.domain.entities import (
    TestPlanVersionId as PlanVersionId,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


class InMemoryTestPlanRepository:
    def __init__(self) -> None:
        self.items: dict[PlanId, Plan] = {}

    async def get_by_id(self, test_plan_id: PlanId) -> Plan | None:
        return self.items.get(test_plan_id)

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Plan], str | None]:
        del cursor
        items = [item for item in self.items.values() if item.project_id == project_id]
        return items[:limit], None

    async def add(self, test_plan: Plan) -> None:
        self.items[test_plan.test_plan_id] = test_plan

    async def save(self, test_plan: Plan) -> None:
        self.items[test_plan.test_plan_id] = test_plan


class InMemoryTestPlanVersionRepository:
    def __init__(self) -> None:
        self.items: dict[PlanVersionId, PlanVersion] = {}

    async def get_by_id(self, version_id: PlanVersionId) -> PlanVersion | None:
        return self.items.get(version_id)

    async def list_by_test_plan(self, test_plan_id: PlanId) -> list[PlanVersion]:
        return [item for item in self.items.values() if item.test_plan_id == test_plan_id]

    async def get_next_version_number(self, test_plan_id: PlanId) -> int:
        versions = await self.list_by_test_plan(test_plan_id)
        return max((item.version_number for item in versions), default=0) + 1

    async def add(self, version: PlanVersion) -> None:
        self.items[version.version_id] = version

    async def save(self, version: PlanVersion) -> None:
        self.items[version.version_id] = version


class StubProjectAccess:
    def __init__(self, project_id: ProjectId, *, member: bool = True) -> None:
        self.project_id = project_id
        self.member = member

    async def ensure_member(self, actor: User, project_id: ProjectId) -> None:
        del actor
        if not self.member or project_id != self.project_id:
            raise ProjectNotFoundError

    async def ensure_editor(self, actor: User, project_id: ProjectId) -> None:
        await self.ensure_member(actor, project_id)
        if actor.role not in {
            SystemRole.SUPER_ADMIN,
            SystemRole.DEVELOPER,
            SystemRole.TESTER,
        }:
            raise PermissionError


class StubCurrentUser:
    def __init__(self, actor: User) -> None:
        self.actor = actor

    async def execute(self, _token: str) -> User:
        return self.actor


class StubCsrf:
    async def execute(self, *_args: object) -> None:
        return None


def create_user(role: SystemRole) -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email(f"plan-{role.value}@example.com"),
        display_name=role.value,
        role=role,
    )


def build_dependencies(
    project_id: ProjectId,
    *,
    member: bool = True,
) -> PlanApiDependencies:
    plans = InMemoryTestPlanRepository()
    versions = InMemoryTestPlanVersionRepository()
    access = StubProjectAccess(project_id, member=member)
    return PlanApiDependencies(
        list_plans=ListTestPlansHandler(test_plans=plans, project_access=access),
        get_plan=GetTestPlanHandler(test_plans=plans, project_access=access),
        create_plan=CreateTestPlanHandler(test_plans=plans, project_access=access),
        update_plan=UpdateTestPlanHandler(test_plans=plans, project_access=access),
        list_versions=ListTestPlanVersionsHandler(
            test_plans=plans,
            versions=versions,
            project_access=access,
        ),
        get_version=GetTestPlanVersionHandler(
            test_plans=plans,
            versions=versions,
            project_access=access,
        ),
        create_version=CreateTestPlanVersionHandler(
            test_plans=plans,
            versions=versions,
            project_access=access,
        ),
        update_version=UpdateTestPlanVersionHandler(
            test_plans=plans,
            versions=versions,
            project_access=access,
        ),
        publish_version=PublishTestPlanVersionHandler(
            test_plans=plans,
            versions=versions,
            project_access=access,
        ),
    )


def client_for(
    actor: User,
    *,
    member: bool = True,
) -> tuple[TestClient, ProjectId]:
    project_id = ProjectId.new()
    app = FastAPI()
    app.include_router(
        create_test_plan_router(
            build_dependencies(project_id, member=member),
            current_user=StubCurrentUser(actor),
            csrf=StubCsrf(),
            settings=Settings(),
        ),
        prefix="/api/v1",
    )
    client = TestClient(app, base_url="https://testserver")
    client.cookies.set("agenttest_session", "session-token")
    client.cookies.set("agenttest_csrf", "csrf-token")
    return client, project_id


def test_developer_creates_updates_and_publishes_test_plan_version() -> None:
    client, project_id = client_for(create_user(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    created = client.post(
        f"/api/v1/projects/{project_id.value}/test-plans",
        headers=csrf,
        json={"name": "Release gate"},
    )
    plan_id = created.json()["id"]
    version = client.post(
        f"/api/v1/projects/{project_id.value}/test-plans/{plan_id}/versions",
        headers=csrf,
        json={
            "agent_version_id": str(uuid4()),
            "dataset_version_id": str(uuid4()),
            "config": {
                "runs_per_case": 2,
                "concurrency": 4,
                "timeout": 120,
                "pass_threshold": 0.9,
                "observation_only": True,
            },
        },
    )
    version_id = version.json()["id"]
    updated = client.patch(
        (f"/api/v1/projects/{project_id.value}/test-plans/{plan_id}/versions/{version_id}"),
        headers=csrf,
        json={
            "config": {
                "concurrency": 8,
                "timeout": 180,
                "observation_only": True,
            }
        },
    )
    published = client.post(
        (f"/api/v1/projects/{project_id.value}/test-plans/{plan_id}/versions/{version_id}/publish"),
        headers=csrf,
    )
    immutable = client.patch(
        (f"/api/v1/projects/{project_id.value}/test-plans/{plan_id}/versions/{version_id}"),
        headers=csrf,
        json={"config": {"concurrency": 1}},
    )

    assert created.status_code == 201
    assert version.status_code == 201
    assert updated.status_code == 200
    assert updated.json()["config"]["concurrency"] == 8
    assert published.json()["status"] == "published"
    assert immutable.status_code == 409


def test_test_plan_viewer_non_member_and_csrf_rules() -> None:
    viewer, project_id = client_for(create_user(SystemRole.VIEWER))
    assert viewer.get(f"/api/v1/projects/{project_id.value}/test-plans").status_code == 200
    assert (
        viewer.post(
            f"/api/v1/projects/{project_id.value}/test-plans",
            headers={"X-CSRF-Token": "csrf-token"},
            json={"name": "Forbidden"},
        ).status_code
        == 403
    )

    outsider, outsider_project_id = client_for(
        create_user(SystemRole.DEVELOPER),
        member=False,
    )
    assert (
        outsider.get(f"/api/v1/projects/{outsider_project_id.value}/test-plans").status_code == 404
    )
    assert (
        outsider.post(
            f"/api/v1/projects/{outsider_project_id.value}/test-plans",
            json={"name": "No CSRF"},
        ).status_code
        == 403
    )


def test_app_factory_registers_test_plans_router() -> None:
    actor = create_user(SystemRole.DEVELOPER)
    project_id = ProjectId.new()
    operation = StubCsrf()
    app = create_app(
        auth_dependencies=AuthApiDependencies(
            login=operation,
            current_user=StubCurrentUser(actor),
            logout=operation,
            csrf=operation,
        ),
        test_plan_dependencies=build_dependencies(project_id),
    )
    client = TestClient(app, base_url="https://testserver")
    client.cookies.set("agenttest_session", "session-token")

    response = client.get(f"/api/v1/projects/{project_id.value}/test-plans")

    assert response.status_code == 200
