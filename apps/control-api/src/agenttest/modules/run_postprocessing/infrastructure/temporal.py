from __future__ import annotations

from typing import Any

from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporalio.exceptions import WorkflowAlreadyStartedError

from agenttest.modules.run_postprocessing.domain import RunPostprocessJob


class TemporalPostprocessScheduler:
    def __init__(
        self,
        *,
        task_queue: str,
        callback_base_url: str,
        address: str | None = None,
        namespace: str = "default",
        client: Any | None = None,
    ) -> None:
        self._task_queue = task_queue
        self._callback_base_url = callback_base_url
        self._address = address
        self._namespace = namespace
        self._client = client

    async def schedule(self, job: RunPostprocessJob) -> str:
        workflow_id = f"run-trust-loop-{job.run_id}-{job.pipeline_version}"
        client = await self._get_client()
        try:
            await client.start_workflow(
                "RunPostprocessWorkflow",
                {
                    "project_id": str(job.project_id),
                    "run_id": str(job.run_id),
                    "pipeline_version": job.pipeline_version,
                    "callback_base_url": self._callback_base_url,
                },
                id=workflow_id,
                task_queue=self._task_queue,
                id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
            )
        except WorkflowAlreadyStartedError:
            pass
        return workflow_id

    async def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if not self._address:
            raise RuntimeError("Run postprocess runtime is unavailable")
        self._client = await Client.connect(self._address, namespace=self._namespace)
        return self._client
