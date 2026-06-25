from dataclasses import dataclass

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
    def __init__(self, *, users: UserAdminRepository) -> None:
        self._users = users

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
        target.update_profile(
            email=command.email,
            display_name=command.display_name,
            role=command.role or target.role,
        )
        await self._users.save(target)
        return target
