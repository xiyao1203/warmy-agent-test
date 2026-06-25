from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from agenttest.bootstrap.app import create_app
from agenttest.modules.audit.api.router import AuditApiDependencies
from agenttest.modules.audit.application.ports import AuditEntry
from agenttest.modules.identity.api.router import AuthApiDependencies
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.domain.entities import Project, ProjectId, ProjectMemberRole
from fastapi.testclient import TestClient


class StubCurrentUser:
    def __init__(self, actor: User) -> None:
        self.actor = actor

    async def execute(self, _token: str) -> User:
        return self.actor


class StubAuthOperation:
    async def execute(self, *_args: object) -> None:
        return None


class FakeAuditReader:
    def __init__(self, entries: list[AuditEntry]) -> None:
        self.entries = entries

    async def list_global(self, *, limit: int) -> list[AuditEntry]:
        return self.entries[:limit]

    async def list_project(
        self,
        *,
        project_id: ProjectId,
        limit: int,
    ) -> list[AuditEntry]:
        return [entry for entry in self.entries if entry.project_id == project_id][:limit]


class FakeProjectReader:
    def __init__(self, projects: list[Project]) -> None:
        self.projects = {project.project_id: project for project in projects}

    async def get_by_id(self, project_id: ProjectId) -> Project | None:
        return self.projects.get(project_id)


def create_user(role: SystemRole, email: str) -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email(email),
        display_name=email.split("@")[0],
        role=role,
    )


def create_entry(project_id: ProjectId | None = None) -> AuditEntry:
    return AuditEntry(
        entry_id=uuid4(),
        actor_user_id=UserId.new(),
        action="projects.member.add",
        object_type="project_member",
        object_id=uuid4(),
        project_id=project_id,
        changes={"password": {"after": "[REDACTED]"}},
        source_ip="127.0.0.1",
        created_at=datetime(2026, 6, 25, tzinfo=UTC),
    )


def client_for(
    actor: User,
    *,
    entries: list[AuditEntry],
    projects: list[Project],
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
            audit_dependencies=AuditApiDependencies(
                audits=FakeAuditReader(entries),
                projects=FakeProjectReader(projects),
            ),
        ),
        base_url="https://testserver",
    )
    client.cookies.set("agenttest_session", "session-token")
    return client


def test_super_admin_can_query_global_audit_without_secrets() -> None:
    admin = create_user(SystemRole.SUPER_ADMIN, "admin@example.com")
    response = client_for(admin, entries=[create_entry()], projects=[]).get("/api/v1/system/audit")

    assert response.status_code == 200
    assert response.json()["items"][0]["changes"]["password"]["after"] == "[REDACTED]"


def test_normal_user_cannot_query_global_audit() -> None:
    user = create_user(SystemRole.DEVELOPER, "developer@example.com")
    response = client_for(user, entries=[], projects=[]).get("/api/v1/system/audit")

    assert response.status_code == 403


def test_project_member_can_query_project_audit() -> None:
    user = create_user(SystemRole.TESTER, "tester@example.com")
    project = Project.create(
        project_id=ProjectId.new(),
        name="Project",
        created_by=UserId.new(),
    )
    project.add_member(user.user_id, ProjectMemberRole.TESTER)
    response = client_for(
        user,
        entries=[create_entry(project.project_id)],
        projects=[project],
    ).get(f"/api/v1/projects/{project.project_id.value}/audit")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_non_member_gets_404_for_project_audit() -> None:
    user = create_user(SystemRole.VIEWER, "viewer@example.com")
    project = Project.create(
        project_id=ProjectId.new(),
        name="Project",
        created_by=UserId.new(),
    )
    response = client_for(user, entries=[], projects=[project]).get(
        f"/api/v1/projects/{project.project_id.value}/audit"
    )

    assert response.status_code == 404
