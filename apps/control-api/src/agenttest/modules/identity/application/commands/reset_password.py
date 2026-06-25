from dataclasses import dataclass

from agenttest.modules.identity.application.errors import UserNotFoundError
from agenttest.modules.identity.application.policies import require_super_admin
from agenttest.modules.identity.application.ports import (
    CredentialWriter,
    PasswordHasher,
    SessionAdmin,
    UserAdminRepository,
)
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import UserId
from agenttest.shared.domain.clock import Clock


@dataclass(frozen=True, slots=True)
class ResetPasswordCommand:
    user_id: UserId
    new_password: str


class ResetPasswordHandler:
    def __init__(
        self,
        *,
        users: UserAdminRepository,
        credentials: CredentialWriter,
        sessions: SessionAdmin,
        password_hasher: PasswordHasher,
        clock: Clock,
    ) -> None:
        self._users = users
        self._credentials = credentials
        self._sessions = sessions
        self._password_hasher = password_hasher
        self._clock = clock

    async def execute(self, actor: User, command: ResetPasswordCommand) -> None:
        require_super_admin(actor)
        target = await self._users.get_by_id(command.user_id)
        if target is None:
            raise UserNotFoundError
        target.require_password_change()
        await self._credentials.set_password_hash(
            target.user_id,
            self._password_hasher.hash(command.new_password),
        )
        await self._users.save(target)
        await self._sessions.revoke_all_for_user(target.user_id, self._clock.now())
