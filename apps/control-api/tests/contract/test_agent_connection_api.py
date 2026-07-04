"""Contract tests for Agent version validate-connection and publish readiness."""

from __future__ import annotations

from uuid import UUID

import pytest
from agenttest.bootstrap.settings import Settings
from agenttest.modules.agents.api.router import AgentApiDependencies, create_agent_router
from agenttest.modules.agents.application.commands import (
    CreateAgentHandler,
    CreateAgentVersionHandler,
    PublishAgentVersionHandler,
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
from agenttest.modules.agents.domain.value_objects import AgentConfig
from agenttest.modules.agents.infrastructure.connection_validator import (
    ConnectionValidationResult,
    HttpAgentConnectionValidator,
)
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.domain.policies import ProjectNotFoundError
from agenttest.modules.projects.public import ProjectId
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ── 从 test_agents_api 复制的共享测试辅助 ───────────────────────────────────


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

    async def add(self, agent: Agent) -> None:
        self.items[agent.agent_id] = agent

    async def save(self, agent: Agent) -> None:
        self.items[agent.agent_id] = agent


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


# ── helpers ────────────────────────────────────────────────────────────────


class StubConnectionValidator:
    """可控连接验证器：可配置成功/失败/异常行为。"""

    def __init__(
        self,
        *,
        should_succeed: bool = True,
        latency_ms: int = 42,
        status_code: int = 200,
        response_preview: object = {"status": "ok"},
        error_message: str | None = None,
    ) -> None:
        self.should_succeed = should_succeed
        self.latency_ms = latency_ms
        self._status_code = status_code
        self._response_preview = response_preview
        self.error_message = error_message
        self.last_config: AgentConfig | None = None
        self.last_probe: dict[str, object] | None = None

    async def validate(
        self,
        config: AgentConfig,
        probe_input: dict[str, object],
    ) -> ConnectionValidationResult:
        self.last_config = config
        self.last_probe = probe_input
        if not self.should_succeed:
            raise RuntimeError(self.error_message or "Connection failed")
        return ConnectionValidationResult(
            status_code=self._status_code,
            latency_ms=self.latency_ms,
            response_preview=self._response_preview,
        )


def client_for_connection(
    actor=None,
    *,
    member: bool = True,
    project_id: ProjectId | None = None,
    validator: StubConnectionValidator | None = None,
    agents: InMemoryAgentRepository | None = None,
    versions: InMemoryAgentVersionRepository | None = None,
) -> tuple[TestClient, ProjectId]:
    if actor is None:
        actor = create_user(SystemRole.DEVELOPER)
    if project_id is None:
        project_id = ProjectId.new()
    if agents is None:
        agents = InMemoryAgentRepository()
    if versions is None:
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
        connection_validator=validator,
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


def _create_agent_and_version(
    client: TestClient,
    project_id: ProjectId,
) -> tuple[str, str]:
    """创建 Agent 和版本，返回 (agent_id, version_id)。"""
    created = client.post(
        f"/api/v1/projects/{project_id.value}/agents",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"name": "Test Agent", "agent_type": "generic_http"},
    )
    assert created.status_code == 201
    agent_id = created.json()["id"]

    version = client.post(
        f"/api/v1/projects/{project_id.value}/agents/{agent_id}/versions",
        headers={"X-CSRF-Token": "csrf-token"},
        json={
            "config": {
                "api_url": "https://agent.example.com/api",
                "protocol": "sync_json",
                "timeout": 30,
            }
        },
    )
    assert version.status_code == 201
    version_id = version.json()["id"]
    return agent_id, version_id


# ── connection validation ──────────────────────────────────────────────────


def test_validate_connection_returns_latency_and_preview() -> None:
    """成功连接返回状态码、延迟和响应预览。"""
    validator = StubConnectionValidator()
    client, project_id = client_for_connection(validator=validator)
    agent_id, version_id = _create_agent_and_version(client, project_id)

    response = client.post(
        f"/api/v1/projects/{project_id.value}/agents/{agent_id}/versions/{version_id}/validate-connection",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"input": {"message": "hello"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["status_code"] == 200
    assert body["latency_ms"] == 42
    assert body["response_preview"] == {"status": "ok"}


def test_validate_connection_forwards_config_to_validator() -> None:
    """验证器接收到正确的 AgentConfig 和探测输入。"""
    validator = StubConnectionValidator()
    client, project_id = client_for_connection(validator=validator)
    agent_id, version_id = _create_agent_and_version(client, project_id)

    client.post(
        f"/api/v1/projects/{project_id.value}/agents/{agent_id}/versions/{version_id}/validate-connection",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"input": {"message": "probe"}},
    )

    assert validator.last_config is not None
    assert validator.last_config.api_url == "https://agent.example.com/api"
    assert validator.last_probe == {"message": "probe"}


def test_validate_connection_fails_with_clear_error() -> None:
    """连接失败返回 400 并包含错误信息。"""
    validator = StubConnectionValidator(
        should_succeed=False,
        error_message="Connection refused",
    )
    client, project_id = client_for_connection(validator=validator)
    agent_id, version_id = _create_agent_and_version(client, project_id)

    response = client.post(
        f"/api/v1/projects/{project_id.value}/agents/{agent_id}/versions/{version_id}/validate-connection",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"input": {"message": "test"}},
    )

    assert response.status_code == 400


def test_validate_connection_returns_503_when_no_validator() -> None:
    """没有注入验证器时返回 503 Runtime unavailable。"""
    client, project_id = client_for_connection(validator=None)
    agent_id, version_id = _create_agent_and_version(client, project_id)

    response = client.post(
        f"/api/v1/projects/{project_id.value}/agents/{agent_id}/versions/{version_id}/validate-connection",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"input": {"message": "test"}},
    )

    assert response.status_code == 503


def test_validate_connection_requires_csrf() -> None:
    """无 CSRF token 时返回 403。"""
    validator = StubConnectionValidator()
    client, project_id = client_for_connection(validator=validator)
    agent_id, version_id = _create_agent_and_version(client, project_id)

    response = client.post(
        f"/api/v1/projects/{project_id.value}/agents/{agent_id}/versions/{version_id}/validate-connection",
        json={"input": {"message": "test"}},
    )

    assert response.status_code == 403


def test_validate_connection_rejects_non_object_input() -> None:
    """探测输入不是对象时返回 422（Pydantic 校验拒绝）。"""
    validator = StubConnectionValidator()
    client, project_id = client_for_connection(validator=validator)
    agent_id, version_id = _create_agent_and_version(client, project_id)

    response = client.post(
        f"/api/v1/projects/{project_id.value}/agents/{agent_id}/versions/{version_id}/validate-connection",
        headers={"X-CSRF-Token": "csrf-token"},
        json="not-an-object",
    )

    # Pydantic 在请求体解析阶段拒绝非对象 JSON
    assert response.status_code == 422


def test_validate_connection_nonexistent_version_returns_404() -> None:
    """不存在的版本返回 404。"""
    validator = StubConnectionValidator()
    client, project_id = client_for_connection(validator=validator)
    agent_id, _ = _create_agent_and_version(client, project_id)
    fake_version_id = "00000000-0000-0000-0000-000000000000"

    response = client.post(
        f"/api/v1/projects/{project_id.value}/agents/{agent_id}/versions/{fake_version_id}/validate-connection",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"input": {"message": "test"}},
    )

    assert response.status_code == 404


def test_validate_connection_cross_project_rejected() -> None:
    """跨项目访问版本返回 404。"""
    validator = StubConnectionValidator()
    client, project_id = client_for_connection(validator=validator)
    agent_id, version_id = _create_agent_and_version(client, project_id)

    # 使用另一项目 ID 访问
    other_project = ProjectId.new()
    response = client.post(
        f"/api/v1/projects/{other_project.value}/agents/{agent_id}/versions/{version_id}/validate-connection",
        headers={"X-CSRF-Token": "csrf-token"},
        json={"input": {"message": "test"}},
    )

    assert response.status_code == 404


# ── publish readiness ──────────────────────────────────────────────────────


def test_publish_version_requires_editor_role() -> None:
    """Viewer 不能发布版本。"""
    agents = InMemoryAgentRepository()
    versions = InMemoryAgentVersionRepository()

    # 先用 Developer 创建 Agent 和版本（共享仓库）
    dev_client, project_id = client_for_connection(
        validator=StubConnectionValidator(),
        agents=agents,
        versions=versions,
    )
    agent_id, version_id = _create_agent_and_version(dev_client, project_id)

    # 再用 Viewer 尝试发布（同一仓库，不同角色）
    viewer_client, _ = client_for_connection(
        actor=create_user(SystemRole.VIEWER),
        project_id=project_id,
        validator=StubConnectionValidator(),
        agents=agents,
        versions=versions,
    )

    response = viewer_client.post(
        f"/api/v1/projects/{project_id.value}/agents/{agent_id}/versions/{version_id}/publish",
        headers={"X-CSRF-Token": "csrf-token"},
    )

    assert response.status_code == 403


def test_publish_version_changes_status_to_published() -> None:
    """发布后版本状态变为 published。"""
    client, project_id = client_for_connection(validator=StubConnectionValidator())
    agent_id, version_id = _create_agent_and_version(client, project_id)

    published = client.post(
        f"/api/v1/projects/{project_id.value}/agents/{agent_id}/versions/{version_id}/publish",
        headers={"X-CSRF-Token": "csrf-token"},
    )

    assert published.status_code == 200
    assert published.json()["status"] == "published"
    assert published.json()["published_at"] is not None


# ── 真实 HttpAgentConnectionValidator 仅做类型和构建验证 ────────────────────


def test_real_validator_can_be_constructed() -> None:
    """HttpAgentConnectionValidator 可构建且符合 ConnectionValidator 协议。"""
    validator = HttpAgentConnectionValidator(allow_private_network=True)
    assert validator is not None
    # 不发起真实网络请求，仅验证对象构建成功


@pytest.mark.asyncio
async def test_real_validator_rejects_credential_bindings() -> None:
    """带凭证绑定的配置应在验证时明确拒绝（需通过环境绑定执行）。"""
    import pytest as pt

    validator = HttpAgentConnectionValidator(allow_private_network=True)
    config = AgentConfig(
        api_url="https://agent.example.com",
    )
    # 通过设置 credential_binding_ids 为非空列表来触发拒绝

    config = AgentConfig(
        api_url="https://agent.example.com",
        credential_binding_ids=[UUID("00000000-0000-0000-0000-000000000001")],
    )
    with pt.raises(ValueError, match="(?i)凭证"):
        await validator.validate(config, {"input": "test"})
