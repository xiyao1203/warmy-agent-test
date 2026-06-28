from __future__ import annotations

from agenttest.modules.identity.application.commands.login import InvalidCredentialsError
from agenttest.modules.identity.application.ports import PasswordHasher, UserAdminRepository
from agenttest.modules.identity.domain.entities import User


class ChangePasswordHandler:
    def __init__(self, users: UserAdminRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    async def execute(self, user: User, current_password: str, new_password: str) -> None:
        # 验证当前密码
        if not self._hasher.verify(current_password, user.password_hash):
            raise InvalidCredentialsError

        # 验证新密码强度
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # 更新密码
        user.password_hash = self._hasher.hash(new_password)
        user.must_change_password = False
        await self._users.save(user)
