from __future__ import annotations

from typing import Protocol
from uuid import UUID

from agenttest.modules.run_postprocessing.domain import RunPostprocessJob


class RunPostprocessCreator(Protocol):
    async def ensure_created(self, project_id: UUID, run_id: UUID) -> RunPostprocessJob: ...


class PostprocessScheduler(Protocol):
    async def schedule(self, job: RunPostprocessJob) -> str: ...


__all__ = ["PostprocessScheduler", "RunPostprocessCreator", "RunPostprocessJob"]
