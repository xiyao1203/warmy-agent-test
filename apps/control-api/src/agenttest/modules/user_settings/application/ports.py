"""用户设置 Application 对外部能力的端口。"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from agenttest.modules.user_settings.domain.entities import UserSettings


class UserSettingsRepository(Protocol):
    """用户设置持久化端口。"""

    async def get_by_user_id(self, user_id: UUID) -> UserSettings | None:
        """按用户读取设置。"""
        ...

    async def save(self, settings: UserSettings) -> None:
        """保存用户设置。"""
        ...
