from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4

from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email, UserId


@dataclass(frozen=True, slots=True)
class SessionRecord:
    user_id: UserId
    token_hash: str
    csrf_token_hash: str
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime
    session_id: UUID = field(default_factory=uuid4)

    def is_valid_at(self, moment: datetime) -> bool:
        return self.revoked_at is None and self.expires_at > moment


class UserReader(Protocol):
    async def get_by_email(self, email: Email) -> User | None: ...

    async def get_by_id(self, user_id: UserId) -> User | None: ...


class CredentialReader(Protocol):
    async def get_password_hash(self, user_id: UserId) -> str | None: ...


class SessionRepository(Protocol):
    async def add(self, session: SessionRecord) -> None: ...

    async def get_by_token_hash(self, token_hash: str) -> SessionRecord | None: ...

    async def revoke_by_token_hash(self, token_hash: str, revoked_at: datetime) -> None: ...


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password_hash: str, password: str) -> bool: ...


class UserAdminRepository(UserReader, Protocol):
    async def add(self, user: User) -> None: ...

    async def save(self, user: User) -> None: ...

    async def count_active_super_admins(self) -> int: ...

    async def has_historical_activity(self, user_id: UserId) -> bool: ...

    async def delete(self, user_id: UserId) -> None: ...

    async def list_page(
        self,
        *,
        cursor: UUID | None,
        limit: int,
    ) -> tuple[list[User], UUID | None]: ...


class CredentialWriter(Protocol):
    async def set_password_hash(self, user_id: UserId, password_hash: str) -> None: ...


class SessionAdmin(Protocol):
    async def revoke_all_for_user(self, user_id: UserId, revoked_at: datetime) -> None: ...
