from datetime import UTC, datetime
from uuid import uuid4

import pytest
from agenttest.modules.browser_profiles.application.service import DuplicateBrowserProfile
from agenttest.modules.browser_profiles.domain.entities import BrowserProfile
from agenttest.modules.browser_profiles.infrastructure.models import BrowserProfileModel
from agenttest.modules.browser_profiles.infrastructure.repository import (
    SqlAlchemyBrowserProfileRepository,
)
from agenttest.modules.identity.infrastructure.persistence.models import UserModel  # noqa: F401
from agenttest.modules.projects.infrastructure.persistence.models import ProjectModel  # noqa: F401
from agenttest.modules.runs.infrastructure.persistence.models import RunCaseModel  # noqa: F401
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.mark.asyncio
async def test_repository_crud_is_scoped_by_project() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(BrowserProfileModel.__table__.create)
    repository = SqlAlchemyBrowserProfileRepository(
        async_sessionmaker(engine, expire_on_commit=False)
    )
    project_id = uuid4()
    other_project_id = uuid4()
    item = BrowserProfile.create(
        project_id=project_id,
        name="TapNow",
        target_domain="app.tapnow.ai",
        created_by=uuid4(),
        now=datetime.now(UTC),
    )
    item.user_data_dir = "/runtime/profiles/one"

    await repository.add(item)

    assert await repository.get(project_id, item.id) == item
    assert await repository.get(other_project_id, item.id) is None
    assert await repository.list(other_project_id) == []
    assert await repository.list(project_id) == [item]

    saved_at = datetime.now(UTC)
    item.store_auth_state(envelope="v1.cipher", sha256="a" * 64, saved_at=saved_at)
    await repository.save(item)
    stored = await repository.get(project_id, item.id)
    assert stored is not None
    assert stored.auth_state_envelope == "v1.cipher"
    assert stored.auth_state_version == 1

    assert await repository.delete(other_project_id, item.id) is False
    assert await repository.delete(project_id, item.id) is True
    assert await repository.get(project_id, item.id) is None
    await engine.dispose()


@pytest.mark.asyncio
async def test_repository_enforces_unique_project_name() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(BrowserProfileModel.__table__.create)
    repository = SqlAlchemyBrowserProfileRepository(
        async_sessionmaker(engine, expire_on_commit=False)
    )
    project_id = uuid4()
    now = datetime.now(UTC)
    first = BrowserProfile.create(
        project_id=project_id,
        name="Primary",
        target_domain="app.tapnow.ai",
        created_by=uuid4(),
        now=now,
    )
    second = BrowserProfile.create(
        project_id=project_id,
        name="Primary",
        target_domain="app.tapnow.ai",
        created_by=uuid4(),
        now=now,
    )

    await repository.add(first)
    with pytest.raises(DuplicateBrowserProfile):
        await repository.add(second)
    await engine.dispose()
