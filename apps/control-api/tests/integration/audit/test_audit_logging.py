from __future__ import annotations

import os
from asyncio import to_thread
from datetime import UTC, datetime
from uuid import uuid4

import asyncpg
import pytest
from agenttest.modules.audit.application.ports import AuditEntry
from agenttest.modules.audit.application.record import AuditRecorder
from agenttest.modules.audit.infrastructure.persistence.repositories import (
    SqlAlchemyAuditRepository,
)
from agenttest.modules.identity.infrastructure.persistence.models import UserModel
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.shared.infrastructure.database import (
    SqlAlchemyUnitOfWork,
    create_database_engine,
    create_session_factory,
    current_database_session,
)
from alembic import command
from alembic.config import Config


class FakeAuditSink:
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    async def append(self, entry: AuditEntry) -> None:
        self.entries.append(entry)


@pytest.mark.asyncio
async def test_audit_recorder_redacts_secret_changes() -> None:
    sink = FakeAuditSink()
    recorder = AuditRecorder(sink)

    await recorder.record(
        actor_user_id=UserId.new(),
        action="identity.user.reset_password",
        object_type="user",
        object_id=uuid4(),
        project_id=None,
        changes={
            "display_name": {"before": "Old", "after": "New"},
            "password": {"before": "old-secret", "after": "new-secret"},
            "session_token": {"after": "raw-token"},
            "cookie": {"after": "session=value"},
        },
        source_ip="127.0.0.1",
    )

    entry = sink.entries[0]
    assert entry.changes["display_name"] == {"before": "Old", "after": "New"}
    assert entry.changes["password"] == {"before": "[REDACTED]", "after": "[REDACTED]"}
    assert entry.changes["session_token"] == {"after": "[REDACTED]"}
    assert entry.changes["cookie"] == {"after": "[REDACTED]"}


@pytest.mark.asyncio
async def test_audit_entry_keeps_actor_object_project_and_source_ip() -> None:
    sink = FakeAuditSink()
    recorder = AuditRecorder(sink)
    actor_id = UserId.new()
    object_id = uuid4()
    project_id = ProjectId.new()

    await recorder.record(
        actor_user_id=actor_id,
        action="projects.member.add",
        object_type="project_member",
        object_id=object_id,
        project_id=project_id,
        changes={"role": {"after": "tester"}},
        source_ip="192.0.2.10",
    )

    entry = sink.entries[0]
    assert entry.actor_user_id == actor_id
    assert entry.object_id == object_id
    assert entry.project_id == project_id
    assert entry.source_ip == "192.0.2.10"


@pytest.mark.asyncio
@pytest.mark.skipif(
    "AGENTTEST_TEST_DATABASE_URL" not in os.environ,
    reason="requires an isolated PostgreSQL database",
)
async def test_business_and_audit_rows_roll_back_together() -> None:
    database_url = os.environ["AGENTTEST_TEST_DATABASE_URL"]
    config = Config("apps/control-api/alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    await to_thread(command.downgrade, config, "base")
    await to_thread(command.upgrade, config, "head")

    engine = create_database_engine(database_url)
    session_factory = create_session_factory(engine)
    audit_repository = SqlAlchemyAuditRepository(session_factory)
    user_id = uuid4()
    entry_id = uuid4()
    now = datetime.now(UTC)

    with pytest.raises(RuntimeError):
        async with SqlAlchemyUnitOfWork(session_factory):
            session = current_database_session()
            assert session is not None
            session.add(
                UserModel(
                    id=user_id,
                    email="rollback@example.com",
                    email_normalized="rollback@example.com",
                    display_name="Rollback",
                    role="developer",
                    status="active",
                    must_change_password=False,
                    created_at=now,
                    updated_at=now,
                    created_by=None,
                    updated_by=None,
                )
            )
            await audit_repository.append(
                AuditEntry(
                    entry_id=entry_id,
                    actor_user_id=UserId(user_id),
                    action="test.rollback",
                    object_type="user",
                    object_id=user_id,
                    project_id=None,
                    changes={},
                    source_ip=None,
                    created_at=now,
                )
            )
            raise RuntimeError("force rollback")

    connection = await asyncpg.connect(
        database_url.replace("postgresql+asyncpg://", "postgresql://")
    )
    try:
        assert await connection.fetchval("select count(*) from users where id = $1", user_id) == 0
        assert (
            await connection.fetchval(
                "select count(*) from audit.audit_logs where id = $1",
                entry_id,
            )
            == 0
        )
    finally:
        await connection.close()
        await engine.dispose()
