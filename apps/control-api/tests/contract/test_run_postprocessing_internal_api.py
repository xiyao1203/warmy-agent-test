from contextlib import asynccontextmanager
from uuid import uuid4

from agenttest.modules.run_postprocessing.domain import RunPostprocessJob
from agenttest.modules.run_postprocessing.stages import StageExecution
from fastapi import FastAPI
from fastapi.testclient import TestClient


class Repository:
    def __init__(self, job: RunPostprocessJob) -> None:
        self.job = job
        self.saved_results = 0

    async def create_or_get(self, job):
        return self.job

    async def get(self, project_id, run_id, pipeline_version):
        if (
            project_id == self.job.project_id
            and run_id == self.job.run_id
            and pipeline_version == self.job.pipeline_version
        ):
            return self.job
        return None

    async def save(self, job):
        self.job = job

    async def save_stage_result(self, job, result):
        self.saved_results += 1

    async def save_stage_records(self, job, result):
        return None

    async def list_stage_results(self, project_id, job_id):
        return list(self.job.stage_results)


class Stages:
    async def execute(self, project_id, run_id, stage):
        return StageExecution("completed", {"stage": stage.value})


@asynccontextmanager
async def uow():
    yield None


def client_for():
    from agenttest.modules.run_postprocessing.api.internal_router import (
        create_internal_postprocess_router,
    )
    from agenttest.modules.run_postprocessing.application import PostprocessStageController

    job = RunPostprocessJob.create(uuid4(), uuid4(), "trust-loop-v1")
    repository = Repository(job)
    app = FastAPI()
    app.include_router(
        create_internal_postprocess_router(
            internal_token="test-internal-token",
            controller=PostprocessStageController(repository, Stages()),
            uow_factory=uow,
        ),
        prefix="/api/v1",
    )
    return TestClient(app, raise_server_exceptions=False), job, repository


def stage_url(job: RunPostprocessJob, stage: str) -> str:
    return (
        f"/api/v1/internal/projects/{job.project_id}/runs/{job.run_id}/"
        f"trust-loop/{job.pipeline_version}/stages/{stage}"
    )


def request_body() -> dict[str, object]:
    return {
        "idempotency_key": "workflow:classify:1",
        "workflow_id": "workflow-1",
        "attempt": 1,
    }


def test_internal_stage_requires_token_and_project_scope() -> None:
    client, job, _ = client_for()

    denied = client.post(stage_url(job, "classify"), json=request_body())
    foreign = client.post(
        stage_url(job, "classify").replace(str(job.project_id), str(uuid4())),
        headers={"X-Internal-Token": "test-internal-token"},
        json=request_body(),
    )

    assert denied.status_code == 403
    assert foreign.status_code == 404


def test_internal_stage_is_idempotent_and_rejects_out_of_order_execution() -> None:
    client, job, repository = client_for()
    headers = {"X-Internal-Token": "test-internal-token"}

    out_of_order = client.post(stage_url(job, "diagnose"), headers=headers, json=request_body())
    first = client.post(stage_url(job, "classify"), headers=headers, json=request_body())
    duplicate = client.post(stage_url(job, "classify"), headers=headers, json=request_body())

    assert out_of_order.status_code == 409
    assert first.status_code == 200
    assert first.json()["status"] == "completed"
    assert duplicate.status_code == 200
    assert duplicate.json() == first.json()
    assert repository.saved_results == 1
