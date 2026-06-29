from __future__ import annotations

from agenttest.modules.identity.application.errors import DuplicateEmailError
from agenttest.modules.identity.application.ports import UserAdminRepository
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email


class UpdateProfileHandler:
    def __init__(self, users: UserAdminRepository) -> None:
        self._users = users

    async def execute(self, user: User, display_name: str, email: Email) -> User:
        # 检查邮箱是否已被其他用户使用
        existing = await self._users.get_by_email(email)
        if existing is not None and existing.user_id != user.user_id:
            raise DuplicateEmailError

        # 更新用户资料
        user.update_profile(
            email=email,
            display_name=display_name,
            role=user.role,  # 保持原有角色
        )
        await self._users.save(user)
        return user
