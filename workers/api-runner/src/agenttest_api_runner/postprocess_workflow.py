from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from .postprocess_activities import execute_postprocess_stage
    from .postprocess_contracts import (
        PostprocessStageResponse,
        PostprocessStageTask,
        PostprocessWorkflowResult,
        PostprocessWorkflowTask,
    )

POSTPROCESS_ACTIVITY_TIMEOUT = timedelta(minutes=2)
POSTPROCESS_ACTIVITY_RETRY = RetryPolicy(
    maximum_attempts=3,
    initial_interval=timedelta(seconds=1),
    maximum_interval=timedelta(seconds=10),
)
POSTPROCESS_STAGES = (
    "classify",
    "diagnose",
    "reproduce",
    "calibrate",
    "evaluate_gate",
    "finalize",
)


class PostprocessStateMachine:
    def __init__(self, completed_stages: tuple[str, ...] = ()) -> None:
        self.status = "running"
        self.completed_stages = list(completed_stages)
        self.stage = self.pending_stages()[0] if self.pending_stages() else "finalize"
        self.warning_codes: list[str] = []
        self.error_type: str | None = None

    def pending_stages(self) -> tuple[str, ...]:
        if self.status != "running":
            return ()
        return tuple(stage for stage in POSTPROCESS_STAGES if stage not in self.completed_stages)

    def cancel(self) -> None:
        self.status = "cancelled"

    def apply(self, stage: str, response: PostprocessStageResponse) -> str:
        self.stage = stage
        if response.status == "completed":
            if stage not in self.completed_stages:
                self.completed_stages.append(stage)
            return "advance"
        if response.status == "warning":
            if stage not in self.completed_stages:
                self.completed_stages.append(stage)
            if response.warning_code and response.warning_code not in self.warning_codes:
                self.warning_codes.append(response.warning_code)
            return "advance"
        self.status = "failed"
        self.error_type = "postprocess_stage_failed"
        return "finish"


def normalize_postprocess_task(
    value: PostprocessWorkflowTask | dict[str, Any],
) -> PostprocessWorkflowTask:
    if isinstance(value, PostprocessWorkflowTask):
        return value
    return PostprocessWorkflowTask(
        project_id=str(value["project_id"]),
        run_id=str(value["run_id"]),
        pipeline_version=str(value["pipeline_version"]),
        callback_base_url=str(value["callback_base_url"]),
    )


@workflow.defn(name="RunPostprocessWorkflow")
class RunPostprocessWorkflow:
    def __init__(self) -> None:
        self._machine = PostprocessStateMachine()
        self._cancel_requested = False
        self._attempt = 1

    @workflow.signal
    async def cancel(self) -> None:
        self._cancel_requested = True
        self._machine.cancel()

    @workflow.query
    def state(self) -> dict[str, object]:
        return {
            "status": self._machine.status,
            "stage": self._machine.stage,
            "completed_stages": list(self._machine.completed_stages),
            "warning_codes": list(self._machine.warning_codes),
        }

    @workflow.run
    async def run(self, raw_task: Any) -> PostprocessWorkflowResult:
        task = normalize_postprocess_task(raw_task)
        for stage in POSTPROCESS_STAGES:
            if self._cancel_requested:
                return PostprocessWorkflowResult(
                    task.run_id,
                    task.pipeline_version,
                    "cancelled",
                    tuple(self._machine.warning_codes),
                )
            response = await workflow.execute_activity(
                execute_postprocess_stage,
                PostprocessStageTask(task, stage, self._attempt),
                start_to_close_timeout=POSTPROCESS_ACTIVITY_TIMEOUT,
                retry_policy=POSTPROCESS_ACTIVITY_RETRY,
            )
            action = self._machine.apply(stage, response)
            if action == "finish":
                return PostprocessWorkflowResult(
                    task.run_id,
                    task.pipeline_version,
                    "failed",
                    tuple(self._machine.warning_codes),
                    self._machine.error_type,
                )
        return PostprocessWorkflowResult(
            task.run_id,
            task.pipeline_version,
            "completed_with_warnings" if self._machine.warning_codes else "completed",
            tuple(self._machine.warning_codes),
        )
