from dataclasses import dataclass

from agenttest.modules.identity.public import User, UserId
from agenttest.modules.projects.domain.entities import (
    Project,
    ProjectId,
    ProjectMemberRole,
)
from agenttest.modules.projects.domain.policies import (
    ProjectAccessPolicy,
    ProjectNotFoundError,
)
from agenttest.modules.projects.domain.repositories import ProjectRepository


@dataclass(frozen=True, slots=True)
class RenameProjectCommand:
    project_id: ProjectId
    name: str


@dataclass(frozen=True, slots=True)
class ProjectMemberCommand:
    project_id: ProjectId
    user_id: UserId
    role: ProjectMemberRole


class RenameProjectHandler:
    def __init__(self, *, projects: ProjectRepository) -> None:
        self._projects = projects

    async def execute(self, actor: User, command: RenameProjectCommand) -> Project:
        project = await required_project(self._projects, command.project_id)
        ProjectAccessPolicy.ensure_can_manage_members(actor, project)
        project.rename(command.name)
        await self._projects.save(project)
        return project


class ArchiveProjectHandler:
    def __init__(self, *, projects: ProjectRepository) -> None:
        self._projects = projects

    async def execute(self, actor: User, project_id: ProjectId) -> Project:
        project = await required_project(self._projects, project_id)
        ProjectAccessPolicy.ensure_can_manage_members(actor, project)
        project.archive()
        await self._projects.save(project)
        return project


class AddProjectMemberHandler:
    def __init__(self, *, projects: ProjectRepository) -> None:
        self._projects = projects

    async def execute(self, actor: User, command: ProjectMemberCommand) -> Project:
        project = await required_project(self._projects, command.project_id)
        ProjectAccessPolicy.ensure_can_manage_members(actor, project)
        project.add_member(command.user_id, command.role)
        await self._projects.save(project)
        return project


class UpdateProjectMemberHandler:
    def __init__(self, *, projects: ProjectRepository) -> None:
        self._projects = projects

    async def execute(self, actor: User, command: ProjectMemberCommand) -> Project:
        project = await required_project(self._projects, command.project_id)
        ProjectAccessPolicy.ensure_can_manage_members(actor, project)
        project.change_member_role(command.user_id, command.role)
        await self._projects.save(project)
        return project


class RemoveProjectMemberHandler:
    def __init__(self, *, projects: ProjectRepository) -> None:
        self._projects = projects

    async def execute(
        self,
        actor: User,
        project_id: ProjectId,
        user_id: UserId,
    ) -> None:
        project = await required_project(self._projects, project_id)
        ProjectAccessPolicy.ensure_can_manage_members(actor, project)
        project.remove_member(user_id)
        await self._projects.save(project)


async def required_project(
    projects: ProjectRepository,
    project_id: ProjectId,
) -> Project:
    project = await projects.get_by_id(project_id)
    if project is None:
        raise ProjectNotFoundError
    return project
