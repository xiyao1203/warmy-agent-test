"""项目级大模型配置领域实体。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId

from .value_objects import ModelPurpose, ProviderType, normalize_base_url


@dataclass(frozen=True, slots=True)
class ModelConfigurationId:
    """大模型配置标识。"""

    value: UUID


@dataclass(slots=True)
class ModelConfiguration:
    """项目共享的大模型连接配置。"""

    model_config_id: ModelConfigurationId
    project_id: ProjectId
    name: str
    provider_type: ProviderType
    base_url: str
    model_name: str
    encrypted_api_key: str
    api_key_hint: str
    supports_text: bool
    supports_vision: bool
    enabled: bool
    created_by: UserId
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        project_id: ProjectId,
        name: str,
        provider_type: ProviderType,
        base_url: str,
        model_name: str,
        encrypted_api_key: str,
        api_key_hint: str,
        supports_text: bool,
        supports_vision: bool,
        created_by: UserId,
    ) -> ModelConfiguration:
        """创建满足项目模型配置不变量的实体。"""

        normalized_name = name.strip()
        normalized_model = model_name.strip()
        if not normalized_name:
            raise ValueError("模型配置名称不能为空")
        if not normalized_model:
            raise ValueError("模型名称不能为空")
        if not supports_text:
            raise ValueError("模型配置必须支持文本能力")
        if not encrypted_api_key:
            raise ValueError("模型 API Key 不能为空")
        now = datetime.now(UTC)
        return cls(
            model_config_id=ModelConfigurationId(uuid4()),
            project_id=project_id,
            name=normalized_name,
            provider_type=provider_type,
            base_url=normalize_base_url(base_url),
            model_name=normalized_model,
            encrypted_api_key=encrypted_api_key,
            api_key_hint=api_key_hint,
            supports_text=supports_text,
            supports_vision=supports_vision,
            enabled=True,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def api_key_hint_for(api_key: str) -> str:
        """生成不可用于还原凭证的尾部提示。"""

        return f"...{api_key[-4:]}" if api_key else ""

    def ensure_usable_for(self, purpose: ModelPurpose) -> None:
        """校验模型是否可用于指定项目用途。"""

        if not self.enabled:
            raise ValueError("已停用的模型配置不能用于调用")
        if purpose is ModelPurpose.VISION_JUDGE and not self.supports_vision:
            raise ValueError("视觉裁判默认模型必须支持视觉能力")

    def disable(self) -> None:
        """停用模型配置。"""

        self.enabled = False
        self.updated_at = datetime.now(UTC)

    def update(
        self,
        *,
        name: str | None = None,
        base_url: str | None = None,
        model_name: str | None = None,
        encrypted_api_key: str | None = None,
        api_key_hint: str | None = None,
        supports_vision: bool | None = None,
        enabled: bool | None = None,
    ) -> None:
        """更新可编辑配置，同时保持领域不变量。"""

        if name is not None:
            if not name.strip():
                raise ValueError("模型配置名称不能为空")
            self.name = name.strip()
        if base_url is not None:
            self.base_url = normalize_base_url(base_url)
        if model_name is not None:
            if not model_name.strip():
                raise ValueError("模型名称不能为空")
            self.model_name = model_name.strip()
        if encrypted_api_key is not None:
            self.encrypted_api_key = encrypted_api_key
            self.api_key_hint = api_key_hint or ""
        if supports_vision is not None:
            self.supports_vision = supports_vision
        if enabled is not None:
            self.enabled = enabled
        self.updated_at = datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class ProjectModelDefault:
    """项目某一用途所选的默认模型。"""

    project_id: ProjectId
    purpose: ModelPurpose
    model_config_id: ModelConfigurationId
    updated_by: UserId
    updated_at: datetime
