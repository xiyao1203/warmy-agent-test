from uuid import uuid4

import pytest
from agenttest.modules.user_settings.application.commands import UpdateUserSettingsHandler
from agenttest.modules.user_settings.application.ports import UserSettingsRepository
from agenttest.modules.user_settings.application.queries import GetUserSettingsHandler
from agenttest.modules.user_settings.domain.entities import UserSettings
from agenttest.modules.user_settings.domain.value_objects import Language, Theme
from agenttest.modules.user_settings.infrastructure.persistence.models import UserSettingsModel
from agenttest.modules.user_settings.infrastructure.persistence.repositories import (
    SqlAlchemyUserSettingsRepository,
)
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


class StubUserSettingsRepository:
    """Application Handler 使用的内存仓储。"""

    def __init__(self, settings: UserSettings | None = None) -> None:
        self.settings = settings
        self.saved: UserSettings | None = None

    async def get_by_user_id(self, _user_id):
        return self.settings

    async def save(self, settings: UserSettings) -> None:
        self.saved = settings
        self.settings = settings


@pytest.mark.asyncio
async def test_user_settings_handlers_depend_on_repository_port() -> None:
    user_id = uuid4()
    repository: UserSettingsRepository = StubUserSettingsRepository()
    update = UpdateUserSettingsHandler(repository)
    query = GetUserSettingsHandler(repository)

    settings = await update.execute(
        str(user_id),
        theme=Theme.DARK,
        language=Language.EN,
        email_notifications=False,
        push_notifications=True,
    )

    assert settings.user_id == user_id
    assert settings.theme is Theme.DARK
    assert settings.language is Language.EN
    assert settings.email_notifications is False
    assert settings.push_notifications is True
    assert await query.execute(str(user_id)) is settings


@pytest.mark.asyncio
async def test_user_settings_repository_persists_with_a_session_factory() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(UserSettingsModel.__table__.create)
    repository = SqlAlchemyUserSettingsRepository(
        async_sessionmaker(engine, expire_on_commit=False)
    )
    settings = UserSettings(user_id=uuid4(), email_notifications=False)

    await repository.save(settings)

    assert await repository.get_by_user_id(settings.user_id) == settings
    await engine.dispose()
