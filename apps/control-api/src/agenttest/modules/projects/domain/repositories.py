from typing import Protocol

from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.domain.entities import Project, ProjectId
from agenttest.shared.application.pagination import PageRequest, PageResult


class ProjectRepository(Protocol):
    async def get_by_id(self, project_id: ProjectId) -> Project | None: ...

    async def list_for_user(self, user_id: UserId | None) -> list[Project]: ...

    async def list_page_for_user(
        self,
        user_id: UserId | None,
        page_request: PageRequest,
    ) -> PageResult[Project]: ...

    async def add(self, project: Project) -> None: ...

    async def save(self, project: Project) -> None: ...
