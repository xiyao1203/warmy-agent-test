"""项目级大模型配置仓库协议。"""

from __future__ import annotations

from typing import Protocol

from agenttest.modules.projects.public import ProjectId

from .entities import ModelConfiguration, ModelConfigurationId, ProjectModelDefault
from .value_objects import ModelPurpose


class ModelConfigRepository(Protocol):
    """模型配置和项目默认用途的持久化端口。"""

    async def list_by_project(self, project_id: ProjectId) -> list[ModelConfiguration]: ...
    async def get(
        self, project_id: ProjectId, model_config_id: ModelConfigurationId
    ) -> ModelConfiguration | None: ...
    async def add(self, item: ModelConfiguration) -> None: ...
    async def save(self, item: ModelConfiguration) -> None: ...
    async def delete(
        self, project_id: ProjectId, model_config_id: ModelConfigurationId
    ) -> None: ...
    async def list_defaults(self, project_id: ProjectId) -> list[ProjectModelDefault]: ...
    async def get_default(
        self, project_id: ProjectId, purpose: ModelPurpose
    ) -> ProjectModelDefault | None: ...
    async def set_default(self, value: ProjectModelDefault) -> None: ...
    async def is_default(
        self, project_id: ProjectId, model_config_id: ModelConfigurationId
    ) -> bool: ...
