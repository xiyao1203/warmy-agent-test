from __future__ import annotations

from typing import Protocol

from agenttest.modules.identity.application.commands.login import InvalidCredentialsError
from agenttest.modules.identity.application.ports import (
    CredentialReader,
    CredentialWriter,
    PasswordHasher,
)
from agenttest.modules.identity.domain.entities import User


class CredentialStore(CredentialReader, CredentialWriter, Protocol):
    pass


class ChangePasswordHandler:
    def __init__(
        self,
        *,
        credentials: CredentialStore,
        password_hasher: PasswordHasher,
    ) -> None:
        self._credentials = credentials
        self._password_hasher = password_hasher

    async def execute(self, user: User, current_password: str, new_password: str) -> None:
        password_hash = await self._credentials.get_password_hash(user.user_id)
        if password_hash is None or not self._password_hasher.verify(
            password_hash,
            current_password,
        ):
            raise InvalidCredentialsError
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        await self._credentials.set_password_hash(
            user.user_id,
            self._password_hasher.hash(new_password),
        )
