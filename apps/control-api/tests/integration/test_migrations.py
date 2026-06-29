from __future__ import annotations

import os
from asyncio import run
from io import StringIO
from pathlib import Path

import asyncpg
import pytest
from alembic import command
from alembic.config import Config

ALEMBIC_CONFIG_PATH = Path("apps/control-api/alembic.ini")


def alembic_config(*, database_url: str | None = None) -> Config:
    config = Config(ALEMBIC_CONFIG_PATH)
    if database_url is not None:
        config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_initial_migration_generates_expected_postgresql_schema() -> None:
    output = StringIO()
    config = alembic_config(
        database_url="postgresql+asyncpg://agenttest:agenttest@localhost/agenttest"
    )
    config.output_buffer = output

    command.upgrade(config, "head", sql=True)

    sql = output.getvalue().lower()
    assert "create schema" in sql and "audit" in sql
    for table_name in (
        "users",
        "user_credentials",
        "user_sessions",
        "projects",
        "project_members",
        "audit_logs",
    ):
        assert "create table" in sql and table_name in sql
    assert "uq_users_email_normalized" in sql
    assert "uq_user_sessions_token_hash" in sql
    assert "uq_project_members_project_user" in sql
    assert "ix_user_sessions_user_expires" in sql
    assert "ix_projects_created_at_desc" in sql
    assert "ix_audit_logs_project_created_at_desc" in sql
    assert "model_configurations" in sql
    assert "project_model_defaults" in sql
    assert "uq_model_configs_project_name" in sql
    assert "uq_project_model_defaults_project_purpose" in sql


@pytest.mark.skipif(
    "AGENTTEST_TEST_DATABASE_URL" not in os.environ,
    reason="requires an isolated PostgreSQL database",
)
def test_empty_database_upgrade_and_revision_cycle() -> None:
    database_url = os.environ["AGENTTEST_TEST_DATABASE_URL"]
    config = alembic_config(database_url=database_url)

    command.upgrade(config, "head")
    assert run(current_revision(database_url)) == "0009"

    command.downgrade(config, "base")
    command.upgrade(config, "head")
    assert run(current_revision(database_url)) == "0009"


async def current_revision(database_url: str) -> str:
    connection = await asyncpg.connect(
        database_url.replace("postgresql+asyncpg://", "postgresql://")
    )
    try:
        revision = await connection.fetchval("select version_num from alembic_version")
        assert isinstance(revision, str)
        return revision
    finally:
        await connection.close()
