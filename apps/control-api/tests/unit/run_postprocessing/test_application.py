from uuid import uuid4

import pytest
from agenttest.modules.run_postprocessing.application import (
    PIPELINE_VERSION,
    PostprocessJobService,
)
from agenttest.modules.run_postprocessing.domain import RunPostprocessJob


class InMemoryRepository:
    def __init__(self) -> None:
        self.job: RunPostprocessJob | None = None

    async def create_or_get(self, job: RunPostprocessJob) -> RunPostprocessJob:
        if self.job is None:
            self.job = job
        return self.job

    async def get(self, project_id, run_id, pipeline_version):
        if (
            self.job
            and self.job.project_id == project_id
            and self.job.run_id == run_id
            and self.job.pipeline_version == pipeline_version
        ):
            return self.job
        return None

    async def save(self, job):
        self.job = job

    async def save_stage_result(self, job, result):
        return None

    async def list_stage_results(self, project_id, job_id):
        return list(self.job.stage_results) if self.job else []


class RecordingScheduler:
    def __init__(self, repository: InMemoryRepository, *, fail: bool = False) -> None:
        self.repository = repository
        self.fail = fail
        self.calls: list[RunPostprocessJob] = []

    async def schedule(self, job: RunPostprocessJob) -> str:
        assert self.repository.job is job
        self.calls.append(job)
        if self.fail:
            raise RuntimeError("temporal unavailable")
        return f"run-trust-loop-{job.run_id}-{job.pipeline_version}"


@pytest.mark.asyncio
async def test_service_creates_one_job_and_schedules_the_persisted_instance() -> None:
    repository = InMemoryRepository()
    scheduler = RecordingScheduler(repository)
    service = PostprocessJobService(repository, scheduler)
    project_id = uuid4()
    run_id = uuid4()

    first = await service.ensure_created(project_id, run_id)
    second = await service.ensure_created(project_id, run_id)
    workflow_id = await service.schedule(project_id, run_id)

    assert first.job_id == second.job_id
    assert first.pipeline_version == PIPELINE_VERSION
    assert workflow_id == f"run-trust-loop-{run_id}-{PIPELINE_VERSION}"
    assert scheduler.calls == [first]


@pytest.mark.asyncio
async def test_scheduling_failure_leaves_the_job_pending() -> None:
    repository = InMemoryRepository()
    scheduler = RecordingScheduler(repository, fail=True)
    service = PostprocessJobService(repository, scheduler)
    project_id = uuid4()
    run_id = uuid4()
    job = await service.ensure_created(project_id, run_id)

    with pytest.raises(RuntimeError, match="temporal unavailable"):
        await service.schedule(project_id, run_id)

    assert job.status.value == "pending"
