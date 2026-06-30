"""项目模型配置 API 契约测试。"""

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.model_configs.api.router import create_model_config_router
from agenttest.modules.model_configs.application.ports import (
    InvocationResult,
    ModelRuntimeUnavailableError,
)
from agenttest.modules.model_configs.application.service import ModelConfigService
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from fastapi import FastAPI
from fastapi.testclient import TestClient


class MemoryRepo:
    def __init__(self) -> None:
        self.items = {}
        self.defaults = {}

    async def list_by_project(self, project_id):
        return [item for item in self.items.values() if item.project_id == project_id]

    async def get(self, project_id, model_config_id):
        item = self.items.get(model_config_id)
        return item if item and item.project_id == project_id else None

    async def add(self, item):
        self.items[item.model_config_id] = item

    async def save(self, item):
        self.items[item.model_config_id] = item

    async def delete(self, project_id, model_config_id):
        self.items.pop(model_config_id, None)

    async def list_defaults(self, project_id):
        return [value for key, value in self.defaults.items() if key[0] == project_id]

    async def get_default(self, project_id, purpose):
        return self.defaults.get((project_id, purpose))

    async def set_default(self, value):
        self.defaults[(value.project_id, value.purpose)] = value

    async def is_default(self, project_id, model_config_id):
        return any(
            value.model_config_id == model_config_id
            for value in await self.list_defaults(project_id)
        )


class Cipher:
    def encrypt(self, value: str) -> str:
        return f"encrypted:{value}"


class Invoker:
    async def invoke(self, config, messages, **kwargs):
        return InvocationResult(content="ok", latency_ms=42, total_tokens=1)


class UnavailableInvoker:
    async def invoke(self, config, messages, **kwargs):
        raise ModelRuntimeUnavailableError("部署未配置 Model Runner")


class Access:
    def __init__(self, project_id: ProjectId) -> None:
        self.project_id = project_id

    async def ensure_member(self, actor, project_id):
        if project_id != self.project_id:
            raise ProjectNotFoundError

    async def ensure_editor(self, actor, project_id):
        await self.ensure_member(actor, project_id)
        if actor.role is SystemRole.VIEWER:
            raise PermissionError


class CurrentUser:
    def __init__(self, value: User) -> None:
        self.value = value

    async def execute(self, token: str) -> User:
        return self.value


class Csrf:
    async def execute(self, token: str, csrf: str) -> None:
        return None


def client_for(
    role: SystemRole = SystemRole.DEVELOPER,
    *,
    invoker=None,
) -> tuple[TestClient, ProjectId]:
    project_id = ProjectId.new()
    actor = User.create(
        user_id=UserId.new(),
        email=Email("model@example.com"),
        display_name="Model User",
        role=role,
    )
    service = ModelConfigService(MemoryRepo(), Access(project_id), Cipher())
    app = FastAPI()
    app.include_router(
        create_model_config_router(
            service=service,
            invoker=invoker or Invoker(),
            current_user=CurrentUser(actor),
            csrf=Csrf(),
            settings=Settings(),
        ),
        prefix="/api/v1",
    )
    client = TestClient(app, base_url="https://testserver")
    client.cookies.set("agenttest_session", "session")
    client.cookies.set("agenttest_csrf", "csrf")
    return client, project_id


def create_model(client: TestClient, project_id: ProjectId):
    return client.post(
        f"/api/v1/projects/{project_id.value}/model-configs",
        headers={"X-CSRF-Token": "csrf"},
        json={
            "name": "主模型",
            "base_url": "https://api.example.com/v1",
            "model_name": "model-a",
            "api_key": "sk-production-secret",
            "supports_vision": True,
        },
    )


def test_crud_never_returns_plaintext_or_ciphertext() -> None:
    client, project_id = client_for()
    created = create_model(client, project_id)
    model_id = created.json()["id"]
    listed = client.get(f"/api/v1/projects/{project_id.value}/model-configs")
    updated = client.patch(
        f"/api/v1/projects/{project_id.value}/model-configs/{model_id}",
        headers={"X-CSRF-Token": "csrf"},
        json={"name": "更新模型"},
    )
    body = f"{created.text}{listed.text}{updated.text}"
    assert created.status_code == 201
    assert updated.json()["name"] == "更新模型"
    assert "sk-production-secret" not in body
    assert "encrypted:" not in body
    assert created.json()["has_api_key"] is True
    assert created.json()["api_key_hint"] == "...cret"


def test_sets_three_project_defaults_and_enforces_csrf() -> None:
    client, project_id = client_for()
    model_id = create_model(client, project_id).json()["id"]
    missing_csrf = client.put(
        f"/api/v1/projects/{project_id.value}/model-defaults/text_judge",
        json={"model_config_id": model_id},
    )
    selected = client.put(
        f"/api/v1/projects/{project_id.value}/model-defaults/vision_judge",
        headers={"X-CSRF-Token": "csrf"},
        json={"model_config_id": model_id},
    )
    defaults = client.get(f"/api/v1/projects/{project_id.value}/model-defaults")
    assert missing_csrf.status_code == 403
    assert selected.status_code == 200
    assert defaults.json()["items"][0]["purpose"] == "vision_judge"


def test_cross_project_is_hidden_and_viewer_cannot_write() -> None:
    client, project_id = client_for(SystemRole.VIEWER)
    forbidden = create_model(client, project_id)
    hidden = client.get(f"/api/v1/projects/{ProjectId.new().value}/model-configs")
    assert forbidden.status_code == 403
    assert hidden.status_code == 404


def test_connection_check_uses_real_invocation_port() -> None:
    client, project_id = client_for()
    model_id = create_model(client, project_id).json()["id"]
    response = client.post(
        f"/api/v1/projects/{project_id.value}/model-configs/{model_id}/test-connection",
        headers={"X-CSRF-Token": "csrf"},
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True, "latency_ms": 42, "total_tokens": 1}


def test_connection_check_exposes_safe_runtime_configuration_error() -> None:
    client, project_id = client_for(invoker=UnavailableInvoker())
    model_id = create_model(client, project_id).json()["id"]

    response = client.post(
        f"/api/v1/projects/{project_id.value}/model-configs/{model_id}/test-connection",
        headers={"X-CSRF-Token": "csrf"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "部署未配置 Model Runner"
