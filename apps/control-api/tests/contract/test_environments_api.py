from __future__ import annotations

from agenttest.bootstrap.app import create_app
from agenttest.bootstrap.settings import Settings
from agenttest.modules.environments.api.router import (
    EnvironmentApiDependencies,
    create_environment_router,
)
from agenttest.modules.environments.application.commands import (
    CreateEnvironmentTemplateHandler,
    DeleteEnvironmentTemplateHandler,
    UpdateEnvironmentTemplateHandler,
)
from agenttest.modules.environments.application.queries import (
    GetEnvironmentTemplateHandler,
    ListEnvironmentTemplatesHandler,
)
from agenttest.modules.environments.domain.entities import (
    EnvironmentTemplate,
    EnvironmentTemplateId,
)
from agenttest.modules.identity.api.router import AuthApiDependencies
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from fastapi import FastAPI
from fastapi.testclient import TestClient


class InMemoryEnvironmentTemplateRepository:
    def __init__(self) -> None:
        self.items: dict[EnvironmentTemplateId, EnvironmentTemplate] = {}

    async def get_by_id(
        self,
        template_id: EnvironmentTemplateId,
    ) -> EnvironmentTemplate | None:
        return self.items.get(template_id)

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[EnvironmentTemplate], str | None]:
        del cursor
        items = [item for item in self.items.values() if item.project_id == project_id]
        return items[:limit], None

    async def add(self, template: EnvironmentTemplate) -> None:
        self.items[template.template_id] = template

    async def save(self, template: EnvironmentTemplate) -> None:
        self.items[template.template_id] = template

    async def delete(self, template_id: EnvironmentTemplateId) -> None:
        self.items.pop(template_id, None)


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
        email=Email(f"environment-{role.value}@example.com"),
        display_name=role.value,
        role=role,
    )


def build_dependencies(
    project_id: ProjectId,
    *,
    member: bool = True,
) -> EnvironmentApiDependencies:
    templates = InMemoryEnvironmentTemplateRepository()
    access = StubProjectAccess(project_id, member=member)
    return EnvironmentApiDependencies(
        list_templates=ListEnvironmentTemplatesHandler(
            templates=templates,
            project_access=access,
        ),
        get_template=GetEnvironmentTemplateHandler(
            templates=templates,
            project_access=access,
        ),
        create_template=CreateEnvironmentTemplateHandler(
            templates=templates,
            project_access=access,
        ),
        update_template=UpdateEnvironmentTemplateHandler(
            templates=templates,
            project_access=access,
        ),
        delete_template=DeleteEnvironmentTemplateHandler(
            templates=templates,
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
        create_environment_router(
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


def test_developer_creates_updates_lists_and_deletes_environment_template() -> None:
    client, project_id = client_for(create_user(SystemRole.DEVELOPER))
    csrf = {"X-CSRF-Token": "csrf-token"}

    created = client.post(
        f"/api/v1/projects/{project_id.value}/environment-templates",
        headers=csrf,
        json={
            "name": "Browser sandbox",
            "template_type": "preset",
            "description": "Streaming agent browser state",
            "config": {"viewport": {"width": 1440, "height": 900}},
        },
    )
    template_id = created.json()["id"]
    updated = client.patch(
        (
            f"/api/v1/projects/{project_id.value}/environment-templates/"
            f"{template_id}"
        ),
        headers=csrf,
        json={"name": "Agent browser sandbox", "config": {"locale": "zh-CN"}},
    )
    listed = client.get(
        f"/api/v1/projects/{project_id.value}/environment-templates"
    )
    deleted = client.delete(
        (
            f"/api/v1/projects/{project_id.value}/environment-templates/"
            f"{template_id}"
        ),
        headers=csrf,
    )
    missing = client.get(
        
            f"/api/v1/projects/{project_id.value}/environment-templates/"
            f"{template_id}"
        
    )

    assert created.status_code == 201
    assert updated.status_code == 200
    assert updated.json()["name"] == "Agent browser sandbox"
    assert updated.json()["config"] == {"locale": "zh-CN"}
    assert [item["name"] for item in listed.json()["items"]] == [
        "Agent browser sandbox"
    ]
    assert deleted.status_code == 204
    assert missing.status_code == 404


def test_environment_template_paths_are_project_isolated() -> None:
    client, project_id = client_for(create_user(SystemRole.TESTER))
    csrf = {"X-CSRF-Token": "csrf-token"}
    template_id = client.post(
        f"/api/v1/projects/{project_id.value}/environment-templates",
        headers=csrf,
        json={"name": "Isolated", "template_type": "blank"},
    ).json()["id"]

    other_project_id = ProjectId.new()
    response = client.get(
        
            f"/api/v1/projects/{other_project_id.value}/environment-templates/"
            f"{template_id}"
        
    )

    assert response.status_code == 404


def test_environment_viewer_non_member_and_csrf_rules() -> None:
    viewer, project_id = client_for(create_user(SystemRole.VIEWER))
    listed = viewer.get(
        f"/api/v1/projects/{project_id.value}/environment-templates"
    )
    forbidden = viewer.post(
        f"/api/v1/projects/{project_id.value}/environment-templates",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"name": "Forbidden", "template_type": "blank"},
    )

    outsider, outsider_project_id = client_for(
        create_user(SystemRole.DEVELOPER),
        member=False,
    )
    hidden = outsider.get(
        f"/api/v1/projects/{outsider_project_id.value}/environment-templates"
    )
    no_csrf = outsider.post(
        f"/api/v1/projects/{outsider_project_id.value}/environment-templates",
        json={"name": "No CSRF", "template_type": "blank"},
    )

    assert listed.status_code == 200
    assert forbidden.status_code == 403
    assert hidden.status_code == 404
    assert no_csrf.status_code == 403


def test_app_factory_registers_environment_router() -> None:
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
        environment_dependencies=build_dependencies(project_id),
    )
    client = TestClient(app, base_url="https://testserver")
    client.cookies.set("agenttest_session", "session-token")

    response = client.get(
        f"/api/v1/projects/{project_id.value}/environment-templates"
    )

    assert response.status_code == 200
