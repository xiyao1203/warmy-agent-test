from __future__ import annotations

from datetime import UTC, datetime

import pytest
from agenttest.modules.identity.application.commands.create_user import (
    CreateUserCommand,
    CreateUserHandler,
)
from agenttest.modules.identity.application.commands.reset_password import (
    ResetPasswordCommand,
    ResetPasswordHandler,
)
from agenttest.modules.identity.application.commands.set_user_status import (
    DeleteUserHandler,
    ProtectedAdministratorError,
    SetUserStatusCommand,
    SetUserStatusHandler,
)
from agenttest.modules.identity.application.commands.update_user import (
    UpdateUserCommand,
    UpdateUserHandler,
)
from agenttest.modules.identity.application.errors import PermissionDeniedError
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email, SystemRole, UserId, UserStatus
from agenttest.modules.identity.infrastructure.passwords import Argon2PasswordHasher


class FakeUserAdminRepository:
    def __init__(self, users: list[User]) -> None:
        self.users = {user.user_id: user for user in users}
        self.deleted: list[UserId] = []
        self.historical_users: set[UserId] = set()

    async def get_by_id(self, user_id: UserId) -> User | None:
        return self.users.get(user_id)

    async def get_by_email(self, email: Email) -> User | None:
        return next((user for user in self.users.values() if user.email == email), None)

    async def add(self, user: User) -> None:
        self.users[user.user_id] = user

    async def save(self, user: User) -> None:
        self.users[user.user_id] = user

    async def count_active_super_admins(self) -> int:
        return sum(
            user.role is SystemRole.SUPER_ADMIN and user.status is UserStatus.ACTIVE
            for user in self.users.values()
        )

    async def has_historical_activity(self, user_id: UserId) -> bool:
        return user_id in self.historical_users

    async def delete(self, user_id: UserId) -> None:
        self.deleted.append(user_id)
        del self.users[user_id]


class FakeCredentialWriter:
    def __init__(self) -> None:
        self.password_hashes: dict[UserId, str] = {}

    async def set_password_hash(self, user_id: UserId, password_hash: str) -> None:
        self.password_hashes[user_id] = password_hash


class FakeSessionAdmin:
    def __init__(self) -> None:
        self.revoked_users: list[tuple[UserId, datetime]] = []

    async def revoke_all_for_user(self, user_id: UserId, revoked_at: datetime) -> None:
        self.revoked_users.append((user_id, revoked_at))


class FrozenClock:
    def __init__(self, current: datetime) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current


def create_user(role: SystemRole, email: str) -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email(email),
        display_name=email.split("@")[0],
        role=role,
    )


@pytest.mark.asyncio
async def test_only_super_admin_can_create_users() -> None:
    actor = create_user(SystemRole.DEVELOPER, "developer@example.com")
    repository = FakeUserAdminRepository([actor])
    handler = CreateUserHandler(
        users=repository,
        credentials=FakeCredentialWriter(),
        password_hasher=Argon2PasswordHasher(),
    )

    with pytest.raises(PermissionDeniedError):
        await handler.execute(
            actor,
            CreateUserCommand(
                email=Email("new@example.com"),
                display_name="New User",
                role=SystemRole.TESTER,
                initial_password="initial-password",
            ),
        )


@pytest.mark.asyncio
async def test_final_active_super_admin_cannot_be_disabled() -> None:
    admin = create_user(SystemRole.SUPER_ADMIN, "admin@example.com")
    repository = FakeUserAdminRepository([admin])
    handler = SetUserStatusHandler(users=repository, sessions=FakeSessionAdmin())

    with pytest.raises(ProtectedAdministratorError):
        await handler.execute(
            admin,
            SetUserStatusCommand(user_id=admin.user_id, enabled=False),
        )


@pytest.mark.asyncio
async def test_super_admin_cannot_disable_itself_even_when_another_admin_exists() -> None:
    actor = create_user(SystemRole.SUPER_ADMIN, "admin1@example.com")
    other_admin = create_user(SystemRole.SUPER_ADMIN, "admin2@example.com")
    repository = FakeUserAdminRepository([actor, other_admin])
    handler = SetUserStatusHandler(users=repository, sessions=FakeSessionAdmin())

    with pytest.raises(ProtectedAdministratorError):
        await handler.execute(
            actor,
            SetUserStatusCommand(user_id=actor.user_id, enabled=False),
        )


@pytest.mark.asyncio
async def test_reset_password_requires_change_and_revokes_sessions() -> None:
    now = datetime(2026, 6, 25, tzinfo=UTC)
    actor = create_user(SystemRole.SUPER_ADMIN, "admin@example.com")
    target = create_user(SystemRole.DEVELOPER, "developer@example.com")
    repository = FakeUserAdminRepository([actor, target])
    credentials = FakeCredentialWriter()
    sessions = FakeSessionAdmin()
    handler = ResetPasswordHandler(
        users=repository,
        credentials=credentials,
        sessions=sessions,
        password_hasher=Argon2PasswordHasher(),
        clock=FrozenClock(now),
    )

    await handler.execute(
        actor,
        ResetPasswordCommand(user_id=target.user_id, new_password="new-password"),
    )

    assert target.must_change_password is True
    assert credentials.password_hashes[target.user_id].startswith("$argon2id$")
    assert sessions.revoked_users == [(target.user_id, now)]


@pytest.mark.asyncio
async def test_user_with_history_is_disabled_instead_of_deleted() -> None:
    actor = create_user(SystemRole.SUPER_ADMIN, "admin@example.com")
    target = create_user(SystemRole.DEVELOPER, "developer@example.com")
    repository = FakeUserAdminRepository([actor, target])
    repository.historical_users.add(target.user_id)
    sessions = FakeSessionAdmin()
    handler = DeleteUserHandler(users=repository, sessions=sessions)

    await handler.execute(actor, target.user_id)

    assert target.status is UserStatus.DISABLED
    assert repository.deleted == []


@pytest.mark.asyncio
async def test_super_admin_cannot_change_own_role() -> None:
    actor = create_user(SystemRole.SUPER_ADMIN, "admin@example.com")
    repository = FakeUserAdminRepository([actor])

    with pytest.raises(ProtectedAdministratorError):
        await UpdateUserHandler(users=repository).execute(
            actor,
            UpdateUserCommand(
                user_id=actor.user_id,
                email=actor.email,
                display_name=actor.display_name,
                role=SystemRole.DEVELOPER,
            ),
        )


@pytest.mark.asyncio
async def test_final_active_super_admin_cannot_be_deleted() -> None:
    admin = create_user(SystemRole.SUPER_ADMIN, "admin@example.com")
    repository = FakeUserAdminRepository([admin])

    with pytest.raises(ProtectedAdministratorError):
        await DeleteUserHandler(
            users=repository,
            sessions=FakeSessionAdmin(),
        ).execute(admin, admin.user_id)
