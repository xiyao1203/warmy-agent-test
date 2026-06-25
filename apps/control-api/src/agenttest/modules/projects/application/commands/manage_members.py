from dataclasses import dataclass

from agenttest.modules.audit.public import AuditWriter
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
    def __init__(self, *, projects: ProjectRepository, audit: AuditWriter | None = None) -> None:
        self._projects = projects
        self._audit = audit

    async def execute(self, actor: User, command: RenameProjectCommand) -> Project:
        project = await required_project(self._projects, command.project_id)
        ProjectAccessPolicy.ensure_can_manage_members(actor, project)
        before = project.name
        project.rename(command.name)
        await self._projects.save(project)
        await _record(
            self._audit,
            actor=actor,
            action="projects.renamed",
            project=project,
            object_type="project",
            object_id=project.project_id.value,
            changes={"name": {"before": before, "after": project.name}},
        )
        return project


class ArchiveProjectHandler:
    def __init__(self, *, projects: ProjectRepository, audit: AuditWriter | None = None) -> None:
        self._projects = projects
        self._audit = audit

    async def execute(self, actor: User, project_id: ProjectId) -> Project:
        project = await required_project(self._projects, project_id)
        ProjectAccessPolicy.ensure_can_manage_members(actor, project)
        project.archive()
        await self._projects.save(project)
        await _record(
            self._audit,
            actor=actor,
            action="projects.archived",
            project=project,
            object_type="project",
            object_id=project.project_id.value,
            changes={"archived": {"after": True}},
        )
        return project


class AddProjectMemberHandler:
    def __init__(self, *, projects: ProjectRepository, audit: AuditWriter | None = None) -> None:
        self._projects = projects
        self._audit = audit

    async def execute(self, actor: User, command: ProjectMemberCommand) -> Project:
        project = await required_project(self._projects, command.project_id)
        ProjectAccessPolicy.ensure_can_manage_members(actor, project)
        project.add_member(command.user_id, command.role)
        await self._projects.save(project)
        await _record_member(self._audit, actor, project, command, "projects.member.added")
        return project


class UpdateProjectMemberHandler:
    def __init__(self, *, projects: ProjectRepository, audit: AuditWriter | None = None) -> None:
        self._projects = projects
        self._audit = audit

    async def execute(self, actor: User, command: ProjectMemberCommand) -> Project:
        project = await required_project(self._projects, command.project_id)
        ProjectAccessPolicy.ensure_can_manage_members(actor, project)
        project.change_member_role(command.user_id, command.role)
        await self._projects.save(project)
        await _record_member(self._audit, actor, project, command, "projects.member.updated")
        return project


class RemoveProjectMemberHandler:
    def __init__(self, *, projects: ProjectRepository, audit: AuditWriter | None = None) -> None:
        self._projects = projects
        self._audit = audit

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
        if self._audit is not None:
            await self._audit.record(
                actor_user_id=actor.user_id,
                action="projects.member.removed",
                object_type="project_member",
                object_id=user_id.value,
                project_id=project.project_id,
                changes={},
                source_ip=None,
            )


async def required_project(
    projects: ProjectRepository,
    project_id: ProjectId,
) -> Project:
    project = await projects.get_by_id(project_id)
    if project is None:
        raise ProjectNotFoundError
    return project


async def _record_member(
    audit: AuditWriter | None,
    actor: User,
    project: Project,
    command: ProjectMemberCommand,
    action: str,
) -> None:
    await _record(
        audit,
        actor=actor,
        action=action,
        project=project,
        object_type="project_member",
        object_id=command.user_id.value,
        changes={"role": {"after": command.role.value}},
    )


async def _record(
    audit: AuditWriter | None,
    *,
    actor: User,
    action: str,
    project: Project,
    object_type: str,
    object_id,
    changes: dict,
) -> None:
    if audit is not None:
        await audit.record(
            actor_user_id=actor.user_id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            project_id=project.project_id,
            changes=changes,
            source_ip=None,
        )
