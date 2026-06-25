from __future__ import annotations

import os
from asyncio import to_thread
from datetime import UTC, datetime
from inspect import signature
from uuid import uuid4

import asyncpg
import pytest
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.domain.entities import (
    Project,
    ProjectId,
    ProjectMemberRole,
)
from agenttest.modules.projects.infrastructure.persistence.repositories import (
    SqlAlchemyProjectRepository,
)
from agenttest.shared.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)
from alembic import command
from alembic.config import Config


def test_project_repository_lookup_requires_project_id() -> None:
    parameters = signature(SqlAlchemyProjectRepository.get_by_id).parameters

    assert list(parameters) == ["self", "project_id"]


@pytest.mark.asyncio
@pytest.mark.skipif(
    "AGENTTEST_TEST_DATABASE_URL" not in os.environ,
    reason="requires an isolated PostgreSQL database",
)
async def test_removed_member_immediately_loses_project_listing() -> None:
    database_url = os.environ["AGENTTEST_TEST_DATABASE_URL"]
    config = Config("apps/control-api/alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    await to_thread(command.downgrade, config, "base")
    await to_thread(command.upgrade, config, "head")

    connection = await asyncpg.connect(
        database_url.replace("postgresql+asyncpg://", "postgresql://")
    )
    admin_id = uuid4()
    member_id = uuid4()
    now = datetime.now(UTC)
    try:
        for user_id, email, role in (
            (admin_id, "admin@example.com", "super_admin"),
            (member_id, "member@example.com", "developer"),
        ):
            await connection.execute(
                """
                INSERT INTO users (
                    id, email, email_normalized, display_name, role, status,
                    must_change_password, created_at, updated_at
                ) VALUES ($1, $2, $2, $2, $3, 'active', false, $4, $4)
                """,
                user_id,
                email,
                role,
                now,
            )
    finally:
        await connection.close()

    engine = create_database_engine(database_url)
    repository = SqlAlchemyProjectRepository(create_session_factory(engine))
    project = Project.create(
        project_id=ProjectId.new(),
        name="Assigned Project",
        created_by=UserId(admin_id),
    )
    project.add_member(UserId(member_id), ProjectMemberRole.DEVELOPER)
    await repository.add(project)

    assert [item.project_id for item in await repository.list_for_user(UserId(member_id))] == [
        project.project_id
    ]

    project.remove_member(UserId(member_id))
    await repository.save(project)

    assert await repository.list_for_user(UserId(member_id)) == []
    await engine.dispose()
