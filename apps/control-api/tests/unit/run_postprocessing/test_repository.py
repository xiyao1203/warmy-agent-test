from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from agenttest.modules.run_postprocessing.domain import RunPostprocessJob
from agenttest.modules.run_postprocessing.infrastructure import repository as repository_module
from agenttest.modules.run_postprocessing.infrastructure.models import (
    RunDiagnosticModel,
    RunPostprocessJobModel,
    RunPostprocessStageResultModel,
    RunRegressionCandidateModel,
)
from agenttest.modules.run_postprocessing.infrastructure.repository import (
    SqlAlchemyPostprocessRepository,
)


@pytest.mark.asyncio
async def test_create_or_get_adds_one_project_scoped_job(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()
    session.add = Mock()

    @asynccontextmanager
    async def fake_transaction_scope(_session_factory):
        yield session

    monkeypatch.setattr(repository_module, "transaction_scope", fake_transaction_scope)
    job = RunPostprocessJob.create(uuid4(), uuid4(), "trust-loop-v1")
    repository = SqlAlchemyPostprocessRepository(Mock())

    restored = await repository.create_or_get(job)

    assert restored == job
    session.add.assert_called_once()
    model = session.add.call_args.args[0]
    assert model.project_id == job.project_id
    assert model.run_id == job.run_id
    assert model.pipeline_version == "trust-loop-v1"


def test_models_enforce_job_and_stage_uniqueness() -> None:
    job_constraints = {
        constraint.name for constraint in RunPostprocessJobModel.__table__.constraints
    }
    stage_constraints = {
        constraint.name for constraint in RunPostprocessStageResultModel.__table__.constraints
    }

    assert "uq_run_postprocess_jobs_project_run_pipeline" in job_constraints
    assert "uq_run_postprocess_stage_results_job_stage" in stage_constraints


class ScalarRows:
    def __init__(self, rows) -> None:
        self._rows = rows

    def all(self):
        return self._rows


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["diagnostics", "regressions"])
async def test_public_record_queries_are_project_scoped_sorted_and_paginated(
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    project_id = uuid4()
    run_id = uuid4()
    now = datetime.now(UTC)
    if kind == "diagnostics":
        row = RunDiagnosticModel(
            id=uuid4(),
            project_id=project_id,
            run_id=run_id,
            run_case_id=uuid4(),
            pipeline_version="trust-loop-v1",
            status="completed",
            failure_class="assertion",
            confidence=0.9,
            evidence_ids=["evidence-1"],
            summary="bounded",
            counterevidence=[],
            verification_steps=[],
            model_adapter_version=None,
            created_at=now,
            updated_at=now,
        )
    else:
        row = RunRegressionCandidateModel(
            id=uuid4(),
            project_id=project_id,
            run_id=run_id,
            run_case_id=uuid4(),
            pipeline_version="trust-loop-v1",
            fingerprint="a" * 64,
            status="published",
            input_reference={},
            minimized_input=None,
            reproduction_run_case_ids=["evidence-1", "evidence-2"],
            reproduction_count=2,
            target_dataset_version_id=None,
            created_at=now,
            updated_at=now,
        )
    session = Mock()
    session.scalar = AsyncMock(return_value=1)
    session.scalars = AsyncMock(return_value=ScalarRows([row]))

    @asynccontextmanager
    async def fake_session_scope(_session_factory):
        yield session

    monkeypatch.setattr(repository_module, "session_scope", fake_session_scope)
    repository = SqlAlchemyPostprocessRepository(Mock())

    method = getattr(repository, f"list_{kind}")
    items, total = await method(
        project_id,
        run_id,
        "trust-loop-v1",
        limit=1,
        offset=2,
    )

    count_sql = str(session.scalar.call_args.args[0])
    list_statement = session.scalars.call_args.args[0]
    list_sql = str(list_statement)
    assert total == 1
    assert len(items) == 1
    assert ".project_id" in count_sql and ".run_id" in count_sql
    assert ".pipeline_version" in count_sql
    assert "ORDER BY" in list_sql
    assert list_statement._limit_clause.value == 1
    assert list_statement._offset_clause.value == 2
