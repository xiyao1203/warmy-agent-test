from agenttest.modules.identity.application.errors import PermissionDeniedError
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import SystemRole


def require_super_admin(actor: User) -> None:
    if actor.role is not SystemRole.SUPER_ADMIN or not actor.can_authenticate:
        raise PermissionDeniedError
