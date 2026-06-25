from dataclasses import dataclass

from agenttest.modules.audit.public import AuditWriter
from agenttest.modules.identity.public import SystemRole, User
from agenttest.modules.projects.domain.entities import Project, ProjectId
from agenttest.modules.projects.domain.policies import ProjectAccessDeniedError
from agenttest.modules.projects.domain.repositories import ProjectRepository


@dataclass(frozen=True, slots=True)
class CreateProjectCommand:
    name: str


class CreateProjectHandler:
    def __init__(
        self,
        *,
        projects: ProjectRepository,
        audit: AuditWriter | None = None,
    ) -> None:
        self._projects = projects
        self._audit = audit

    async def execute(self, actor: User, command: CreateProjectCommand) -> Project:
        if actor.role is not SystemRole.SUPER_ADMIN:
            raise ProjectAccessDeniedError
        project = Project.create(
            project_id=ProjectId.new(),
            name=command.name,
            created_by=actor.user_id,
        )
        await self._projects.add(project)
        if self._audit is not None:
            await self._audit.record(
                actor_user_id=actor.user_id,
                action="projects.created",
                object_type="project",
                object_id=project.project_id.value,
                project_id=project.project_id,
                changes={"name": {"after": project.name}},
                source_ip=None,
            )
        return project
