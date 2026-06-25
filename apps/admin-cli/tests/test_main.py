from __future__ import annotations

from dataclasses import dataclass

import pytest
from agenttest.modules.identity.application.errors import DuplicateEmailError
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email, UserId
from agenttest_admin.main import create_super_admin


class FakeUsers:
    def __init__(self) -> None:
        self.user: User | None = None

    async def get_by_email(self, email: Email) -> User | None:
        if self.user is not None and self.user.email == email:
            return self.user
        return None

    async def add(self, user: User) -> None:
        self.user = user


@dataclass
class FakeCredentials:
    user_id: UserId | None = None
    password_hash: str | None = None

    async def set_password_hash(self, user_id: UserId, password_hash: str) -> None:
        self.user_id = user_id
        self.password_hash = password_hash


@pytest.mark.asyncio
async def test_create_super_admin_hashes_password_and_requires_change(
    capsys: pytest.CaptureFixture[str],
) -> None:
    users = FakeUsers()
    credentials = FakeCredentials()

    user = await create_super_admin(
        users=users,
        credentials=credentials,
        email="ADMIN@EXAMPLE.COM",
        name="Admin",
        password="initial-password",
    )

    assert user.email.value == "admin@example.com"
    assert user.must_change_password is True
    assert credentials.password_hash is not None
    assert credentials.password_hash.startswith("$argon2id$")
    assert "initial-password" not in capsys.readouterr().out


@pytest.mark.asyncio
async def test_create_super_admin_refuses_duplicate_email() -> None:
    users = FakeUsers()
    credentials = FakeCredentials()
    await create_super_admin(
        users=users,
        credentials=credentials,
        email="admin@example.com",
        name="Admin",
        password="initial-password",
    )

    with pytest.raises(DuplicateEmailError):
        await create_super_admin(
            users=users,
            credentials=credentials,
            email="ADMIN@example.com",
            name="Other Admin",
            password="another-password",
        )
