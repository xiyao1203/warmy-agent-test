from typing import Protocol

from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email, UserId


class UserRepository(Protocol):
    async def get_by_id(self, user_id: UserId) -> User | None: ...

    async def get_by_email(self, email: Email) -> User | None: ...

    async def add(self, user: User) -> None: ...

    async def save(self, user: User) -> None: ...
