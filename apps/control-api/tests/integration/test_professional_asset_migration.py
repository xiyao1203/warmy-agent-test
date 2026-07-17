from __future__ import annotations

import json
import os
import sqlite3
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


def _config(database_url: str) -> Config:
    config = Config(ALEMBIC_CONFIG_PATH)
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_offline_sql_contains_professional_asset_contract() -> None:
    output = StringIO()
    config = _config("postgresql+asyncpg://agenttest:agenttest@localhost/agenttest")
    config.output_buffer = output

    command.upgrade(config, "head", sql=True)

    sql = output.getvalue().lower()
    assert "project_sequences" in sql
    assert "case_key" in sql
    assert "objective" in sql
    assert "data_bindings" in sql
    assert "steps" in sql
    assert "postconditions" in sql
    assert "run_type" in sql
    assert "source_test_case_id" in sql
    assert "case_spec_snapshot" in sql
    assert "jsonb" in sql
    assert "ix_runs_project_created_latest" in sql
    assert "ix_runs_project_agent_created" in sql
    assert "ix_runs_project_plan_created" in sql
    assert "ix_release_decisions_project_gate_created" in sql
    assert "0027" in sql


def test_legacy_project_and_case_are_backfilled_on_sqlite(tmp_path: Path) -> None:
    database_path = tmp_path / "professional-assets.db"
    config = _config(f"sqlite+aiosqlite:///{database_path}")
    command.upgrade(config, "0026")

    user_id = uuid4().hex
    project_id = uuid4().hex
    dataset_id = uuid4().hex
    version_id = uuid4().hex
    case_id = uuid4().hex
    draft_case_id = uuid4().hex
    now = datetime.now(UTC).isoformat()
    empty_list = json.dumps([])
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            INSERT INTO users (
                id, email, email_normalized, display_name, role, status,
                must_change_password, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'super_admin', 'active', false, ?, ?)
            """,
            (user_id, "owner@example.test", "owner@example.test", "Owner", now, now),
        )
        connection.execute(
            """
            INSERT INTO projects (
                id, name, description, archived_at, created_at, updated_at,
                created_by, updated_by
            ) VALUES (?, 'Legacy', 'Existing description', null, ?, ?, ?, ?)
            """,
            (project_id, now, now, user_id, user_id),
        )
        connection.execute(
            """
            INSERT INTO datasets (
                id, project_id, name, description, created_at, updated_at,
                created_by, updated_by
            ) VALUES (?, ?, 'Legacy data', null, ?, ?, ?, ?)
            """,
            (dataset_id, project_id, now, now, user_id, user_id),
        )
        connection.execute(
            """
            INSERT INTO dataset_versions (
                id, dataset_id, version_number, status, published_at,
                created_at, updated_at, created_by
            ) VALUES (?, ?, 1, 'published', ?, ?, ?, ?)
            """,
            (version_id, dataset_id, now, now, now, user_id),
        )
        connection.execute(
            """
            INSERT INTO test_cases (
                id, dataset_version_id, name, input, initial_state, execution_mode,
                expected_outcome, assertions, scorers, security_policies, tags,
                scenario, priority, risk_level, difficulty, test_group, sort_order,
                created_at, updated_at
            ) VALUES (
                ?, ?, 'Legacy case', ?, null, 'api', null, ?, ?, ?, ?,
                'Legacy objective', 'P1', 'high', 'medium', 'test', 1, ?, ?
            )
            """,
            (
                case_id,
                version_id,
                json.dumps({"message": "hello"}),
                json.dumps([{"type": "contains"}]),
                empty_list,
                empty_list,
                empty_list,
                now,
                now,
            ),
        )
        connection.execute(
            """
            INSERT INTO test_cases (
                id, dataset_version_id, name, input, initial_state, execution_mode,
                expected_outcome, assertions, scorers, security_policies, tags,
                scenario, priority, risk_level, difficulty, test_group, sort_order,
                created_at, updated_at
            ) VALUES (
                ?, ?, 'Legacy case without oracle', ?, null, 'api', null, ?, ?, ?, ?,
                null, 'P2', 'medium', 'medium', 'test', 2, ?, ?
            )
            """,
            (
                draft_case_id,
                version_id,
                json.dumps({"message": "hello"}),
                empty_list,
                empty_list,
                empty_list,
                empty_list,
                now,
                now,
            ),
        )
        connection.commit()

    command.upgrade(config, "head")

    with sqlite3.connect(database_path) as connection:
        project = connection.execute(
            "SELECT key, description FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        case = connection.execute(
            """
            SELECT case_key, objective, case_status, template, automation_status,
                   source, preconditions, steps, postconditions, created_by, updated_by
            FROM test_cases WHERE id = ?
            """,
            (case_id,),
        ).fetchone()
        draft_status = connection.execute(
            "SELECT case_status FROM test_cases WHERE id = ?", (draft_case_id,)
        ).fetchone()
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
        run_columns = {row[1] for row in connection.execute("PRAGMA table_info(runs)").fetchall()}
        run_case_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(run_cases)").fetchall()
        }
        performance_indexes = {
            row[0]
            for row in connection.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'index' AND name LIKE 'ix_%_created%'
                """
            ).fetchall()
        }

    assert project is not None
    assert project[0].startswith("P")
    assert project[1] == "Existing description"
    assert case is not None
    assert case[0].startswith(f"{project[0]}-TC-")
    assert case[1] == "Legacy objective"
    assert case[2:6] == ("ready", "ai_eval", "automated", "manual")
    assert json.loads(case[6]) == []
    assert json.loads(case[7]) == []
    assert json.loads(case[8]) == []
    assert case[9:] == (user_id, user_id)
    assert draft_status == ("draft",)
    assert {"run_type", "source_test_case_id"} <= run_columns
    assert "case_spec_snapshot" in run_case_columns
    assert {
        "ix_runs_project_created_latest",
        "ix_runs_project_agent_created",
        "ix_runs_project_plan_created",
        "ix_release_decisions_project_gate_created",
    } <= performance_indexes
    assert revision == ("0027",)


@pytest.mark.skipif(
    "AGENTTEST_TEST_DATABASE_URL" not in os.environ,
    reason="requires an isolated PostgreSQL database",
)
def test_legacy_project_and_case_are_backfilled_on_postgresql() -> None:
    database_url = os.environ["AGENTTEST_TEST_DATABASE_URL"]
    config = _config(database_url)
    command.downgrade(config, "base")
    command.upgrade(config, "0026")

    identifiers = run(_seed_legacy_postgresql(database_url))
    command.upgrade(config, "head")
    result = run(_read_professional_postgresql(database_url, identifiers))

    assert result["revision"] == "0027"
    assert str(result["project_key"]).startswith("P")
    assert result["project_description"] == "Existing description"
    assert str(result["case_key"]).startswith(f"{result['project_key']}-TC-")
    assert result["objective"] == "Legacy objective"
    assert result["case_status"] == "ready"
    assert result["draft_case_status"] == "draft"
    assert result["template"] == "ai_eval"
    assert result["automation_status"] == "automated"
    assert result["source"] == "manual"
    assert result["preconditions"] == []
    assert result["steps"] == []
    assert result["postconditions"] == []
    assert result["created_by"] == identifiers["user_id"]
    assert result["updated_by"] == identifiers["user_id"]
    assert result["next_value"] == 3
    assert {
        "ix_test_cases_version_status",
        "ix_test_cases_version_type",
        "ix_test_cases_version_automation",
    } <= result["indexes"]
    assert {
        "uq_test_cases_case_key",
        "fk_test_cases_created_by",
        "fk_test_cases_updated_by",
    } <= result["constraints"]
    assert {"run_type", "source_test_case_id"} <= result["run_columns"]
    assert "case_spec_snapshot" in result["run_case_columns"]
    assert set(result["professional_json_types"].values()) == {"jsonb"}
    assert {
        "ix_runs_project_created_latest",
        "ix_runs_project_agent_created",
        "ix_runs_project_plan_created",
        "ix_release_decisions_project_gate_created",
    } <= result["performance_indexes"]


async def _seed_legacy_postgresql(database_url: str) -> dict[str, object]:
    connection = await asyncpg.connect(_postgres_dsn(database_url))
    user_id = uuid4()
    project_id = uuid4()
    dataset_id = uuid4()
    version_id = uuid4()
    case_id = uuid4()
    draft_case_id = uuid4()
    now = datetime.now(UTC)
    try:
        async with connection.transaction():
            await connection.execute(
                """
                INSERT INTO users (
                    id, email, email_normalized, display_name, role, status,
                    must_change_password, created_at, updated_at
                ) VALUES ($1, $2, $2, 'Owner', 'super_admin', 'active', false, $3, $3)
                """,
                user_id,
                f"owner-{user_id}@example.test",
                now,
            )
            await connection.execute(
                """
                INSERT INTO projects (
                    id, name, description, archived_at, created_at, updated_at,
                    created_by, updated_by
                ) VALUES ($1, 'Legacy', 'Existing description', null, $2, $2, $3, $3)
                """,
                project_id,
                now,
                user_id,
            )
            await connection.execute(
                """
                INSERT INTO datasets (
                    id, project_id, name, description, created_at, updated_at,
                    created_by, updated_by
                ) VALUES ($1, $2, 'Legacy data', null, $3, $3, $4, $4)
                """,
                dataset_id,
                project_id,
                now,
                user_id,
            )
            await connection.execute(
                """
                INSERT INTO dataset_versions (
                    id, dataset_id, version_number, status, published_at,
                    created_at, updated_at, created_by
                ) VALUES ($1, $2, 1, 'published', $3, $3, $3, $4)
                """,
                version_id,
                dataset_id,
                now,
                user_id,
            )
            await connection.execute(
                """
                INSERT INTO test_cases (
                    id, dataset_version_id, name, input, initial_state, execution_mode,
                    expected_outcome, assertions, scorers, security_policies, tags,
                    scenario, priority, risk_level, difficulty, test_group, sort_order,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, 'Legacy case', $3, null, 'api', null, $4, $5, $5, $5,
                    'Legacy objective', 'P1', 'high', 'medium', 'test', 1, $6, $6
                )
                """,
                case_id,
                version_id,
                json.dumps({"message": "hello"}),
                json.dumps([{"type": "contains"}]),
                json.dumps([]),
                now,
            )
            await connection.execute(
                """
                INSERT INTO test_cases (
                    id, dataset_version_id, name, input, initial_state, execution_mode,
                    expected_outcome, assertions, scorers, security_policies, tags,
                    scenario, priority, risk_level, difficulty, test_group, sort_order,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, 'Legacy case without oracle', $3, null, 'api', null,
                    $4, $4, $4, $4, null, 'P2', 'medium', 'medium', 'test', 2, $5, $5
                )
                """,
                draft_case_id,
                version_id,
                json.dumps({"message": "hello"}),
                json.dumps([]),
                now,
            )
    finally:
        await connection.close()
    return {
        "case_id": case_id,
        "draft_case_id": draft_case_id,
        "project_id": project_id,
        "user_id": user_id,
    }


async def _read_professional_postgresql(
    database_url: str,
    identifiers: dict[str, object],
) -> dict[str, object]:
    connection = await asyncpg.connect(_postgres_dsn(database_url))
    try:
        project = await connection.fetchrow(
            "SELECT key, description FROM projects WHERE id = $1",
            identifiers["project_id"],
        )
        case = await connection.fetchrow(
            """
            SELECT case_key, objective, case_status, template, automation_status,
                   source, preconditions, steps, postconditions, created_by, updated_by
            FROM test_cases WHERE id = $1
            """,
            identifiers["case_id"],
        )
        assert project is not None
        assert case is not None
        indexes = {
            row["indexname"]
            for row in await connection.fetch(
                "SELECT indexname FROM pg_indexes WHERE tablename = 'test_cases'"
            )
        }
        constraints = {
            row["conname"]
            for row in await connection.fetch(
                """
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = 'test_cases'::regclass
                """
            )
        }
        run_columns = {
            row["column_name"]
            for row in await connection.fetch(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'runs'
                """
            )
        }
        run_case_columns = {
            row["column_name"]
            for row in await connection.fetch(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'run_cases'
                """
            )
        }
        professional_json_types = {
            row["column_name"]: row["data_type"]
            for row in await connection.fetch(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'test_cases'
                  AND column_name IN (
                    'requirement_refs', 'preconditions', 'data_bindings', 'steps',
                    'artifact_requirements', 'postconditions', 'custom_fields'
                  )
                """
            )
        }
        performance_indexes = {
            row["indexname"]
            for row in await connection.fetch(
                """
                SELECT indexname FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename IN ('runs', 'release_decisions')
                """
            )
        }
        return {
            "automation_status": case["automation_status"],
            "case_key": case["case_key"],
            "case_status": case["case_status"],
            "draft_case_status": await connection.fetchval(
                "SELECT case_status FROM test_cases WHERE id = $1",
                identifiers["draft_case_id"],
            ),
            "constraints": constraints,
            "created_by": case["created_by"],
            "indexes": indexes,
            "next_value": await connection.fetchval(
                """
                SELECT next_value FROM project_sequences
                WHERE project_id = $1 AND resource_type = 'test_case'
                """,
                identifiers["project_id"],
            ),
            "objective": case["objective"],
            "postconditions": json.loads(case["postconditions"]),
            "professional_json_types": professional_json_types,
            "performance_indexes": performance_indexes,
            "preconditions": json.loads(case["preconditions"]),
            "project_description": project["description"],
            "project_key": project["key"],
            "revision": await connection.fetchval("SELECT version_num FROM alembic_version"),
            "run_case_columns": run_case_columns,
            "run_columns": run_columns,
            "source": case["source"],
            "steps": json.loads(case["steps"]),
            "template": case["template"],
            "updated_by": case["updated_by"],
        }
    finally:
        await connection.close()


def _postgres_dsn(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://")
