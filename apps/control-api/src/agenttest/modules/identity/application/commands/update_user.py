from dataclasses import dataclass

from agenttest.modules.audit.public import AuditWriter
from agenttest.modules.identity.application.commands.set_user_status import (
    ProtectedAdministratorError,
)
from agenttest.modules.identity.application.errors import DuplicateEmailError, UserNotFoundError
from agenttest.modules.identity.application.policies import require_super_admin
from agenttest.modules.identity.application.ports import UserAdminRepository
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email, SystemRole, UserId


@dataclass(frozen=True, slots=True)
class UpdateUserCommand:
    user_id: UserId
    email: Email
    display_name: str
    role: SystemRole | None


class UpdateUserHandler:
    def __init__(
        self,
        *,
        users: UserAdminRepository,
        audit: AuditWriter | None = None,
    ) -> None:
        self._users = users
        self._audit = audit

    async def execute(self, actor: User, command: UpdateUserCommand) -> User:
        require_super_admin(actor)
        target = await self._users.get_by_id(command.user_id)
        if target is None:
            raise UserNotFoundError
        existing = await self._users.get_by_email(command.email)
        if existing is not None and existing.user_id != target.user_id:
            raise DuplicateEmailError
        if (
            actor.user_id == target.user_id
            and command.role is not None
            and command.role is not target.role
        ):
            raise ProtectedAdministratorError
        before = {
            "email": target.email.value,
            "display_name": target.display_name,
            "role": target.role.value,
        }
        target.update_profile(
            email=command.email,
            display_name=command.display_name,
            role=command.role or target.role,
        )
        await self._users.save(target)
        if self._audit is not None:
            await self._audit.record(
                actor_user_id=actor.user_id,
                action="identity.user.updated",
                object_type="user",
                object_id=target.user_id.value,
                project_id=None,
                changes={
                    key: {"before": before[key], "after": value}
                    for key, value in {
                        "email": target.email.value,
                        "display_name": target.display_name,
                        "role": target.role.value,
                    }.items()
                    if before[key] != value
                },
                source_ip=None,
            )
        return target
