from __future__ import annotations

from typing import Protocol

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.reports.application.contracts import RunCaseReport, RunReport
from agenttest.modules.runs.public import Run, RunCase, RunId


class ReportNotFoundError(Exception):
    """项目中不存在指定运行。"""


class ReportProjectAccess(Protocol):
    async def ensure_member(self, actor: User, project_id: ProjectId) -> None: ...


class ReportRunRepository(Protocol):
    async def get_by_id(self, project_id: ProjectId, run_id: RunId) -> Run | None: ...

    async def list_cases(
        self,
        project_id: ProjectId,
        run_id: RunId,
    ) -> list[RunCase]: ...


class ReportService:
    def __init__(
        self,
        *,
        runs: ReportRunRepository,
        project_access: ReportProjectAccess,
    ) -> None:
        self._runs = runs
        self._project_access = project_access

    async def build(
        self,
        actor: User,
        project_id: ProjectId,
        run_id: RunId,
    ) -> RunReport:
        await self._project_access.ensure_member(actor, project_id)
        run = await self._runs.get_by_id(project_id, run_id)
        if run is None:
            raise ReportNotFoundError
        cases = await self._runs.list_cases(project_id, run_id)
        duration_ms = None
        if run.started_at is not None and run.completed_at is not None:
            duration_ms = int((run.completed_at - run.started_at).total_seconds() * 1000)
        return {
            "run_id": str(run.run_id.value),
            "project_id": str(run.project_id.value),
            "plan_id": (str(run.test_plan_version_id.value) if run.test_plan_version_id else None),
            "status": run.status.value,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "duration_ms": duration_ms,
            "total_cases": run.total_cases,
            "passed_cases": run.passed_cases,
            "failed_cases": run.failed_cases,
            "error_cases": run.error_cases,
            "cancelled_cases": run.cancelled_cases,
            "cases": [_case_data(case) for case in cases],
        }


def _case_data(case: RunCase) -> RunCaseReport:
    return {
        "case_id": str(case.run_case_id.value),
        "name": case.name,
        "status": case.status.value,
        "duration_ms": case.duration_ms,
        "error_type": case.error_type,
        "error": case.error_message,
    }
