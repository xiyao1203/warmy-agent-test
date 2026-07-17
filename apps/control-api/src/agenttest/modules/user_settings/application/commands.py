"""用户设置命令处理器。"""

from __future__ import annotations

from uuid import UUID

from agenttest.modules.user_settings.application.ports import UserSettingsRepository
from agenttest.modules.user_settings.domain.entities import UserSettings
from agenttest.modules.user_settings.domain.value_objects import Language, Theme


class UpdateUserSettingsHandler:
    """更新用户设置处理器。"""

    def __init__(self, repository: UserSettingsRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        user_id: str,
        *,
        theme: Theme | None = None,
        language: Language | None = None,
        email_notifications: bool | None = None,
        push_notifications: bool | None = None,
        test_complete_notifications: bool | None = None,
    ) -> UserSettings:
        # 获取现有设置或创建默认设置
        settings = await self._repository.get_by_user_id(UUID(user_id))
        if settings is None:
            settings = UserSettings(user_id=UUID(user_id))

        # 更新设置
        if theme is not None:
            settings.update_theme(theme)
        if language is not None:
            settings.update_language(language)
        notification_values = (
            email_notifications,
            push_notifications,
            test_complete_notifications,
        )
        if any(value is not None for value in notification_values):
            settings.update_notifications(
                email=email_notifications,
                push=push_notifications,
                test_complete=test_complete_notifications,
            )

        await self._repository.save(settings)
        return settings
