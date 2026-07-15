from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from agenttest.modules.experiments.domain.entities import Experiment, ExperimentId
from agenttest.modules.experiments.domain.statistics import (
    calculate_statistics,
    identify_degradation,
)
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.public import (
    ProjectAccessPort,
    Run,
    RunCase,
    RunId,
    RunRepository,
)


class ExperimentRepository(Protocol):
    async def get_by_id_and_project(
        self,
        exp_id: ExperimentId,
        project_id: ProjectId,
    ) -> Experiment | None: ...

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int,
        offset: int,
    ) -> list[Experiment]: ...

    async def add(self, experiment: Experiment) -> None: ...

    async def save(self, experiment: Experiment) -> None: ...


class ExperimentNotFound(Exception):
    pass


class ExperimentValidationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class ExperimentStatisticsDto:
    payload: dict[str, object]


class ExperimentService:
    def __init__(
        self,
        *,
        experiments: ExperimentRepository,
        runs: RunRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._experiments = experiments
        self._runs = runs
        self._project_access = project_access

    async def list(
        self,
        actor: User,
        project_id: UUID,
        limit: int,
        offset: int,
    ) -> list[Experiment]:
        project = ProjectId(project_id)
        await self._project_access.ensure_member(actor, project)
        return await self._experiments.list_by_project(
            project,
            limit=limit,
            offset=offset,
        )

    async def create(
        self,
        actor: User,
        project_id: UUID,
        *,
        name: str,
        run_a_id: UUID,
        run_b_id: UUID,
        description: str | None,
    ) -> Experiment:
        project = ProjectId(project_id)
        await self._project_access.ensure_editor(actor, project)
        run_a = await self._completed_run(project, run_a_id)
        run_b = await self._completed_run(project, run_b_id)
        if run_a.test_plan_version_id != run_b.test_plan_version_id:
            raise ExperimentValidationError("仅可对比来自同一测试计划版本的运行")
        try:
            experiment = Experiment.create(
                experiment_id=ExperimentId.new(),
                project_id=project,
                name=name,
                run_a_id=run_a_id,
                run_b_id=run_b_id,
                description=description,
            )
        except ValueError as error:
            raise ExperimentValidationError(str(error)) from error
        await self._experiments.add(experiment)
        return experiment

    async def get(self, actor: User, project_id: UUID, experiment_id: UUID) -> Experiment:
        project = ProjectId(project_id)
        await self._project_access.ensure_member(actor, project)
        return await self._experiment(project, experiment_id)

    async def run(self, actor: User, project_id: UUID, experiment_id: UUID) -> Experiment:
        project = ProjectId(project_id)
        await self._project_access.ensure_editor(actor, project)
        experiment = await self._experiment(project, experiment_id)
        if experiment.status.value == "completed":
            return experiment
        run_a = await self._runs.get_by_id(project, RunId(experiment.run_a_id))
        run_b = await self._runs.get_by_id(project, RunId(experiment.run_b_id))
        if run_a is None:
            raise ExperimentValidationError(f"运行 {experiment.run_a_id} 不属于该项目")
        if run_b is None:
            raise ExperimentValidationError(f"运行 {experiment.run_b_id} 不属于该项目")
        cases_a = await self._runs.list_cases(project, RunId(experiment.run_a_id))
        cases_b = await self._runs.list_cases(project, RunId(experiment.run_b_id))
        experiment.complete(_comparison_result(cases_a, cases_b))
        await self._experiments.save(experiment)
        return experiment

    async def statistics(
        self,
        actor: User,
        project_id: UUID,
        *,
        run_id: UUID | None,
        experiment_id: UUID | None,
    ) -> ExperimentStatisticsDto:
        project = ProjectId(project_id)
        await self._project_access.ensure_member(actor, project)
        if run_id is not None:
            run = await self._runs.get_by_id(project, RunId(run_id))
            if run is None:
                raise ExperimentValidationError(f"运行 {run_id} 不属于该项目")
            cases = await self._runs.list_cases(project, RunId(run_id))
            return ExperimentStatisticsDto(
                {"run_id": str(run_id), "statistics": calculate_statistics(_cases(cases)).to_dict()}
            )
        if experiment_id is None:
            raise ExperimentValidationError("run_id 或 experiment_id 必须提供一个")
        experiment = await self._experiment(project, experiment_id)
        cases_a = await self._runs.list_cases(project, RunId(experiment.run_a_id))
        cases_b = await self._runs.list_cases(project, RunId(experiment.run_b_id))
        values_a = _cases(cases_a)
        values_b = _cases(cases_b)
        return ExperimentStatisticsDto(
            {
                "experiment_id": str(experiment_id),
                "run_a": {
                    "id": str(experiment.run_a_id),
                    "statistics": calculate_statistics(values_a).to_dict(),
                },
                "run_b": {
                    "id": str(experiment.run_b_id),
                    "statistics": calculate_statistics(values_b).to_dict(),
                },
                "degradation": identify_degradation(values_a, values_b),
            }
        )

    async def _experiment(self, project: ProjectId, experiment_id: UUID) -> Experiment:
        experiment = await self._experiments.get_by_id_and_project(
            ExperimentId(experiment_id),
            project,
        )
        if experiment is None:
            raise ExperimentNotFound
        return experiment

    async def _completed_run(self, project: ProjectId, run_id: UUID) -> Run:
        run = await self._runs.get_by_id(project, RunId(run_id))
        if run is None or run.status.value not in {"passed", "failed", "error"}:
            raise ExperimentValidationError(f"运行 {run_id} 不存在、未完成或不属于该项目")
        return run


def _cases(cases: list[RunCase]) -> list[dict[str, object]]:
    return [
        {
            "test_case_id": str(item.test_case_id),
            "status": item.status.value,
            "duration_ms": item.duration_ms,
        }
        for item in cases
    ]


def _comparison_result(cases_a: list[RunCase], cases_b: list[RunCase]) -> dict[str, object]:
    map_a = {str(item.test_case_id): item for item in cases_a}
    map_b = {str(item.test_case_id): item for item in cases_b}
    case_diffs: list[dict[str, object]] = []
    duration_deltas: list[int] = []
    improved = degraded = unchanged = 0
    for case_id in sorted(set(map_a) | set(map_b)):
        left = map_a.get(case_id)
        right = map_b.get(case_id)
        duration_delta = 0
        status_a = left.status.value if left else None
        status_b = right.status.value if right else None
        changed = left is not None and right is not None and status_a != status_b
        category = "no_change"
        if left is not None and right is not None:
            duration_delta = (right.duration_ms or 0) - (left.duration_ms or 0)
            duration_deltas.append(duration_delta)
            if changed and status_a == "passed" and status_b != "passed":
                category = "degraded"
                degraded += 1
            elif changed and status_a != "passed" and status_b == "passed":
                category = "improved"
                improved += 1
            else:
                unchanged += 1
        else:
            unchanged += 1
        case_diffs.append(
            {
                "test_case_id": case_id,
                "status_a": status_a,
                "status_b": status_b,
                "status_changed": changed,
                "duration_delta_ms": duration_delta,
                "category": category,
            }
        )
    sorted_durations = sorted(duration_deltas) if duration_deltas else [0]
    p50 = sorted_durations[min(int(len(sorted_durations) * 0.5), len(sorted_durations) - 1)]
    p95 = sorted_durations[min(int(len(sorted_durations) * 0.95), len(sorted_durations) - 1)]
    return {
        "case_diffs": case_diffs,
        "summary": {
            "total_cases": len(case_diffs),
            "improved": improved,
            "degraded": degraded,
            "unchanged": unchanged,
            "avg_duration_delta_ms": round(
                statistics.mean(duration_deltas) if duration_deltas else 0.0,
                2,
            ),
            "p50_duration_delta_ms": float(p50),
            "p95_duration_delta_ms": float(p95),
        },
    }
