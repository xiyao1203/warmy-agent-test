from __future__ import annotations

from typing import Any

from temporalio.client import Client
from temporalio.exceptions import WorkflowAlreadyStartedError

from agenttest.modules.test_missions.domain.entities import TestMission
from agenttest.modules.test_missions.domain.value_objects import MissionRevision


class TemporalMissionOrchestrator:
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

    async def start(
        self, mission: TestMission, revision: MissionRevision, idempotency_key: str
    ) -> str:
        workflow_id = f"test-mission-{mission.mission_id}-{revision.revision_number}"
        client = await self._get_client()
        try:
            await client.start_workflow(
                "TestMissionWorkflow",
                {
                    "project_id": str(mission.project_id),
                    "mission_id": str(mission.mission_id),
                    "revision_id": str(revision.revision_id),
                    "revision_hash": revision.content_hash,
                    "callback_base_url": self._callback_base_url,
                    "idempotency_key": idempotency_key,
                },
                id=workflow_id,
                task_queue=self._task_queue,
            )
        except WorkflowAlreadyStartedError:
            pass
        return workflow_id

    async def cancel(self, workflow_id: str) -> None:
        client = await self._get_client()
        await client.get_workflow_handle(workflow_id).signal("cancel")

    async def resume(self, workflow_id: str) -> None:
        client = await self._get_client()
        await client.get_workflow_handle(workflow_id).signal("resume")

    async def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if not self._address:
            raise RuntimeError("Mission execution runtime is unavailable")
        self._client = await Client.connect(self._address, namespace=self._namespace)
        return self._client
