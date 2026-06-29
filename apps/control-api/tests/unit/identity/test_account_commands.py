from __future__ import annotations

import pytest
from agenttest.modules.identity.application.commands.change_password import (
    ChangePasswordHandler,
)
from agenttest.modules.identity.application.commands.login import InvalidCredentialsError
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email, SystemRole, UserId


def create_user() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("user@example.com"),
        display_name="User",
        role=SystemRole.DEVELOPER,
    )


class FakeCredentials:
    def __init__(self, password_hash: str | None) -> None:
        self.password_hash = password_hash

    async def get_password_hash(self, _user_id: UserId) -> str | None:
        return self.password_hash

    async def set_password_hash(self, _user_id: UserId, password_hash: str) -> None:
        self.password_hash = password_hash


class FakePasswordHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password_hash: str, password: str) -> bool:
        return password_hash == f"hashed:{password}"


@pytest.mark.asyncio
async def test_change_password_verifies_and_replaces_the_credential_hash() -> None:
    user = create_user()
    credentials = FakeCredentials("hashed:current-password")
    handler = ChangePasswordHandler(
        credentials=credentials,
        password_hasher=FakePasswordHasher(),
    )

    await handler.execute(user, "current-password", "new-password")

    assert credentials.password_hash == "hashed:new-password"


@pytest.mark.asyncio
async def test_change_password_rejects_an_incorrect_current_password() -> None:
    user = create_user()
    credentials = FakeCredentials("hashed:current-password")
    handler = ChangePasswordHandler(
        credentials=credentials,
        password_hasher=FakePasswordHasher(),
    )

    with pytest.raises(InvalidCredentialsError):
        await handler.execute(user, "wrong-password", "new-password")
