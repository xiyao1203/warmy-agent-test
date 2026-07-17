"""用户设置查询处理器。"""

from __future__ import annotations

from uuid import UUID

from agenttest.modules.user_settings.application.ports import UserSettingsRepository
from agenttest.modules.user_settings.domain.entities import UserSettings


class GetUserSettingsHandler:
    """获取用户设置处理器。"""

    def __init__(self, repository: UserSettingsRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: str) -> UserSettings | None:
        return await self._repository.get_by_user_id(UUID(user_id))
