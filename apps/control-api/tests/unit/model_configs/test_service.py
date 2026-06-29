"""模型配置应用服务测试。"""

from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.model_configs.application.service import ModelConfigService
from agenttest.modules.model_configs.domain.errors import ModelConfigInUseError
from agenttest.modules.model_configs.domain.value_objects import ModelPurpose
from agenttest.modules.projects.public import ProjectId


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


class Access:
    async def ensure_member(self, actor, project_id):
        return None

    async def ensure_editor(self, actor, project_id):
        return None


class Cipher:
    def encrypt(self, value: str) -> str:
        return f"encrypted:{value}"


def actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("developer@example.com"),
        display_name="Developer",
        role=SystemRole.DEVELOPER,
    )


@pytest.mark.asyncio
async def test_create_encrypts_key_and_only_keeps_hint() -> None:
    repo = MemoryRepo()
    service = ModelConfigService(repo, Access(), Cipher())
    project_id = ProjectId(uuid4())

    item = await service.create(
        actor(),
        project_id,
        name="主模型",
        base_url="https://api.example.com/v1",
        model_name="model-a",
        api_key="sk-production-secret",
        supports_vision=False,
    )

    assert item.encrypted_api_key == "encrypted:sk-production-secret"
    assert item.api_key_hint == "...cret"


@pytest.mark.asyncio
async def test_update_without_key_retains_existing_ciphertext() -> None:
    repo = MemoryRepo()
    service = ModelConfigService(repo, Access(), Cipher())
    project_id = ProjectId(uuid4())
    item = await service.create(
        actor(),
        project_id,
        name="主模型",
        base_url="https://api.example.com/v1",
        model_name="model-a",
        api_key="sk-original",
        supports_vision=False,
    )

    updated = await service.update(
        actor(),
        project_id,
        item.model_config_id,
        name="新名称",
        api_key=None,
    )
    assert updated.name == "新名称"
    assert updated.encrypted_api_key == "encrypted:sk-original"


@pytest.mark.asyncio
async def test_vision_default_rejects_text_only_model() -> None:
    repo = MemoryRepo()
    service = ModelConfigService(repo, Access(), Cipher())
    project_id = ProjectId(uuid4())
    item = await service.create(
        actor(),
        project_id,
        name="文本",
        base_url="https://api.example.com/v1",
        model_name="text",
        api_key="sk-key",
        supports_vision=False,
    )
    with pytest.raises(ValueError, match="视觉"):
        await service.set_default(
            actor(),
            project_id,
            ModelPurpose.VISION_JUDGE,
            item.model_config_id,
        )


@pytest.mark.asyncio
async def test_cannot_delete_model_referenced_by_default() -> None:
    repo = MemoryRepo()
    service = ModelConfigService(repo, Access(), Cipher())
    project_id = ProjectId(uuid4())
    item = await service.create(
        actor(),
        project_id,
        name="文本",
        base_url="https://api.example.com/v1",
        model_name="text",
        api_key="sk-key",
        supports_vision=False,
    )
    await service.set_default(
        actor(),
        project_id,
        ModelPurpose.TEXT_JUDGE,
        item.model_config_id,
    )
    with pytest.raises(ModelConfigInUseError):
        await service.delete(actor(), project_id, item.model_config_id)
