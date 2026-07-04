"""Contract tests for environment version API endpoints."""

from __future__ import annotations

from uuid import UUID

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
from agenttest.modules.environments.application.versions import (
    CreateEnvironmentVersionHandler,
    EnvironmentVersionRecord,
    GetEnvironmentVersionHandler,
    ListEnvironmentVersionsHandler,
    PublishEnvironmentVersionHandler,
    UpdateEnvironmentVersionHandler,
)
from agenttest.modules.environments.domain.entities import (
    EnvironmentTemplate,
    EnvironmentTemplateId,
)
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ── In-memory repositories ────────────────────────────────────────────────


class InMemoryEnvironmentTemplateRepository:
    def __init__(self) -> None:
        self.items: dict[EnvironmentTemplateId, EnvironmentTemplate] = {}

    async def get_by_id(self, tid: EnvironmentTemplateId) -> EnvironmentTemplate | None:
        return self.items.get(tid)

    async def list_by_project(self, pid: ProjectId, *, limit=50, cursor=None):
        del cursor
        items = [i for i in self.items.values() if i.project_id == pid]
        return items[:limit], None

    async def add(self, template: EnvironmentTemplate) -> None:
        self.items[template.template_id] = template

    async def save(self, template: EnvironmentTemplate) -> None:
        self.items[template.template_id] = template

    async def delete(self, tid: EnvironmentTemplateId) -> None:
        self.items.pop(tid, None)

    async def get_by_id_and_project(
        self, tid: EnvironmentTemplateId, pid: ProjectId
    ) -> EnvironmentTemplate | None:
        tmpl = self.items.get(tid)
        if tmpl and tmpl.project_id == pid:
            return tmpl
        return None


class InMemoryEnvironmentVersionRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, EnvironmentVersionRecord] = {}

    async def get_by_id(self, vid: UUID, pid: ProjectId) -> EnvironmentVersionRecord | None:
        item = self.items.get(vid)
        if item and item.project_id == pid.value:
            return item
        return None

    async def list_by_template(
        self, tid: EnvironmentTemplateId, pid: ProjectId
    ) -> list[EnvironmentVersionRecord]:
        return sorted(
            (
                i
                for i in self.items.values()
                if i.environment_template_id == tid.value and i.project_id == pid.value
            ),
            key=lambda i: i.version_number,
            reverse=True,
        )

    async def get_next_version_number(self, tid: EnvironmentTemplateId, pid: ProjectId) -> int:
        return (
            max(
                (
                    i.version_number
                    for i in self.items.values()
                    if i.environment_template_id == tid.value and i.project_id == pid.value
                ),
                default=0,
            )
            + 1
        )

    async def add(self, version: EnvironmentVersionRecord) -> None:
        self.items[version.id] = version

    async def save(self, version: EnvironmentVersionRecord) -> None:
        self.items[version.id] = version


# ── Stubs ──────────────────────────────────────────────────────────────────


class StubProjectAccess:
    def __init__(self, project_id: ProjectId, *, member: bool = True) -> None:
        self.project_id = project_id
        self.member = member

    async def ensure_member(self, actor: User, pid: ProjectId) -> None:
        del actor
        if not self.member or pid != self.project_id:
            raise ProjectNotFoundError

    async def ensure_editor(self, actor: User, pid: ProjectId) -> None:
        await self.ensure_member(actor, pid)
        if actor.role not in {SystemRole.SUPER_ADMIN, SystemRole.DEVELOPER, SystemRole.TESTER}:
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
        email=Email(f"env-{role.value}@example.com"),
        display_name=role.value,
        role=role,
    )


# ── Test helpers ───────────────────────────────────────────────────────────


def client_with_versions(
    actor: User | None = None,
    *,
    member: bool = True,
    project_id: ProjectId | None = None,
) -> tuple[TestClient, ProjectId, InMemoryEnvironmentVersionRepository]:
    if actor is None:
        actor = create_user(SystemRole.DEVELOPER)
    if project_id is None:
        project_id = ProjectId.new()

    templates = InMemoryEnvironmentTemplateRepository()
    versions = InMemoryEnvironmentVersionRepository()
    access = StubProjectAccess(project_id, member=member)

    deps = EnvironmentApiDependencies(
        list_templates=ListEnvironmentTemplatesHandler(templates=templates, project_access=access),
        get_template=GetEnvironmentTemplateHandler(templates=templates, project_access=access),
        create_template=CreateEnvironmentTemplateHandler(
            templates=templates, project_access=access
        ),
        update_template=UpdateEnvironmentTemplateHandler(
            templates=templates, project_access=access
        ),
        delete_template=DeleteEnvironmentTemplateHandler(
            templates=templates, project_access=access
        ),
        list_versions=ListEnvironmentVersionsHandler(
            versions=versions, templates=templates, project_access=access
        ),
        get_version=GetEnvironmentVersionHandler(
            versions=versions, templates=templates, project_access=access
        ),
        create_version=CreateEnvironmentVersionHandler(
            versions=versions, templates=templates, project_access=access
        ),
        update_version=UpdateEnvironmentVersionHandler(
            versions=versions, templates=templates, project_access=access
        ),
        publish_version=PublishEnvironmentVersionHandler(
            versions=versions, templates=templates, project_access=access
        ),
    )

    app = FastAPI()
    app.include_router(
        create_environment_router(
            deps,
            current_user=StubCurrentUser(actor),
            csrf=StubCsrf(),
            settings=Settings(),
        ),
        prefix="/api/v1",
    )
    client = TestClient(app, base_url="https://testserver")
    client.cookies.set("agenttest_session", "session-token")
    client.cookies.set("agenttest_csrf", "csrf-token")
    return client, project_id, versions


def create_template(client: TestClient, project_id: ProjectId) -> str:
    """Create a template and return its id."""
    csrf = {"X-CSRF-Token": "csrf-token"}
    r = client.post(
        f"/api/v1/projects/{project_id.value}/environment-templates",
        headers=csrf,
        json={"name": "Test Template", "template_type": "blank"},
    )
    assert r.status_code == 201, r.json()
    return r.json()["id"]


# ── Tests ──────────────────────────────────────────────────────────────────


def test_list_versions_empty_by_default() -> None:
    """New template has no versions."""
    client, project_id, _ = client_with_versions()
    template_id = create_template(client, project_id)

    r = client.get(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions"
    )

    assert r.status_code == 200
    assert r.json()["items"] == []


def test_create_version_returns_201_with_draft_status() -> None:
    """Creating a version returns 201 with draft status and version_number=1."""
    client, project_id, _ = client_with_versions()
    template_id = create_template(client, project_id)

    r = client.post(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"config": {"variables": {"NODE_ENV": "staging"}}},
    )

    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "draft"
    assert body["version_number"] == 1
    assert body["config"]["variables"] == {"NODE_ENV": "staging"}


def test_create_and_list_versions() -> None:
    """Create two versions and list them."""
    client, project_id, _ = client_with_versions()
    template_id = create_template(client, project_id)

    csrf = {"X-CSRF-Token": "csrf-token"}
    r1 = client.post(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions",
        headers=csrf,
        json={"config": {"variables": {"A": "1"}}},
    )
    assert r1.status_code == 201
    r2 = client.post(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions",
        headers=csrf,
        json={"config": {"variables": {"B": "2"}}},
    )
    assert r2.status_code == 201

    listed = client.get(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions"
    )

    assert listed.status_code == 200
    items = listed.json()["items"]
    assert len(items) == 2
    assert items[0]["version_number"] == 2
    assert items[1]["version_number"] == 1


def test_get_version_by_id() -> None:
    """Fetch a specific version by ID."""
    client, project_id, _ = client_with_versions()
    template_id = create_template(client, project_id)

    r = client.post(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"config": {"headers": {"X-Custom": "test"}}},
    )
    version_id = r.json()["id"]

    get = client.get(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions/{version_id}"
    )

    assert get.status_code == 200
    assert get.json()["id"] == version_id
    assert get.json()["config"]["headers"] == {"X-Custom": "test"}


def test_update_draft_version() -> None:
    """Update a draft version's config."""
    client, project_id, _ = client_with_versions()
    template_id = create_template(client, project_id)

    r = client.post(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"config": {"variables": {"old": "value"}}},
    )
    version_id = r.json()["id"]

    updated = client.patch(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions/{version_id}",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"config": {"variables": {"new": "value"}}},
    )

    assert updated.status_code == 200
    assert updated.json()["config"]["variables"] == {"new": "value"}


def test_publish_changes_status_and_sets_published_at() -> None:
    """Publishing a draft version makes it immutable with published_at timestamp."""
    client, project_id, _ = client_with_versions()
    template_id = create_template(client, project_id)

    r = client.post(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"config": {"variables": {"env": "prod"}}},
    )
    version_id = r.json()["id"]

    published = client.post(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions/{version_id}/publish",
        headers={"X-CSRF-Token": "csrf-token"},
    )

    assert published.status_code == 200
    body = published.json()
    assert body["status"] == "published"
    assert body["published_at"] is not None


def test_cannot_update_published_version() -> None:
    """Updating a published version returns 400."""
    client, project_id, _ = client_with_versions()
    template_id = create_template(client, project_id)

    r = client.post(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"config": {}},
    )
    version_id = r.json()["id"]

    client.post(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions/{version_id}/publish",
        headers={"X-CSRF-Token": "csrf-token"},
    )

    updated = client.patch(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions/{version_id}",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"config": {"variables": {"should": "fail"}}},
    )

    assert updated.status_code == 400


def test_version_requires_csrf() -> None:
    """Creating a version without CSRF returns 403."""
    client, project_id, _ = client_with_versions()
    template_id = create_template(client, project_id)

    r = client.post(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions",
        json={"config": {}},
    )

    assert r.status_code == 403


def test_viewer_cannot_create_version() -> None:
    """Viewers cannot create versions."""
    # Use a developer to create the template first (viewers can't create templates)
    dev_client, project_id, _ = client_with_versions()
    template_id = create_template(dev_client, project_id)

    # Now test that a viewer cannot create versions
    viewer_client, _, _ = client_with_versions(
        actor=create_user(SystemRole.VIEWER), project_id=project_id
    )

    r = viewer_client.post(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"config": {}},
    )

    assert r.status_code == 403


def test_version_cross_project_isolation() -> None:
    """Accessing version via a different project returns 404."""
    client, project_id, _ = client_with_versions()
    template_id = create_template(client, project_id)

    r = client.post(
        f"/api/v1/projects/{project_id.value}/environment-templates/{template_id}/versions",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"config": {}},
    )
    version_id = r.json()["id"]

    # Access via different project
    other = client.get(
        f"/api/v1/projects/{ProjectId.new().value}/environment-templates/{template_id}/versions/{version_id}"
    )

    assert other.status_code == 404


def test_nonexistent_template_returns_404() -> None:
    """Accessing versions of nonexistent template returns 404."""
    client, project_id, _ = client_with_versions()
    fake_tid = "00000000-0000-0000-0000-000000000000"

    r = client.get(f"/api/v1/projects/{project_id.value}/environment-templates/{fake_tid}/versions")

    assert r.status_code == 404
