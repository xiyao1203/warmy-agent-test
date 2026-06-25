from dataclasses import dataclass

from agenttest.modules.identity.application.errors import UserNotFoundError
from agenttest.modules.identity.application.policies import require_super_admin
from agenttest.modules.identity.application.ports import SessionAdmin, UserAdminRepository
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import SystemRole, UserId
from agenttest.shared.domain.clock import Clock, SystemClock


class ProtectedAdministratorError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class SetUserStatusCommand:
    user_id: UserId
    enabled: bool


class SetUserStatusHandler:
    def __init__(
        self,
        *,
        users: UserAdminRepository,
        sessions: SessionAdmin,
        clock: Clock | None = None,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._clock = clock or SystemClock()

    async def execute(self, actor: User, command: SetUserStatusCommand) -> User:
        require_super_admin(actor)
        target = await _required_user(self._users, command.user_id)
        if command.enabled:
            target.enable()
        else:
            await _ensure_can_remove_access(actor, target, self._users)
            target.disable()
            await self._sessions.revoke_all_for_user(target.user_id, self._clock.now())
        await self._users.save(target)
        return target


class DeleteUserHandler:
    def __init__(
        self,
        *,
        users: UserAdminRepository,
        sessions: SessionAdmin,
        clock: Clock | None = None,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._clock = clock or SystemClock()

    async def execute(self, actor: User, user_id: UserId) -> None:
        require_super_admin(actor)
        target = await _required_user(self._users, user_id)
        await _ensure_can_remove_access(actor, target, self._users)
        if await self._users.has_historical_activity(user_id):
            target.disable()
            await self._users.save(target)
            await self._sessions.revoke_all_for_user(user_id, self._clock.now())
            return
        await self._users.delete(user_id)
        await self._sessions.revoke_all_for_user(user_id, self._clock.now())


async def _required_user(repository: UserAdminRepository, user_id: UserId) -> User:
    user = await repository.get_by_id(user_id)
    if user is None:
        raise UserNotFoundError
    return user


async def _ensure_can_remove_access(
    actor: User,
    target: User,
    repository: UserAdminRepository,
) -> None:
    if actor.user_id == target.user_id:
        raise ProtectedAdministratorError
    if (
        target.role is SystemRole.SUPER_ADMIN
        and await repository.count_active_super_admins() <= 1
    ):
        raise ProtectedAdministratorError
