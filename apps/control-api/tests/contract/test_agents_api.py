from __future__ import annotations

from agenttest.bootstrap.app import create_app
from agenttest.bootstrap.settings import Settings
from agenttest.modules.agents.api.router import AgentApiDependencies, create_agent_router
from agenttest.modules.agents.application.commands import (
    CreateAgentHandler,
    CreateAgentVersionHandler,
    DeleteAgentHandler,
    PublishAgentVersionHandler,
    SetBaselineAgentVersionHandler,
    SetCurrentAgentVersionHandler,
    UpdateAgentHandler,
    UpdateAgentVersionHandler,
)
from agenttest.modules.agents.application.queries import (
    GetAgentHandler,
    GetAgentVersionHandler,
    ListAgentsHandler,
    ListAgentVersionsHandler,
)
from agenttest.modules.agents.domain.entities import (
    Agent,
    AgentId,
    AgentVersion,
    AgentVersionId,
)
from agenttest.modules.identity.api.router import AuthApiDependencies
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.domain.policies import ProjectNotFoundError
from agenttest.modules.projects.public import ProjectId
from agenttest.shared.application.pagination import PageRequest, PageResult
from fastapi import FastAPI
from fastapi.testclient import TestClient


class InMemoryAgentRepository:
    def __init__(self) -> None:
        self.items: dict[AgentId, Agent] = {}

    async def get_by_id(self, agent_id: AgentId) -> Agent | None:
        return self.items.get(agent_id)

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Agent], str | None]:
        del cursor
        items = [item for item in self.items.values() if item.project_id == project_id]
        return items[:limit], None

    async def list_page_by_project(
        self,
        project_id: ProjectId,
        page_request: PageRequest,
    ) -> PageResult[Agent]:
        items = [item for item in self.items.values() if item.project_id == project_id]
        start = page_request.offset
        return PageResult(
            items=items[start : start + page_request.page_size],
            total=len(items),
            page=page_request.page,
            page_size=page_request.page_size,
        )

    async def count_by_project(self, project_id: ProjectId) -> int:
        return sum(item.project_id == project_id for item in self.items.values())

    async def add(self, agent: Agent) -> None:
        self.items[agent.agent_id] = agent

    async def save(self, agent: Agent) -> None:
        self.items[agent.agent_id] = agent

    async def delete(self, agent_id: AgentId) -> None:
        self.items.pop(agent_id, None)


class InMemoryAgentVersionRepository:
    def __init__(self) -> None:
        self.items: dict[AgentVersionId, AgentVersion] = {}

    async def get_by_id(self, version_id: AgentVersionId) -> AgentVersion | None:
        return self.items.get(version_id)

    async def list_by_agent(self, agent_id: AgentId) -> list[AgentVersion]:
        return [item for item in self.items.values() if item.agent_id == agent_id]

    async def get_next_version_number(self, agent_id: AgentId) -> int:
        versions = await self.list_by_agent(agent_id)
        return max((item.version_number for item in versions), default=0) + 1

    async def add(self, version: AgentVersion) -> None:
        self.items[version.version_id] = version

    async def save(self, version: AgentVersion) -> None:
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
        email=Email(f"{role.value}@example.com"),
        display_name=role.value,
        role=role,
    )


def client_for(
    actor: User,
    *,
    member: bool = True,
) -> tuple[TestClient, ProjectId]:
    project_id = ProjectId.new()
    agents = InMemoryAgentRepository()
    versions = InMemoryAgentVersionRepository()
    access = StubProjectAccess(project_id, member=member)
    dependencies = AgentApiDependencies(
        list_agents=ListAgentsHandler(agents=agents, project_access=access),
        get_agent=GetAgentHandler(agents=agents, project_access=access),
        create_agent=CreateAgentHandler(agents=agents, project_access=access),
        update_agent=UpdateAgentHandler(agents=agents, project_access=access),
        list_versions=ListAgentVersionsHandler(
            agents=agents,
            versions=versions,
            project_access=access,
        ),
        get_version=GetAgentVersionHandler(
            agents=agents,
            versions=versions,
            project_access=access,
        ),
        create_version=CreateAgentVersionHandler(
            agents=agents,
            versions=versions,
            project_access=access,
        ),
        update_version=UpdateAgentVersionHandler(
            agents=agents,
            versions=versions,
            project_access=access,
        ),
        publish_version=PublishAgentVersionHandler(
            agents=agents,
            versions=versions,
            project_access=access,
        ),
        set_current_version=SetCurrentAgentVersionHandler(
            agents=agents, versions=versions, project_access=access
        ),
        set_baseline_version=SetBaselineAgentVersionHandler(
            agents=agents, versions=versions, project_access=access
        ),
        delete_agent=DeleteAgentHandler(agents=agents, versions=versions, project_access=access),
    )
    app = FastAPI()
    app.include_router(
        create_agent_router(
            dependencies,
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


def test_developer_creates_lists_and_publishes_agent_version() -> None:
    client, project_id = client_for(create_user(SystemRole.DEVELOPER))

    created = client.post(
        f"/api/v1/projects/{project_id.value}/agents",
        headers={"X-CSRF-Token": "csrf-token"},
        json={
            "name": "Support Agent",
            "agent_type": "generic_http",
            "description": "Customer support",
        },
    )
    agent_id = created.json()["id"]
    version = client.post(
        f"/api/v1/projects/{project_id.value}/agents/{agent_id}/versions",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"config": {"api_url": "https://agent.example.com", "timeout": 30}},
    )
    version_id = version.json()["id"]
    published = client.post(
        (f"/api/v1/projects/{project_id.value}/agents/{agent_id}/versions/{version_id}/publish"),
        headers={"X-CSRF-Token": "csrf-token"},
    )
    current = client.get(f"/api/v1/projects/{project_id.value}/agents/{agent_id}")
    baseline = client.patch(
        f"/api/v1/projects/{project_id.value}/agents/{agent_id}/baseline-version",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"version_id": version_id},
    )
    listed = client.get(f"/api/v1/projects/{project_id.value}/agents")

    assert created.status_code == 201
    assert version.status_code == 201
    assert published.status_code == 200
    assert published.json()["status"] == "published"
    assert current.json()["current_version_id"] == version_id
    assert baseline.status_code == 200
    assert baseline.json()["baseline_version_id"] == version_id
    assert [item["name"] for item in listed.json()["items"]] == ["Support Agent"]


def test_agent_delete_requires_no_versions() -> None:
    client, project_id = client_for(create_user(SystemRole.DEVELOPER))
    created = client.post(
        f"/api/v1/projects/{project_id.value}/agents",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"name": "Disposable", "agent_type": "generic_http"},
    )
    agent_id = created.json()["id"]

    deleted = client.delete(
        f"/api/v1/projects/{project_id.value}/agents/{agent_id}",
        headers={"X-CSRF-Token": "csrf-token"},
    )

    assert deleted.status_code == 204
    assert client.get(f"/api/v1/projects/{project_id.value}/agents/{agent_id}").status_code == 404


def test_viewer_can_read_but_cannot_create_agent() -> None:
    client, project_id = client_for(create_user(SystemRole.VIEWER))

    listed = client.get(f"/api/v1/projects/{project_id.value}/agents")
    created = client.post(
        f"/api/v1/projects/{project_id.value}/agents",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"name": "Forbidden", "agent_type": "generic_http"},
    )

    assert listed.status_code == 200
    assert created.status_code == 403


def test_agent_list_supports_numbered_page_mode() -> None:
    client, project_id = client_for(create_user(SystemRole.DEVELOPER))
    for index in range(12):
        response = client.post(
            f"/api/v1/projects/{project_id.value}/agents",
            headers={"X-CSRF-Token": "csrf-token"},
            json={"name": f"Agent {index:02d}", "agent_type": "generic_http"},
        )
        assert response.status_code == 201

    response = client.get(
        f"/api/v1/projects/{project_id.value}/agents",
        params={"page": 2, "page_size": 10},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": response.json()["items"],
        "next_cursor": None,
        "total": 12,
        "page": 2,
        "page_size": 10,
        "total_pages": 2,
    }
    assert len(response.json()["items"]) == 2


def test_non_member_gets_404_and_mutation_requires_csrf() -> None:
    client, project_id = client_for(create_user(SystemRole.DEVELOPER), member=False)

    listed = client.get(f"/api/v1/projects/{project_id.value}/agents")
    no_csrf = client.post(
        f"/api/v1/projects/{project_id.value}/agents",
        json={"name": "No CSRF", "agent_type": "generic_http"},
    )

    assert listed.status_code == 404
    assert no_csrf.status_code == 403


def test_app_factory_registers_agents_router() -> None:
    actor = create_user(SystemRole.DEVELOPER)
    project_id = ProjectId.new()
    agents = InMemoryAgentRepository()
    versions = InMemoryAgentVersionRepository()
    access = StubProjectAccess(project_id)
    dependencies = AgentApiDependencies(
        list_agents=ListAgentsHandler(agents=agents, project_access=access),
        get_agent=GetAgentHandler(agents=agents, project_access=access),
        create_agent=CreateAgentHandler(agents=agents, project_access=access),
        update_agent=UpdateAgentHandler(agents=agents, project_access=access),
        list_versions=ListAgentVersionsHandler(
            agents=agents, versions=versions, project_access=access
        ),
        get_version=GetAgentVersionHandler(agents=agents, versions=versions, project_access=access),
        create_version=CreateAgentVersionHandler(
            agents=agents, versions=versions, project_access=access
        ),
        update_version=UpdateAgentVersionHandler(
            agents=agents, versions=versions, project_access=access
        ),
        publish_version=PublishAgentVersionHandler(
            agents=agents, versions=versions, project_access=access
        ),
        set_current_version=SetCurrentAgentVersionHandler(
            agents=agents, versions=versions, project_access=access
        ),
        set_baseline_version=SetBaselineAgentVersionHandler(
            agents=agents, versions=versions, project_access=access
        ),
        delete_agent=DeleteAgentHandler(agents=agents, versions=versions, project_access=access),
    )
    operation = StubCsrf()
    app = create_app(
        auth_dependencies=AuthApiDependencies(
            login=operation,
            current_user=StubCurrentUser(actor),
            logout=operation,
            csrf=operation,
        ),
        agent_dependencies=dependencies,
    )
    client = TestClient(app, base_url="https://testserver")
    client.cookies.set("agenttest_session", "session-token")

    response = client.get(f"/api/v1/projects/{project_id.value}/agents")

    assert response.status_code == 200
