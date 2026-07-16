from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from uuid import uuid4

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
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()

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
    assert revision == ("0027",)
