from uuid import uuid4

import pytest
from agenttest.modules.user_settings.domain.entities import UserSettings
from agenttest.modules.user_settings.infrastructure.persistence.models import UserSettingsModel
from agenttest.modules.user_settings.infrastructure.persistence.repositories import (
    SqlAlchemyUserSettingsRepository,
)
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


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
