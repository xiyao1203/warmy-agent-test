"""Environment 领域仓库接口。"""

from __future__ import annotations

from typing import Protocol

from agenttest.modules.environments.domain.entities import (
    EnvironmentTemplate,
    EnvironmentTemplateId,
)
from agenttest.modules.projects.public import ProjectId
from agenttest.shared.application.pagination import PageRequest, PageResult


class EnvironmentTemplateRepository(Protocol):
    """环境模板的持久化仓库接口。"""

    async def get_by_id(self, template_id: EnvironmentTemplateId) -> EnvironmentTemplate | None: ...

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[EnvironmentTemplate], str | None]: ...

    async def count_by_project(self, project_id: ProjectId) -> int: ...

    async def list_page_by_project(
        self,
        project_id: ProjectId,
        page_request: PageRequest,
    ) -> PageResult[EnvironmentTemplate]: ...

    async def add(self, template: EnvironmentTemplate) -> None: ...

    async def save(self, template: EnvironmentTemplate) -> None: ...

    async def delete(self, template_id: EnvironmentTemplateId) -> None: ...

    async def get_by_id_and_project(
        self, template_id: EnvironmentTemplateId, project_id: ProjectId
    ) -> EnvironmentTemplate | None: ...
