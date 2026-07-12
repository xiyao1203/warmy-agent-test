from __future__ import annotations

from uuid import UUID

from agenttest.modules.run_postprocessing.domain import RunPostprocessJob
from agenttest.modules.run_postprocessing.ports import PostprocessRepository
from agenttest.modules.run_postprocessing.public import PostprocessScheduler

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
