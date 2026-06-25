"""Environment template application query handlers."""

from __future__ import annotations

from agenttest.modules.environments.application.commands import _required
from agenttest.modules.environments.application.ports import ProjectAccessPort
from agenttest.modules.environments.domain.entities import (
    EnvironmentTemplate,
    EnvironmentTemplateId,
)
from agenttest.modules.environments.domain.repositories import (
    EnvironmentTemplateRepository,
)
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId


class ListEnvironmentTemplatesHandler:
    def __init__(
        self,
        *,
        templates: EnvironmentTemplateRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._templates = templates
        self._project_access = project_access

    async def execute(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[EnvironmentTemplate], str | None]:
        await self._project_access.ensure_member(actor, project_id)
        return await self._templates.list_by_project(project_id, limit=limit, cursor=cursor)


class GetEnvironmentTemplateHandler:
    def __init__(
        self,
        *,
        templates: EnvironmentTemplateRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._templates = templates
        self._project_access = project_access

    async def execute(
        self, actor: User, template_id: EnvironmentTemplateId
    ) -> EnvironmentTemplate:
        template = await _required(self._templates, template_id)
        await self._project_access.ensure_member(actor, template.project_id)
        return template
