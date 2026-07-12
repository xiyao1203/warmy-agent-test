from __future__ import annotations

from typing import Protocol
from uuid import UUID

from agenttest.modules.run_postprocessing.domain import (
    RunPostprocessJob,
    StageResult,
)


class PostprocessRepository(Protocol):
    async def create_or_get(self, job: RunPostprocessJob) -> RunPostprocessJob: ...

    async def get(
        self, project_id: UUID, run_id: UUID, pipeline_version: str
    ) -> RunPostprocessJob | None: ...

    async def save(self, job: RunPostprocessJob) -> None: ...

    async def save_stage_result(self, job: RunPostprocessJob, result: StageResult) -> None: ...

    async def list_stage_results(self, project_id: UUID, job_id: UUID) -> list[StageResult]: ...
