from __future__ import annotations

from uuid import UUID

from agenttest.modules.run_postprocessing.domain import (
    PostprocessStage,
    RunPostprocessJob,
)
from agenttest.modules.run_postprocessing.ports import PostprocessRepository
from agenttest.modules.run_postprocessing.public import PostprocessScheduler
from agenttest.modules.run_postprocessing.stages import (
    PostprocessStageService,
    StageExecution,
)

PIPELINE_VERSION = "trust-loop-v1"


class PostprocessJobService:
    def __init__(
        self,
        repository: PostprocessRepository,
        scheduler: PostprocessScheduler | None = None,
    ) -> None:
        self._repository = repository
        self._scheduler = scheduler

    async def ensure_created(self, project_id: UUID, run_id: UUID) -> RunPostprocessJob:
        return await self._repository.create_or_get(
            RunPostprocessJob.create(project_id, run_id, PIPELINE_VERSION)
        )

    async def schedule(self, project_id: UUID, run_id: UUID) -> str:
        if self._scheduler is None:
            raise RuntimeError("Run postprocess runtime is unavailable")
        job = await self._repository.get(project_id, run_id, PIPELINE_VERSION)
        if job is None:
            raise LookupError("Run postprocess job does not exist")
        return await self._scheduler.schedule(job)


class PostprocessStageController:
    _REQUIRED_STAGES = {
        PostprocessStage.CLASSIFY,
        PostprocessStage.EVALUATE_GATE,
        PostprocessStage.FINALIZE,
    }

    def __init__(
        self,
        repository: PostprocessRepository,
        stages: PostprocessStageService,
    ) -> None:
        self._repository = repository
        self._stages = stages

    async def execute(
        self,
        *,
        project_id: UUID,
        run_id: UUID,
        pipeline_version: str,
        stage: PostprocessStage,
        workflow_id: str,
        attempt: int,
    ) -> StageExecution:
        job = await self._repository.get(project_id, run_id, pipeline_version)
        if job is None:
            raise LookupError("Run postprocess job does not exist")
        existing = next((item for item in job.stage_results if item.stage is stage), None)
        if existing is not None:
            return StageExecution(existing.status, existing.output, existing.warning_code)
        if job.status.value == "pending":
            job.start(workflow_id)
            job.attempt = max(job.attempt, attempt)
        job.begin_stage(stage)
        try:
            execution = await self._stages.execute(project_id, run_id, stage)
        except Exception:
            required = stage in self._REQUIRED_STAGES
            job.fail_stage(
                stage,
                "stage_execution_failed",
                "Postprocess stage execution failed",
                required=required,
            )
            result = job.stage_results[-1]
            await self._repository.save_stage_result(job, result)
            await self._repository.save(job)
            return StageExecution(result.status, result.output, result.warning_code)
        if execution.status == "completed":
            job.complete_stage(stage, execution.output)
        else:
            job.fail_stage(
                stage,
                execution.warning_code or "stage_inconclusive",
                "Postprocess stage completed with a warning",
                required=False,
            )
            job.stage_results[-1] = job.stage_results[-1].__class__(
                stage=stage,
                status="warning",
                output=execution.output,
                warning_code=execution.warning_code or "stage_inconclusive",
                error_type=execution.warning_code or "stage_inconclusive",
                error_message="Postprocess stage completed with a warning",
                completed_at=job.stage_results[-1].completed_at,
            )
        result = job.stage_results[-1]
        await self._repository.save_stage_result(job, result)
        await self._repository.save_stage_records(job, result)
        await self._repository.save(job)
        return StageExecution(result.status, result.output, result.warning_code)
