from __future__ import annotations

import os
from asyncio import to_thread
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import asyncpg
import pytest
from agenttest.modules.audit.infrastructure.persistence.models import AuditLogModel
from agenttest.modules.datasets.infrastructure.persistence.models import TestCaseModel
from agenttest.modules.identity.infrastructure.persistence.models import (
    UserModel,
    UserSessionModel,
)
from agenttest.modules.projects.infrastructure.persistence.models import ProjectMemberModel
from agenttest.modules.run_postprocessing.infrastructure.models import (
    RunCalibrationModel,
    RunDiagnosticModel,
    RunJointGateDecisionModel,
    RunPostprocessJobModel,
    RunPostprocessStageResultModel,
    RunRegressionCandidateModel,
)
from alembic import command
from alembic.config import Config
from sqlalchemy import CheckConstraint, UniqueConstraint


def constraint_names(model: type[object]) -> set[str]:
    return {
        constraint.name
        for constraint in model.__table__.constraints  # type: ignore[attr-defined]
        if constraint.name is not None
    }


def test_users_enforce_normalized_email_and_valid_role_status() -> None:
    constraints = UserModel.__table__.constraints

    assert "uq_users_email_normalized" in constraint_names(UserModel)
    assert sum(isinstance(item, CheckConstraint) for item in constraints) == 2


def test_session_token_hash_is_unique() -> None:
    constraints = UserSessionModel.__table__.constraints

    assert any(
        isinstance(item, UniqueConstraint) and item.name == "uq_user_sessions_token_hash"
        for item in constraints
    )


def test_project_membership_is_unique_per_project_and_user() -> None:
    assert "uq_project_members_project_user" in constraint_names(ProjectMemberModel)


def test_audit_log_model_is_append_only() -> None:
    assert AuditLogModel.__mapper_args__["confirm_deleted_rows"] is False
    assert AuditLogModel.__table__.info["append_only"] is True


def test_test_case_execution_mode_allows_codex_explore() -> None:
    checks = {
        constraint.name: str(constraint.sqltext)
        for constraint in TestCaseModel.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "ck_test_cases_execution_mode" in checks
    assert "codex_explore" in checks["ck_test_cases_execution_mode"]


def test_run_trust_loop_records_are_project_scoped_and_idempotent() -> None:
    expected = {
        RunPostprocessJobModel: "uq_run_postprocess_jobs_project_run_pipeline",
        RunPostprocessStageResultModel: "uq_run_postprocess_stage_results_job_stage",
        RunDiagnosticModel: "uq_run_diagnostics_project_case_pipeline",
        RunRegressionCandidateModel: ("uq_run_regression_candidates_project_fingerprint_pipeline"),
        RunCalibrationModel: "uq_run_calibrations_project_run_pipeline",
        RunJointGateDecisionModel: "uq_run_joint_gate_decisions_project_run_pipeline",
    }

    for model, unique_name in expected.items():
        assert "project_id" in model.__table__.columns
        assert unique_name in constraint_names(model)


def postgres_dsn(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://")


@pytest.mark.asyncio
@pytest.mark.skipif(
    "AGENTTEST_TEST_DATABASE_URL" not in os.environ,
    reason="requires an isolated PostgreSQL database",
)
async def test_database_rejects_duplicate_identity_and_membership_values() -> None:
    database_url = os.environ["AGENTTEST_TEST_DATABASE_URL"]
    config = Config(Path("apps/control-api/alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    await to_thread(command.upgrade, config, "head")

    connection = await asyncpg.connect(postgres_dsn(database_url))
    now = datetime.now(UTC)
    user_id = uuid4()
    project_id = uuid4()
    try:
        async with connection.transaction():
            await connection.execute(
                """
                INSERT INTO users (
                    id, email, email_normalized, display_name, role, status,
                    must_change_password, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, false, $7, $7)
                """,
                user_id,
                "user@example.com",
                "user@example.com",
                "User",
                "developer",
                "active",
                now,
            )
            with pytest.raises(asyncpg.UniqueViolationError):
                async with connection.transaction():
                    await connection.execute(
                        """
                        INSERT INTO users (
                            id, email, email_normalized, display_name, role, status,
                            must_change_password, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, false, $7, $7)
                        """,
                        uuid4(),
                        "USER@example.com",
                        "user@example.com",
                        "Other User",
                        "tester",
                        "active",
                        now,
                    )

            token_hash = uuid4().hex + uuid4().hex
            await connection.execute(
                """
                INSERT INTO user_sessions (
                    id, user_id, token_hash, csrf_token_hash, expires_at, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                uuid4(),
                user_id,
                token_hash,
                uuid4().hex + uuid4().hex,
                now + timedelta(hours=8),
                now,
            )
            with pytest.raises(asyncpg.UniqueViolationError):
                async with connection.transaction():
                    await connection.execute(
                        """
                        INSERT INTO user_sessions (
                            id, user_id, token_hash, csrf_token_hash, expires_at, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        uuid4(),
                        user_id,
                        token_hash,
                        uuid4().hex + uuid4().hex,
                        now + timedelta(hours=8),
                        now,
                    )

            await connection.execute(
                """
                INSERT INTO projects (
                    id, name, created_at, updated_at, created_by, updated_by
                ) VALUES ($1, $2, $3, $3, $4, $4)
                """,
                project_id,
                "Project",
                now,
                user_id,
            )
            await connection.execute(
                """
                INSERT INTO project_members (
                    id, project_id, user_id, role, created_at, updated_at,
                    created_by, updated_by
                ) VALUES ($1, $2, $3, $4, $5, $5, $3, $3)
                """,
                uuid4(),
                project_id,
                user_id,
                "developer",
                now,
            )
            with pytest.raises(asyncpg.UniqueViolationError):
                async with connection.transaction():
                    await connection.execute(
                        """
                        INSERT INTO project_members (
                            id, project_id, user_id, role, created_at, updated_at,
                            created_by, updated_by
                        ) VALUES ($1, $2, $3, $4, $5, $5, $3, $3)
                        """,
                        uuid4(),
                        project_id,
                        user_id,
                        "tester",
                        now,
                    )
    finally:
        await connection.close()
