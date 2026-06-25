from dataclasses import dataclass
from uuid import UUID

from agenttest.modules.identity.application.errors import UserNotFoundError
from agenttest.modules.identity.application.policies import require_super_admin
from agenttest.modules.identity.application.ports import UserAdminRepository
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import UserId


@dataclass(frozen=True, slots=True)
class UserPage:
    items: list[User]
    next_cursor: UUID | None


class ListUsersQuery:
    def __init__(self, *, users: UserAdminRepository) -> None:
        self._users = users

    async def execute(
        self,
        actor: User,
        cursor: UUID | None,
        limit: int,
    ) -> UserPage:
        require_super_admin(actor)
        items, next_cursor = await self._users.list_page(cursor=cursor, limit=limit)
        return UserPage(items=items, next_cursor=next_cursor)


class GetUserQuery:
    def __init__(self, *, users: UserAdminRepository) -> None:
        self._users = users

    async def execute(self, actor: User, user_id: UserId) -> User:
        require_super_admin(actor)
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError
        return user
