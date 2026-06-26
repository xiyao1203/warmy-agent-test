from __future__ import annotations

from agenttest.modules.runs.infrastructure.persistence.models import (
    RunCaseModel,
    RunEventModel,
    RunModel,
)
from sqlalchemy import CheckConstraint, Index, UniqueConstraint


def test_run_tables_enforce_project_isolation_and_idempotency() -> None:
    assert RunModel.__table__.c.project_id.nullable is False
    unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in RunModel.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("project_id", "idempotency_key") in unique_columns

    indexes = {
        tuple(expression.name for expression in index.expressions)
        for index in RunModel.__table__.indexes
        if isinstance(index, Index)
    }
    assert ("project_id", "status", "created_at") in indexes


def test_run_case_and_event_tables_are_append_scoped_to_run() -> None:
    assert RunCaseModel.__table__.c.run_id.nullable is False
    assert RunEventModel.__table__.c.run_id.nullable is False
    assert RunEventModel.__table__.c.sequence.nullable is False

    case_checks = {
        constraint.name
        for constraint in RunCaseModel.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert "ck_run_cases_status" in case_checks
