from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from agenttest.modules.run_postprocessing.domain import RunPostprocessJob
from agenttest.modules.run_postprocessing.infrastructure import repository as repository_module
from agenttest.modules.run_postprocessing.infrastructure.models import (
    RunPostprocessJobModel,
    RunPostprocessStageResultModel,
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
