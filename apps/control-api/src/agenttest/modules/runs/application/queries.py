from __future__ import annotations

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.application.commands import RunNotFoundError
from agenttest.modules.runs.application.ports import ProjectAccessPort, RunRepository
from agenttest.modules.runs.domain.entities import Run, RunCase, RunId
from agenttest.shared.application.pagination import PageRequest, PageResult


class ListRunsHandler:
    def __init__(self, *, runs: RunRepository, project_access: ProjectAccessPort) -> None:
        self._runs = runs
        self._project_access = project_access

    async def execute(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        limit: int = 50,
    ) -> list[Run]:
        await self._project_access.ensure_member(actor, project_id)
        return await self._runs.list_by_project(project_id, limit=limit)

    async def execute_page(
        self,
        actor: User,
        project_id: ProjectId,
        page: PageRequest,
    ) -> PageResult[Run]:
        await self._project_access.ensure_member(actor, project_id)
        items = await self._runs.list_by_project(
            project_id,
            limit=page.page_size,
            offset=page.offset,
        )
        total = await self._runs.count_by_project(project_id)
        return PageResult(
            items=items,
            total=total,
            page=page.page,
            page_size=page.page_size,
        )


class GetRunHandler:
    def __init__(self, *, runs: RunRepository, project_access: ProjectAccessPort) -> None:
        self._runs = runs
        self._project_access = project_access

    async def execute(self, actor: User, project_id: ProjectId, run_id: RunId) -> Run:
        await self._project_access.ensure_member(actor, project_id)
        run = await self._runs.get_by_id(project_id, run_id)
        if run is None:
            raise RunNotFoundError
        return run


class ListRunCasesHandler:
    def __init__(self, *, runs: RunRepository, project_access: ProjectAccessPort) -> None:
        self._runs = runs
        self._project_access = project_access

    async def execute(
        self,
        actor: User,
        project_id: ProjectId,
        run_id: RunId,
    ) -> list[RunCase]:
        await self._project_access.ensure_member(actor, project_id)
        run = await self._runs.get_by_id(project_id, run_id)
        if run is None:
            raise RunNotFoundError
        return await self._runs.list_cases(project_id, run_id)
