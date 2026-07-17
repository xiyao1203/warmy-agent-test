from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.application.ports import ProjectAccessPort, RunRepository
from agenttest.modules.runs.domain.entities import Run, RunCase, RunId


class RunComparisonNotFound(Exception):
    def __init__(self, run_id: UUID) -> None:
        self.run_id = run_id


@dataclass(frozen=True, slots=True)
class RunComparisonDto:
    run_a: dict[str, object]
    run_b: dict[str, object]
    case_diffs: list[dict[str, object]]
    summary: dict[str, object]


class RunComparisonService:
    def __init__(self, *, runs: RunRepository, project_access: ProjectAccessPort) -> None:
        self._runs = runs
        self._project_access = project_access

    async def compare(
        self,
        actor: User,
        project_id: UUID,
        run_a_id: UUID,
        run_b_id: UUID,
    ) -> RunComparisonDto:
        project = ProjectId(project_id)
        await self._project_access.ensure_member(actor, project)
        run_a = await self._runs.get_by_id(project, RunId(run_a_id))
        run_b = await self._runs.get_by_id(project, RunId(run_b_id))
        if run_a is None:
            raise RunComparisonNotFound(run_a_id)
        if run_b is None:
            raise RunComparisonNotFound(run_b_id)
        cases_a = await self._runs.list_cases(project, RunId(run_a_id))
        cases_b = await self._runs.list_cases(project, RunId(run_b_id))
        case_diffs = _case_diffs(cases_a, cases_b)
        return RunComparisonDto(
            run_a=_run_summary(run_a),
            run_b=_run_summary(run_b),
            case_diffs=case_diffs,
            summary={
                "total_cases": len(case_diffs),
                "status_changes": sum(1 for item in case_diffs if item.get("status_changed")),
                "duration_delta_ms_total": sum(
                    int(value)
                    for item in case_diffs
                    if isinstance((value := item.get("duration_delta_ms")), (int, float))
                ),
            },
        )


def _run_summary(run: Run) -> dict[str, object]:
    return {
        "id": str(run.run_id.value),
        "status": run.status.value,
        "total_cases": run.total_cases,
        "passed_cases": run.passed_cases,
        "failed_cases": run.failed_cases,
        "error_cases": run.error_cases,
        "cancelled_cases": run.cancelled_cases,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


def _case_diffs(cases_a: list[RunCase], cases_b: list[RunCase]) -> list[dict[str, object]]:
    case_map_a = {str(item.test_case_id): item for item in cases_a}
    case_map_b = {str(item.test_case_id): item for item in cases_b}
    results: list[dict[str, object]] = []
    for case_id in sorted(set(case_map_a) | set(case_map_b)):
        left = case_map_a.get(case_id)
        right = case_map_b.get(case_id)
        item: dict[str, object] = {"test_case_id": case_id}
        if left is not None and right is not None:
            item.update(
                duration_delta_ms=(right.duration_ms or 0) - (left.duration_ms or 0),
                status_a=left.status.value,
                status_b=right.status.value,
                status_changed=left.status is not right.status,
                error_type_a=left.error_type,
                error_type_b=right.error_type,
            )
        elif left is not None:
            item.update(
                status_a=left.status.value,
                status_b=None,
                status_changed=True,
                note="仅存在于运行 A",
            )
        else:
            assert right is not None
            item.update(
                status_a=None,
                status_b=right.status.value,
                status_changed=True,
                note="仅存在于运行 B",
            )
        results.append(item)
    return results
