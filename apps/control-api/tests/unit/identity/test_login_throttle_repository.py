from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from agenttest.modules.identity.infrastructure.persistence.models import LoginThrottleModel
from agenttest.modules.identity.infrastructure.persistence.repositories import (
    SqlAlchemyLoginThrottleRepository,
)
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


@pytest.mark.asyncio
async def test_sqlite_repository_atomically_updates_resets_clears_and_expires(
    tmp_path: Path,
) -> None:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'throttle.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(LoginThrottleModel.__table__.create)
    repository = SqlAlchemyLoginThrottleRepository(
        async_sessionmaker(engine, expire_on_commit=False)
    )
    now = datetime(2026, 7, 16, 9, 0, tzinfo=UTC)
    window = timedelta(minutes=15)
    blocked_for = timedelta(minutes=30)

    for expected_count in range(1, 9):
        entry = await repository.record_failure(
            "a" * 64,
            now=now,
            window=window,
            max_failures=8,
            blocked_for=blocked_for,
        )
        assert entry.failure_count == expected_count
    assert entry.blocked_until is not None

    first_failure_block = await repository.record_failure(
        "c" * 64,
        now=now,
        window=window,
        max_failures=1,
        blocked_for=blocked_for,
    )
    assert first_failure_block.blocked_until == now + blocked_for

    await repository.record_failure(
        "b" * 64,
        now=now,
        window=window,
        max_failures=8,
        blocked_for=blocked_for,
    )
    reset = await repository.record_failure(
        "b" * 64,
        now=now + window + timedelta(seconds=1),
        window=window,
        max_failures=8,
        blocked_for=blocked_for,
    )
    assert reset.failure_count == 1

    assert await repository.delete_expired(now + timedelta(seconds=1), limit=1) == 1
    await repository.clear(("b" * 64,))
    assert await repository.get("b" * 64) is None

    await engine.dispose()
