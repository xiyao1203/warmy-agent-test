from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.application.ports import ProjectAccessPort, RunRepository
from agenttest.modules.runs.domain.entities import RunId


@dataclass(frozen=True, slots=True)
class RunProgressDto:
    status: str
    passed: int
    failed: int
    error: int
    cancelled: int
    total: int

    def cases(self) -> dict[str, int]:
        return {
            "passed": self.passed,
            "failed": self.failed,
            "error": self.error,
            "cancelled": self.cancelled,
            "total": self.total,
        }


class RunProgressService:
    def __init__(self, *, runs: RunRepository, project_access: ProjectAccessPort) -> None:
        self._runs = runs
        self._project_access = project_access

    async def get(
        self,
        actor: User,
        project_id: UUID,
        run_id: UUID,
    ) -> RunProgressDto | None:
        project = ProjectId(project_id)
        await self._project_access.ensure_member(actor, project)
        run = await self._runs.get_by_id(project, RunId(run_id))
        if run is None:
            return None
        return RunProgressDto(
            status=run.status.value,
            passed=run.passed_cases,
            failed=run.failed_cases,
            error=run.error_cases,
            cancelled=run.cancelled_cases,
            total=run.total_cases,
        )
