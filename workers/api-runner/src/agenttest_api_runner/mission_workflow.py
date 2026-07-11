from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .mission_activities import execute_mission_stage
    from .mission_contracts import (
        MissionStageResponse,
        MissionStageTask,
        MissionWorkflowResult,
        MissionWorkflowTask,
    )

MISSION_ACTIVITY_TIMEOUT = timedelta(minutes=2)
MISSION_ACTIVITY_RETRY = RetryPolicy(
    maximum_attempts=3,
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=10),
)


class MissionStateMachine:
    def __init__(self) -> None:
        self.status = "running"
        self.stage = "provision"
        self.error_type: str | None = None
        self.error_message: str | None = None

    def apply(self, stage: str, response: MissionStageResponse) -> str:
        self.stage = stage
        if response.status == "completed":
            self.status = "running"
            return "advance"
        if response.status in {"running", "pending"}:
            self.status = "running"
            return "poll"
        if response.status == "needs_attention":
            self.status = "needs_attention"
            self.error_type = response.error_type
            self.error_message = response.error_message
            return "pause"
        self.status = "failed"
        self.error_type = response.error_type or "platform_error"
        self.error_message = response.error_message
        return "finish"

    def resume(self) -> None:
        if self.status == "needs_attention":
            self.status = "running"
            self.error_type = None
            self.error_message = None


def normalize_mission_task(value: MissionWorkflowTask | dict[str, Any]) -> MissionWorkflowTask:
    if isinstance(value, MissionWorkflowTask):
        return value
    return MissionWorkflowTask(
        project_id=str(value["project_id"]),
        mission_id=str(value["mission_id"]),
        revision_id=str(value["revision_id"]),
        revision_hash=str(value["revision_hash"]),
        callback_base_url=str(value["callback_base_url"]),
        idempotency_key=str(value.get("idempotency_key") or ""),
    )


@workflow.defn(name="TestMissionWorkflow")
class TestMissionWorkflow:
    def __init__(self) -> None:
        self._machine = MissionStateMachine()
        self._cancel_requested = False
        self._resume_requested = False

    @workflow.signal
    async def cancel(self) -> None:
        self._cancel_requested = True

    @workflow.signal
    async def resume(self) -> None:
        self._resume_requested = True
        self._machine.resume()

    @workflow.query
    def state(self) -> dict[str, object]:
        return {
            "status": self._machine.status,
            "stage": self._machine.stage,
            "error_type": self._machine.error_type,
        }

    @workflow.run
    async def run(self, raw_task: Any) -> MissionWorkflowResult:
        task = normalize_mission_task(raw_task)
        for stage in ("provision", "start_run", "await_run", "close_loop"):
            while True:
                if self._cancel_requested:
                    await self._execute(task, "cancel")
                    return MissionWorkflowResult(
                        mission_id=task.mission_id,
                        revision_id=task.revision_id,
                        status="cancelled",
                    )
                response = await self._execute(task, stage)
                action = self._machine.apply(stage, response)
                if action == "advance":
                    break
                if action == "finish":
                    return MissionWorkflowResult(
                        mission_id=task.mission_id,
                        revision_id=task.revision_id,
                        status="failed",
                        error_type=self._machine.error_type,
                        error_message=self._machine.error_message,
                    )
                if action == "pause":
                    self._resume_requested = False
                    await workflow.wait_condition(
                        lambda: self._resume_requested or self._cancel_requested
                    )
                    continue
                await workflow.sleep(timedelta(seconds=2))
        return MissionWorkflowResult(
            mission_id=task.mission_id,
            revision_id=task.revision_id,
            status="completed",
        )

    async def _execute(self, task: MissionWorkflowTask, stage: str) -> MissionStageResponse:
        return await workflow.execute_activity(
            execute_mission_stage,
            MissionStageTask(task, stage),
            start_to_close_timeout=MISSION_ACTIVITY_TIMEOUT,
            retry_policy=MISSION_ACTIVITY_RETRY,
        )
