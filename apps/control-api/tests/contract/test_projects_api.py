from __future__ import annotations

from uuid import UUID

from agenttest.bootstrap.app import create_app
from agenttest.modules.identity.api.router import AuthApiDependencies
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.api.router import ProjectApiDependencies
from agenttest.modules.projects.application.commands.create_project import (
    CreateProjectHandler,
)
from agenttest.modules.projects.application.commands.manage_members import (
    AddProjectMemberHandler,
    ArchiveProjectHandler,
    RemoveProjectMemberHandler,
    RenameProjectHandler,
    UpdateProjectMemberHandler,
)
from agenttest.modules.projects.application.queries.list_projects import (
    GetProjectHandler,
    ListProjectMembersHandler,
    ListProjectsHandler,
)
from agenttest.modules.projects.domain.entities import (
    Project,
    ProjectId,
    ProjectMemberRole,
)
from fastapi.testclient import TestClient


class InMemoryProjectRepository:
    def __init__(self) -> None:
        self.projects: dict[ProjectId, Project] = {}

    async def get_by_id(self, project_id: ProjectId) -> Project | None:
        return self.projects.get(project_id)

    async def list_for_user(self, user_id: UserId | None) -> list[Project]:
        if user_id is None:
            return list(self.projects.values())
        return [
            project
            for project in self.projects.values()
            if project.member_role(user_id) is not None
        ]

    async def add(self, project: Project) -> None:
        self.projects[project.project_id] = project

    async def save(self, project: Project) -> None:
        self.projects[project.project_id] = project


class StubCurrentUser:
    def __init__(self, actor: User) -> None:
        self.actor = actor

    async def execute(self, _token: str) -> User:
        return self.actor


class StubAuthOperation:
    async def execute(self, *_args: object) -> None:
        return None


def create_user(role: SystemRole, email: str) -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email(email),
        display_name=email.split("@")[0],
        role=role,
    )


def project_dependencies(repository: InMemoryProjectRepository) -> ProjectApiDependencies:
    return ProjectApiDependencies(
        list_projects=ListProjectsHandler(projects=repository),
        get_project=GetProjectHandler(projects=repository),
        create_project=CreateProjectHandler(projects=repository),
        rename_project=RenameProjectHandler(projects=repository),
        archive_project=ArchiveProjectHandler(projects=repository),
        list_members=ListProjectMembersHandler(projects=repository),
        add_member=AddProjectMemberHandler(projects=repository),
        update_member=UpdateProjectMemberHandler(projects=repository),
        remove_member=RemoveProjectMemberHandler(projects=repository),
    )


def client_for(
    actor: User,
    repository: InMemoryProjectRepository,
) -> TestClient:
    operation = StubAuthOperation()
    client = TestClient(
        create_app(
            auth_dependencies=AuthApiDependencies(
                login=operation,
                current_user=StubCurrentUser(actor),
                logout=operation,
                csrf=operation,
            ),
            project_dependencies=project_dependencies(repository),
        ),
        base_url="https://testserver",
    )
    client.cookies.set("agenttest_session", "session-token")
    client.cookies.set("agenttest_csrf", "csrf-token")
    return client


def create_project(
    repository: InMemoryProjectRepository,
    *,
    creator: User,
) -> Project:
    project = Project.create(
        project_id=ProjectId.new(),
        name="Project",
        created_by=creator.user_id,
    )
    repository.projects[project.project_id] = project
    return project


def test_super_admin_creates_and_lists_all_projects() -> None:
    admin = create_user(SystemRole.SUPER_ADMIN, "admin@example.com")
    repository = InMemoryProjectRepository()
    client = client_for(admin, repository)

    created = client.post(
        "/api/v1/projects",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"name": "Project A"},
    )
    listed = client.get("/api/v1/projects")

    assert created.status_code == 201
    assert listed.status_code == 200
    assert [item["name"] for item in listed.json()["items"]] == ["Project A"]


def test_project_api_round_trips_professional_metadata() -> None:
    admin = create_user(SystemRole.SUPER_ADMIN, "admin@example.com")
    repository = InMemoryProjectRepository()
    client = client_for(admin, repository)

    created = client.post(
        "/api/v1/projects",
        headers={"X-CSRF-Token": "csrf-token"},
        json={
            "name": "Professional QA",
            "key": "qa-core",
            "description": "Agent regression program",
            "lead_user_id": str(admin.user_id.value),
        },
    )

    assert created.status_code == 201
    body = created.json()
    assert body["key"] == "QA-CORE"
    assert body["description"] == "Agent regression program"
    assert body["lead_user_id"] == str(admin.user_id.value)
    assert body["status"] == "active"
    assert body["created_at"] == body["updated_at"]


def test_normal_user_lists_only_assigned_projects_and_other_project_is_404() -> None:
    admin = create_user(SystemRole.SUPER_ADMIN, "admin@example.com")
    user = create_user(SystemRole.DEVELOPER, "developer@example.com")
    repository = InMemoryProjectRepository()
    assigned = create_project(repository, creator=admin)
    assigned.add_member(user.user_id, role=ProjectMemberRole.DEVELOPER)
    other = create_project(repository, creator=admin)
    client = client_for(user, repository)

    listed = client.get("/api/v1/projects")
    direct = client.get(f"/api/v1/projects/{other.project_id.value}")

    assert [item["id"] for item in listed.json()["items"]] == [str(assigned.project_id.value)]
    assert direct.status_code == 404


def test_removed_member_immediately_loses_direct_access() -> None:
    admin = create_user(SystemRole.SUPER_ADMIN, "admin@example.com")
    member = create_user(SystemRole.TESTER, "tester@example.com")
    repository = InMemoryProjectRepository()
    project = create_project(repository, creator=admin)
    project.add_member(member.user_id, role=ProjectMemberRole.TESTER)

    admin_client = client_for(admin, repository)
    removed = admin_client.delete(
        f"/api/v1/projects/{project.project_id.value}/members/{member.user_id.value}",
        headers={"X-CSRF-Token": "csrf-token"},
    )
    member_client = client_for(member, repository)
    direct = member_client.get(f"/api/v1/projects/{project.project_id.value}")

    assert removed.status_code == 204
    assert direct.status_code == 404


def test_normal_member_cannot_manage_membership() -> None:
    admin = create_user(SystemRole.SUPER_ADMIN, "admin@example.com")
    member = create_user(SystemRole.DEVELOPER, "developer@example.com")
    target_id = UUID("00000000-0000-0000-0000-000000000999")
    repository = InMemoryProjectRepository()
    project = create_project(repository, creator=admin)
    project.add_member(member.user_id, role=ProjectMemberRole.DEVELOPER)
    client = client_for(member, repository)

    response = client.post(
        f"/api/v1/projects/{project.project_id.value}/members",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"user_id": str(target_id), "role": "viewer"},
    )

    assert response.status_code == 403
