from uuid import uuid4

import pytest
from agenttest.modules.run_postprocessing.domain import RunPostprocessJob
from agenttest.modules.run_postprocessing.infrastructure.temporal import (
    TemporalPostprocessScheduler,
)
from temporalio.common import WorkflowIDReusePolicy
from temporalio.exceptions import WorkflowAlreadyStartedError


class Client:
    def __init__(self, *, duplicate: bool = False) -> None:
        self.duplicate = duplicate
        self.calls: list[dict[str, object]] = []

    async def start_workflow(self, name, payload, **options):
        self.calls.append({"name": name, "payload": payload, **options})
        if self.duplicate:
            raise WorkflowAlreadyStartedError(
                str(options["id"]),
                str(name),
            )


@pytest.mark.asyncio
async def test_scheduler_uses_stable_id_and_secret_free_payload() -> None:
    client = Client()
    scheduler = TemporalPostprocessScheduler(
        task_queue="agenttest-api-runner",
        callback_base_url="https://control.example",
        client=client,
    )
    job = RunPostprocessJob.create(uuid4(), uuid4(), "trust-loop-v1")

    workflow_id = await scheduler.schedule(job)

    assert workflow_id == f"run-trust-loop-{job.run_id}-trust-loop-v1"
    assert client.calls[0]["id"] == workflow_id
    assert client.calls[0]["id_reuse_policy"] is WorkflowIDReusePolicy.REJECT_DUPLICATE
    assert "token" not in repr(client.calls[0]["payload"]).lower()


@pytest.mark.asyncio
async def test_scheduler_treats_duplicate_start_as_success() -> None:
    scheduler = TemporalPostprocessScheduler(
        task_queue="agenttest-api-runner",
        callback_base_url="https://control.example",
        client=Client(duplicate=True),
    )
    job = RunPostprocessJob.create(uuid4(), uuid4(), "trust-loop-v1")

    assert await scheduler.schedule(job) == f"run-trust-loop-{job.run_id}-trust-loop-v1"
