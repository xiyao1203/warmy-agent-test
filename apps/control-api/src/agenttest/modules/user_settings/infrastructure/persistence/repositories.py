"""用户设置仓储实现。"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agenttest.modules.user_settings.domain.entities import UserSettings
from agenttest.modules.user_settings.domain.value_objects import Language, Theme
from agenttest.modules.user_settings.infrastructure.persistence.models import UserSettingsModel


class SqlAlchemyUserSettingsRepository:
    """基于 SQLAlchemy 的用户设置仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: UUID) -> UserSettings | None:
        stmt = select(UserSettingsModel).where(UserSettingsModel.user_id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def save(self, settings: UserSettings) -> None:
        model = self._to_model(settings)
        await self._session.merge(model)
        await self._session.flush()

    def _to_domain(self, model: UserSettingsModel) -> UserSettings:
        return UserSettings(
            user_id=model.user_id,
            theme=Theme(model.theme),
            language=Language(model.language),
            email_notifications=model.email_notifications,
            push_notifications=model.push_notifications,
            test_complete_notifications=model.test_complete_notifications,
        )

    def _to_model(self, settings: UserSettings) -> UserSettingsModel:
        return UserSettingsModel(
            user_id=settings.user_id,
            theme=settings.theme.value,
            language=settings.language.value,
            email_notifications=settings.email_notifications,
            push_notifications=settings.push_notifications,
            test_complete_notifications=settings.test_complete_notifications,
        )
