"""Environment 领域实体。

定义环境模板实体 EnvironmentTemplate，
支持 blank（空）和 preset（预设）两种类型。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from agenttest.modules.environments.domain.value_objects import TemplateType
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId


@dataclass(frozen=True, slots=True)
class EnvironmentTemplateId:
    """环境模板实体的唯一标识。"""
    value: UUID

    @classmethod
    def new(cls) -> EnvironmentTemplateId:
        return cls(uuid4())


@dataclass(slots=True)
class EnvironmentTemplate:
    """环境模板实体。

    定义测试执行时的环境配置，包括初始状态、Mock 服务和
    测试账号等。支持两种类型：
    - BLANK：空环境，无预设配置。
    - PRESET：预设环境，包含预定义配置。

    Attributes:
        template_id: 模板唯一标识。
        project_id: 所属项目 ID。
        name: 模板名称，项目内唯一。
        template_type: 模板类型。
        config: 环境配置（JSONB）。
        description: 可选描述。
    """
    template_id: EnvironmentTemplateId
    project_id: ProjectId
    name: str
    template_type: TemplateType
    config: dict[str, object]
    created_by: UserId
    created_at: datetime
    updated_at: datetime
    description: str | None = None

    @classmethod
    def create(
        cls,
        *,
        template_id: EnvironmentTemplateId,
        project_id: ProjectId,
        name: str,
        template_type: TemplateType,
        created_by: UserId,
        config: dict[str, object] | None = None,
        description: str | None = None,
    ) -> EnvironmentTemplate:
        """创建新的环境模板。

        Raises:
            ValueError: name 为空。
        """
        normalized = name.strip()
        if not normalized:
            raise ValueError("Environment template name is required")
        now = datetime.now(UTC)
        return cls(
            template_id=template_id,
            project_id=project_id,
            name=normalized,
            template_type=template_type,
            config=config or {},
            created_by=created_by,
            created_at=now,
            updated_at=now,
            description=description,
        )

    def rename(self, name: str) -> None:
        """修改模板名称。"""
        normalized = name.strip()
        if not normalized:
            raise ValueError("Environment template name is required")
        self.name = normalized
        self.updated_at = datetime.now(UTC)

    def update_description(self, description: str | None) -> None:
        """更新模板描述。"""
        self.description = description
        self.updated_at = datetime.now(UTC)

    def update_config(self, config: dict[str, object]) -> None:
        """更新环境配置。"""
        self.config = config
        self.updated_at = datetime.now(UTC)
