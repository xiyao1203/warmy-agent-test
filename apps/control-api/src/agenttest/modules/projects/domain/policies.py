from agenttest.modules.identity.public import SystemRole, User
from agenttest.modules.projects.domain.entities import Project


class ProjectNotFoundError(Exception):
    """Used for unauthorized project access to avoid existence disclosure."""


class ProjectAccessDeniedError(Exception):
    pass


class ProjectAccessPolicy:
    @staticmethod
    def ensure_can_view(user: User, project: Project) -> None:
        if user.role is SystemRole.SUPER_ADMIN:
            return
        if project.member_role(user.user_id) is None:
            raise ProjectNotFoundError

    @staticmethod
    def ensure_can_manage_members(user: User, project: Project) -> None:
        ProjectAccessPolicy.ensure_can_view(user, project)
        if user.role is not SystemRole.SUPER_ADMIN:
            raise ProjectAccessDeniedError
