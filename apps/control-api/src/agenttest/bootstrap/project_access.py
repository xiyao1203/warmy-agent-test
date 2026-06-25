"""Adapters that expose project authorization to M2 application modules."""

from agenttest.modules.identity.public import SystemRole, User
from agenttest.modules.projects.domain.entities import ProjectMemberRole
from agenttest.modules.projects.domain.policies import ProjectNotFoundError
from agenttest.modules.projects.domain.repositories import ProjectRepository
from agenttest.modules.projects.public import ProjectId


class ProjectAccessAdapter:
    """Resolve project membership without exposing Projects internals to modules."""

    def __init__(self, projects: ProjectRepository) -> None:
        self._projects = projects

    async def ensure_member(self, actor: User, project_id: ProjectId) -> None:
        project = await self._projects.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError
        if actor.role is SystemRole.SUPER_ADMIN:
            return
        if project.member_role(actor.user_id) is None:
            raise ProjectNotFoundError

    async def ensure_editor(self, actor: User, project_id: ProjectId) -> None:
        project = await self._projects.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError
        if actor.role is SystemRole.SUPER_ADMIN:
            return
        role = project.member_role(actor.user_id)
        if role is None:
            raise ProjectNotFoundError
        if role not in {ProjectMemberRole.DEVELOPER, ProjectMemberRole.TESTER}:
            raise PermissionError("Project editor access is required")
