from __future__ import annotations

import os
from asyncio import run
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from uuid import uuid4

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
    assert "test_agent_sessions" in sql
    assert "test_agent_messages" in sql
    assert "fk_test_agent_messages_project_session" in sql
    assert "uq_test_agent_messages_sequence" in sql
    for table_name in (
        "environment_versions",
        "credential_bindings",
        "scorer_versions",
        "run_evaluations",
        "scores",
        "security_profiles",
        "review_policies",
        "release_decisions",
    ):
        assert table_name in sql
    assert "invocation_config" in sql
    assert "ix_release_decisions_project_run" in sql
    assert "test_agent_chat_generations" in sql
    assert "fk_test_agent_events_project_generation" in sql
    assert "browser_profiles" in sql
    assert "uq_browser_profiles_project_name" in sql
    assert "ix_browser_profiles_project_updated" in sql
    assert "ix_browser_profiles_project_status" in sql
    assert "test_missions" in sql
    assert "test_mission_facts" in sql
    assert "test_mission_revisions" in sql
    assert "test_mission_assets" in sql
    assert "test_mission_events" in sql
    assert "test_mission_stage_receipts" in sql
    assert "uq_mission_facts_project_mission_key" in sql
    assert "ix_mission_events_project_mission_sequence" in sql
    assert "alter table audit.audit_logs set schema public" in sql
    assert "add column session_id varchar(255)" in sql
    assert "fk_artifacts_project_run" in sql


def test_empty_sqlite_database_upgrades_to_head(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'migration.db'}"
    config = alembic_config(database_url=database_url)

    command.upgrade(config, "head")

    assert run(current_sqlite_revision(database_url)) == "0025"


def test_sqlite_backfills_existing_scorer_versions(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'scorer-backfill.db'}"
    config = alembic_config(database_url=database_url)

    command.upgrade(config, "0015")
    scorer_id = run(insert_legacy_scorer(database_url))
    command.upgrade(config, "head")

    version = run(read_scorer_version(database_url, scorer_id))
    assert version is not None
    assert version["status"] == "published"
    assert version["version_number"] == 1


@pytest.mark.skipif(
    "AGENTTEST_TEST_DATABASE_URL" not in os.environ,
    reason="requires an isolated PostgreSQL database",
)
def test_empty_database_upgrade_and_revision_cycle() -> None:
    database_url = os.environ["AGENTTEST_TEST_DATABASE_URL"]
    config = alembic_config(database_url=database_url)

    command.upgrade(config, "head")
    assert run(current_revision(database_url)) == "0025"

    command.downgrade(config, "base")
    command.upgrade(config, "head")
    assert run(current_revision(database_url)) == "0025"


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


async def current_sqlite_revision(database_url: str) -> str:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as connection:
            revision = await connection.scalar(text("select version_num from alembic_version"))
            assert isinstance(revision, str)
            return revision
    finally:
        await engine.dispose()


async def insert_legacy_scorer(database_url: str) -> str:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(database_url)
    user_id = uuid4().hex
    project_id = uuid4().hex
    member_id = uuid4().hex
    scorer_id = uuid4().hex
    now = datetime.now(UTC)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    INSERT INTO users (
                        id, email, email_normalized, display_name, role, status,
                        must_change_password, created_at, updated_at
                    ) VALUES (
                        :id, :email, :email, :display_name, 'developer', 'active',
                        false, :now, :now
                    )
                    """
                ),
                {
                    "id": user_id,
                    "email": "scorer-owner@example.com",
                    "display_name": "Scorer Owner",
                    "now": now,
                },
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO projects (
                        id, name, description, archived_at, created_at, updated_at,
                        created_by, updated_by
                    ) VALUES (
                        :id, '评分项目', null, null, :now, :now, :user_id, :user_id
                    )
                    """
                ),
                {"id": project_id, "now": now, "user_id": user_id},
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO project_members (
                        id, project_id, user_id, role, created_at, updated_at,
                        created_by, updated_by
                    ) VALUES (
                        :id, :project_id, :user_id, 'developer', :now, :now,
                        :user_id, :user_id
                    )
                    """
                ),
                {
                    "id": member_id,
                    "project_id": project_id,
                    "user_id": user_id,
                    "now": now,
                },
            )
            await connection.execute(
                text(
                    """
                    INSERT INTO scorers (
                        id, project_id, name, scorer_type, weight, threshold,
                        config_json, description, enabled, created_at, updated_at
                    ) VALUES (
                        :id, :project_id, '事实评分', 'rule', 1.0, 0.8,
                        :config_json, null, true, :now, :now
                    )
                    """
                ),
                {
                    "id": scorer_id,
                    "project_id": project_id,
                    "config_json": '{"operator":"contains","expected":"ok"}',
                    "now": now,
                },
            )
    finally:
        await engine.dispose()
    return scorer_id


async def read_scorer_version(database_url: str, scorer_id: str) -> dict[str, object] | None:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(database_url)
    try:
        async with engine.connect() as connection:
            row = (
                (
                    await connection.execute(
                        text(
                            """
                        SELECT status, version_number
                        FROM scorer_versions
                        WHERE scorer_id = :scorer_id
                        """
                        ),
                        {"scorer_id": scorer_id},
                    )
                )
                .mappings()
                .first()
            )
            return dict(row) if row else None
    finally:
        await engine.dispose()
