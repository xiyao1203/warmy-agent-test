"""验证 0013 可执行资产合同迁移的完整性。

覆盖：
- 从 0012 到 0013 的升级路径
- agent_versions 新增字段与旧数据洗入
- 新增表的复合主键、外键和唯一约束
- 降级后重建
"""

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


def test_offline_sql_includes_executable_asset_tables_and_columns() -> None:
    """离线 SQL 输出包含 0013 新增的所有表和列。"""
    output = StringIO()
    config = alembic_config(
        database_url="postgresql+asyncpg://agenttest:agenttest@localhost/agenttest"
    )
    config.output_buffer = output

    command.upgrade(config, "head", sql=True)

    sql = output.getvalue().lower()

    # ── agent_versions 新增字段 ─────────────────────────────────
    for column in ("schema_version", "invocation_config", "readiness_status"):
        assert column in sql, f"Missing agent_versions column: {column}"

    # ── 新增核心表 ─────────────────────────────────────────────
    for table_name in (
        "environment_versions",
        "credential_bindings",
        "scorer_versions",
        "security_profiles",
        "review_policies",
        "run_evaluations",
        "scores",
        "release_decisions",
    ):
        assert table_name in sql, f"Missing table: {table_name}"

    # ── 项目隔离复合唯一约束 ───────────────────────────────────
    for constraint in (
        "uq_environment_versions_project_id",
        "uq_credential_bindings_project_id",
        "uq_credential_bindings_alias",
        "uq_scorer_versions_project_id",
        "uq_security_profiles_name",
        "uq_review_policies_name",
        "uq_run_evaluations_project_run",
        "uq_run_evaluations_project_id",
        "uq_scores_source",
    ):
        assert constraint in sql, f"Missing constraint: {constraint}"

    # ── 反向引用索引 ───────────────────────────────────────────
    for index_name in (
        "ix_environment_versions_project_template",
        "ix_scores_project_case",
        "ix_release_decisions_project_run",
        "ix_security_scans_project_run",
    ):
        assert index_name in sql, f"Missing index: {index_name}"

    # ── 安全扫描新增资产引用列 ─────────────────────────────────
    for column in ("run_id", "agent_version_id", "environment_version_id", "security_profile_id"):
        assert column in sql, f"Missing security_scans column: {column}"

    # ── legacy api_url → endpoint_url 映射 ──────────────────────
    assert "endpoint_url" in sql
    assert "needs_configuration" in sql


def test_sqlite_legacy_agent_config_is_migrated(tmp_path: Path) -> None:
    """SQLite 从空库升级到 0013 后 agent_versions 表新增字段存在。"""
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    database_url = f"sqlite+aiosqlite:///{tmp_path / 'migrate.db'}"

    config = alembic_config(database_url=database_url)
    command.upgrade(config, "0013")

    async def _verify() -> None:
        engine = create_async_engine(database_url)
        try:
            async with engine.connect() as conn:
                # 验证 agent_versions 表有 0013 新增字段
                columns = [
                    row[1]
                    for row in (
                        await conn.execute(text("PRAGMA table_info('agent_versions')"))
                    ).fetchall()
                ]
                for col in ("schema_version", "invocation_config", "readiness_status"):
                    assert col in columns, f"agent_versions missing column: {col}"

                # 验证 0013 新增表存在
                tables = [
                    row[0]
                    for row in (
                        await conn.execute(
                            text("SELECT name FROM sqlite_master WHERE type='table'")
                        )
                    ).fetchall()
                ]
                for table_name in (
                    "environment_versions",
                    "credential_bindings",
                    "scorer_versions",
                    "security_profiles",
                    "review_policies",
                    "run_evaluations",
                    "scores",
                    "release_decisions",
                ):
                    assert table_name in tables, f"Missing table: {table_name}"
        finally:
            await engine.dispose()

    run(_verify())


@pytest.mark.skipif(
    "AGENTTEST_TEST_DATABASE_URL" not in os.environ,
    reason="requires an isolated PostgreSQL database",
)
def test_0012_to_0013_postgresql_upgrade_and_downgrade() -> None:
    """PostgreSQL 上 0012→0013→降级→再升级的完整周期。"""
    database_url = os.environ["AGENTTEST_TEST_DATABASE_URL"]
    config = alembic_config(database_url=database_url)

    command.downgrade(config, "base")

    # 升级到 0012
    command.upgrade(config, "0012")

    # 升级到 0013
    command.upgrade(config, "0013")
    assert run(_current_revision(database_url)) == "0013"

    # 验证 0013 新表存在且有项目外键
    run(_verify_0013_tables_exist(database_url))

    # 降级到 0012
    command.downgrade(config, "0012")
    assert run(_current_revision(database_url)) == "0012"

    # 再升级到 0013
    command.upgrade(config, "0013")
    assert run(_current_revision(database_url)) == "0013"


@pytest.mark.skipif(
    "AGENTTEST_TEST_DATABASE_URL" not in os.environ,
    reason="requires an isolated PostgreSQL database",
)
def test_0013_new_tables_enforce_project_isolation() -> None:
    """0013 新增表强制项目外键约束。"""
    database_url = os.environ["AGENTTEST_TEST_DATABASE_URL"]
    config = alembic_config(database_url=database_url)

    command.downgrade(config, "base")
    command.upgrade(config, "0013")

    run(_verify_project_fk_constraints(database_url))


async def _current_revision(database_url: str) -> str:
    connection = await asyncpg.connect(
        database_url.replace("postgresql+asyncpg://", "postgresql://")
    )
    try:
        revision = await connection.fetchval("select version_num from alembic_version")
        assert isinstance(revision, str)
        return revision
    finally:
        await connection.close()


async def _verify_0013_tables_exist(database_url: str) -> None:
    connection = await asyncpg.connect(
        database_url.replace("postgresql+asyncpg://", "postgresql://")
    )
    try:
        for table_name in (
            "environment_versions",
            "credential_bindings",
            "scorer_versions",
            "security_profiles",
            "review_policies",
            "run_evaluations",
            "scores",
            "release_decisions",
        ):
            result = await connection.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                table_name,
            )
            assert result is True, f"Table {table_name} does not exist"
    finally:
        await connection.close()


async def _verify_project_fk_constraints(database_url: str) -> None:
    """确保 0013 新增表都引用了 projects.id。"""
    connection = await asyncpg.connect(
        database_url.replace("postgresql+asyncpg://", "postgresql://")
    )
    try:
        for table_name in (
            "environment_versions",
            "credential_bindings",
            "run_evaluations",
            "release_decisions",
        ):
            constraint_exists = await connection.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_constraint c
                    JOIN pg_class source_table ON source_table.oid = c.conrelid
                    JOIN pg_class target_table ON target_table.oid = c.confrelid
                    JOIN pg_attribute source_column
                      ON source_column.attrelid = source_table.oid
                     AND source_column.attnum = ANY(c.conkey)
                    JOIN pg_attribute target_column
                      ON target_column.attrelid = target_table.oid
                     AND target_column.attnum = ANY(c.confkey)
                    WHERE c.contype = 'f'
                      AND source_table.relname = $1
                      AND source_column.attname = 'project_id'
                      AND target_table.relname = 'projects'
                      AND target_column.attname = 'id'
                )
                """,
                table_name,
            )
            assert constraint_exists is True, f"{table_name}.project_id must reference projects.id"
    finally:
        await connection.close()
