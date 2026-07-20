from agenttest.modules.identity.public import SystemRole, User
from agenttest.modules.projects.application.commands.manage_members import required_project
from agenttest.modules.projects.domain.entities import Project, ProjectId
from agenttest.modules.projects.domain.policies import ProjectAccessPolicy
from agenttest.modules.projects.domain.repositories import ProjectRepository
from agenttest.shared.application.pagination import PageRequest, PageResult


class ListProjectsHandler:
    def __init__(self, *, projects: ProjectRepository) -> None:
        self._projects = projects

    async def execute(self, actor: User) -> list[Project]:
        user_id = None if actor.role is SystemRole.SUPER_ADMIN else actor.user_id
        return await self._projects.list_for_user(user_id)

    async def execute_page(
        self,
        actor: User,
        page_request: PageRequest,
    ) -> PageResult[Project]:
        user_id = None if actor.role is SystemRole.SUPER_ADMIN else actor.user_id
        return await self._projects.list_page_for_user(user_id, page_request)


class GetProjectHandler:
    def __init__(self, *, projects: ProjectRepository) -> None:
        self._projects = projects

    async def execute(self, actor: User, project_id: ProjectId) -> Project:
        project = await required_project(self._projects, project_id)
        ProjectAccessPolicy.ensure_can_view(actor, project)
        return project


class ListProjectMembersHandler:
    def __init__(self, *, projects: ProjectRepository) -> None:
        self._projects = projects

    async def execute(self, actor: User, project_id: ProjectId) -> Project:
        project = await required_project(self._projects, project_id)
        ProjectAccessPolicy.ensure_can_view(actor, project)
        return project
