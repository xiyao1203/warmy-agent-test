from dataclasses import dataclass

from agenttest.modules.identity.application.errors import DuplicateEmailError
from agenttest.modules.identity.application.policies import require_super_admin
from agenttest.modules.identity.application.ports import (
    CredentialWriter,
    PasswordHasher,
    UserAdminRepository,
)
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email, SystemRole, UserId


@dataclass(frozen=True, slots=True)
class CreateUserCommand:
    email: Email
    display_name: str
    role: SystemRole
    initial_password: str


class CreateUserHandler:
    def __init__(
        self,
        *,
        users: UserAdminRepository,
        credentials: CredentialWriter,
        password_hasher: PasswordHasher,
    ) -> None:
        self._users = users
        self._credentials = credentials
        self._password_hasher = password_hasher

    async def execute(self, actor: User, command: CreateUserCommand) -> User:
        require_super_admin(actor)
        if await self._users.get_by_email(command.email) is not None:
            raise DuplicateEmailError
        user = User.create(
            user_id=UserId.new(),
            email=command.email,
            display_name=command.display_name,
            role=command.role,
        )
        user.require_password_change()
        await self._users.add(user)
        await self._credentials.set_password_hash(
            user.user_id,
            self._password_hasher.hash(command.initial_password),
        )
        return user
