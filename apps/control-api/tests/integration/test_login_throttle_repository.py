from __future__ import annotations

import os
from asyncio import gather, to_thread
from datetime import UTC, datetime, timedelta

import pytest
from agenttest.modules.identity.infrastructure.persistence.repositories import (
    SqlAlchemyLoginThrottleRepository,
)
from agenttest.shared.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)
from alembic import command
from alembic.config import Config


@pytest.mark.asyncio
@pytest.mark.skipif(
    "AGENTTEST_TEST_DATABASE_URL" not in os.environ,
    reason="requires an isolated PostgreSQL database",
)
async def test_postgresql_concurrent_failures_are_counted_atomically() -> None:
    database_url = os.environ["AGENTTEST_TEST_DATABASE_URL"]
    config = Config("apps/control-api/alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    await to_thread(command.upgrade, config, "head")
    repository = SqlAlchemyLoginThrottleRepository(
        create_session_factory(create_database_engine(database_url))
    )
    key_hash = "f" * 64
    now = datetime(2026, 7, 16, 9, 0, tzinfo=UTC)
    await repository.clear((key_hash,))

    entries = await gather(
        *(
            repository.record_failure(
                key_hash,
                now=now,
                window=timedelta(minutes=15),
                max_failures=8,
                blocked_for=timedelta(minutes=30),
            )
            for _ in range(8)
        )
    )

    stored = await repository.get(key_hash)
    assert sorted(entry.failure_count for entry in entries) == list(range(1, 9))
    assert stored is not None
    assert stored.failure_count == 8
    assert stored.blocked_until == now + timedelta(minutes=30)
    await repository.clear((key_hash,))
