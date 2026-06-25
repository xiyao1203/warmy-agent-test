from dataclasses import dataclass

from agenttest.modules.identity.public import SystemRole, User
from agenttest.modules.projects.domain.entities import Project, ProjectId
from agenttest.modules.projects.domain.policies import ProjectAccessDeniedError
from agenttest.modules.projects.domain.repositories import ProjectRepository


@dataclass(frozen=True, slots=True)
class CreateProjectCommand:
    name: str


class CreateProjectHandler:
    def __init__(self, *, projects: ProjectRepository) -> None:
        self._projects = projects

    async def execute(self, actor: User, command: CreateProjectCommand) -> Project:
        if actor.role is not SystemRole.SUPER_ADMIN:
            raise ProjectAccessDeniedError
        project = Project.create(
            project_id=ProjectId.new(),
            name=command.name,
            created_by=actor.user_id,
        )
        await self._projects.add(project)
        return project
