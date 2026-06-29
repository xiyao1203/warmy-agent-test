"""项目级大模型配置应用服务。"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId

from ..domain.entities import ModelConfiguration, ModelConfigurationId, ProjectModelDefault
from ..domain.errors import (
    ModelConfigInUseError,
    ModelConfigNotFoundError,
    ModelDefaultMissingError,
)
from ..domain.repositories import ModelConfigRepository
from ..domain.value_objects import ModelPurpose, ProviderType


class ProjectAccess(Protocol):
    """模型配置模块需要的项目授权能力。"""

    async def ensure_member(self, actor: User, project_id: ProjectId) -> None: ...
    async def ensure_editor(self, actor: User, project_id: ProjectId) -> None: ...


class CredentialCipher(Protocol):
    """项目模型凭证加密端口。"""

    def encrypt(self, value: str) -> str: ...


class ModelConfigService:
    """编排模型配置 CRUD、项目授权和默认用途。"""

    def __init__(
        self,
        repository: ModelConfigRepository,
        project_access: ProjectAccess,
        cipher: CredentialCipher,
    ) -> None:
        self._repository = repository
        self._project_access = project_access
        self._cipher = cipher

    async def list_configs(self, actor: User, project_id: ProjectId) -> list[ModelConfiguration]:
        """列出项目模型配置。"""

        await self._project_access.ensure_member(actor, project_id)
        return await self._repository.list_by_project(project_id)

    async def get(
        self, actor: User, project_id: ProjectId, model_config_id: ModelConfigurationId
    ) -> ModelConfiguration:
        """读取项目模型配置，跨项目时同样按不存在处理。"""

        await self._project_access.ensure_member(actor, project_id)
        item = await self._repository.get(project_id, model_config_id)
        if item is None:
            raise ModelConfigNotFoundError
        return item

    async def get_for_execution(
        self,
        actor: User,
        project_id: ProjectId,
        model_config_id: ModelConfigurationId,
    ) -> ModelConfiguration:
        """读取用于产生费用的模型配置并要求项目编辑权限。"""

        await self._project_access.ensure_editor(actor, project_id)
        item = await self._repository.get(project_id, model_config_id)
        if item is None:
            raise ModelConfigNotFoundError
        item.ensure_usable_for(ModelPurpose.TEST_AGENT_CHAT)
        return item

    async def create(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        name: str,
        base_url: str,
        model_name: str,
        api_key: str,
        supports_vision: bool,
    ) -> ModelConfiguration:
        """加密写入新的 OpenAI-Compatible 模型配置。"""

        await self._project_access.ensure_editor(actor, project_id)
        item = ModelConfiguration.create(
            project_id=project_id,
            name=name,
            provider_type=ProviderType.OPENAI_COMPATIBLE,
            base_url=base_url,
            model_name=model_name,
            encrypted_api_key=self._cipher.encrypt(api_key),
            api_key_hint=ModelConfiguration.api_key_hint_for(api_key),
            supports_text=True,
            supports_vision=supports_vision,
            created_by=actor.user_id,
        )
        await self._repository.add(item)
        return item

    async def update(
        self,
        actor: User,
        project_id: ProjectId,
        model_config_id: ModelConfigurationId,
        *,
        name: str | None = None,
        base_url: str | None = None,
        model_name: str | None = None,
        api_key: str | None = None,
        supports_vision: bool | None = None,
        enabled: bool | None = None,
    ) -> ModelConfiguration:
        """更新配置；未提供 API Key 时保留原密文。"""

        await self._project_access.ensure_editor(actor, project_id)
        item = await self._repository.get(project_id, model_config_id)
        if item is None:
            raise ModelConfigNotFoundError
        if enabled is False and await self._repository.is_default(project_id, model_config_id):
            raise ModelConfigInUseError
        item.update(
            name=name,
            base_url=base_url,
            model_name=model_name,
            encrypted_api_key=self._cipher.encrypt(api_key) if api_key else None,
            api_key_hint=ModelConfiguration.api_key_hint_for(api_key or "") if api_key else None,
            supports_vision=supports_vision,
            enabled=enabled,
        )
        await self._repository.save(item)
        return item

    async def delete(
        self, actor: User, project_id: ProjectId, model_config_id: ModelConfigurationId
    ) -> None:
        """删除未被默认用途引用的模型配置。"""

        await self._project_access.ensure_editor(actor, project_id)
        if await self._repository.get(project_id, model_config_id) is None:
            raise ModelConfigNotFoundError
        if await self._repository.is_default(project_id, model_config_id):
            raise ModelConfigInUseError
        await self._repository.delete(project_id, model_config_id)

    async def list_defaults(self, actor: User, project_id: ProjectId) -> list[ProjectModelDefault]:
        """列出项目三类默认模型。"""

        await self._project_access.ensure_member(actor, project_id)
        return await self._repository.list_defaults(project_id)

    async def set_default(
        self,
        actor: User,
        project_id: ProjectId,
        purpose: ModelPurpose,
        model_config_id: ModelConfigurationId,
    ) -> ProjectModelDefault:
        """校验能力后设置项目默认模型。"""

        await self._project_access.ensure_editor(actor, project_id)
        item = await self._repository.get(project_id, model_config_id)
        if item is None:
            raise ModelConfigNotFoundError
        item.ensure_usable_for(purpose)
        value = ProjectModelDefault(
            project_id=project_id,
            purpose=purpose,
            model_config_id=model_config_id,
            updated_by=actor.user_id,
            updated_at=datetime.now(UTC),
        )
        await self._repository.set_default(value)
        return value

    async def resolve_default(
        self,
        actor: User,
        project_id: ProjectId,
        purpose: ModelPurpose,
    ) -> ModelConfiguration:
        """解析项目用途默认模型并校验当前可用性。"""

        await self._project_access.ensure_editor(actor, project_id)
        selected = await self._repository.get_default(project_id, purpose)
        if selected is None:
            raise ModelDefaultMissingError
        item = await self._repository.get(project_id, selected.model_config_id)
        if item is None:
            raise ModelDefaultMissingError
        item.ensure_usable_for(purpose)
        return item
