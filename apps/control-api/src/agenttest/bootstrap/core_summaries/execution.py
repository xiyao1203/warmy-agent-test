"""SQLAlchemy read-side projections for decision-ready core lists.

The reader lives in the composition layer because it joins several bounded contexts.
It never mutates business data and every method applies an explicit project scope.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.bootstrap.core_summaries.lookups import (
    _agent_version_refs,
    _case_refs,
    _dataset_version_refs,
    _dict,
    _integer,
    _optional_float,
    _plan_version_refs,
    _run_refs,
    _string,
    _user_refs,
)
from agenttest.modules.experiments.infrastructure.persistence.models import ExperimentModel
from agenttest.modules.runs.infrastructure.persistence.models import (
    RunEventModel,
    RunModel,
)
from agenttest.shared.application.core_summaries import (
    ExperimentSummaryMetrics,
    RunSummaryMetrics,
)


class ExecutionSummaryQueries:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def runs(self, project_id: UUID, ids: list[UUID]) -> dict[UUID, RunSummaryMetrics]:
        if not ids:
            return {}
        summaries: dict[UUID, RunSummaryMetrics] = {}
        async with self._session_factory() as session:
            result = await session.execute(
                select(RunModel).where(RunModel.project_id == project_id, RunModel.id.in_(ids))
            )
            runs = list(result.scalars())
            plan_refs = await _plan_version_refs(
                session, project_id, [run.test_plan_version_id for run in runs]
            )
            agent_refs = await _agent_version_refs(
                session, project_id, [run.agent_version_id for run in runs]
            )
            dataset_refs = await _dataset_version_refs(
                session, project_id, [run.dataset_version_id for run in runs]
            )
            case_refs = await _case_refs(
                session, project_id, [run.source_test_case_id for run in runs]
            )
            users = await _user_refs(session, project_id, [run.created_by for run in runs])
            event_rows = await session.execute(
                select(
                    RunEventModel.run_id,
                    func.sum(RunEventModel.token_count),
                    func.sum(RunEventModel.cost),
                )
                .where(RunEventModel.run_id.in_(ids))
                .group_by(RunEventModel.run_id)
            )
            event_totals = {run_id: (tokens, cost) for run_id, tokens, cost in event_rows}
            for run in runs:
                completed = (
                    run.passed_cases + run.failed_cases + run.error_cases + run.cancelled_cases
                )
                tokens, cost = event_totals.get(run.id, (None, None))
                duration_ms = None
                if run.started_at and run.completed_at:
                    duration_ms = int((run.completed_at - run.started_at).total_seconds() * 1000)
                summaries[run.id] = RunSummaryMetrics(
                    run_number=f"RUN-{str(run.id).split('-')[0].upper()}",
                    plan_ref=(
                        plan_refs.get(run.test_plan_version_id)
                        if run.test_plan_version_id
                        else None
                    ),
                    agent_ref=agent_refs.get(run.agent_version_id),
                    dataset_ref=dataset_refs.get(run.dataset_version_id),
                    source_case_ref=(
                        case_refs.get(run.source_test_case_id) if run.source_test_case_id else None
                    ),
                    trigger_type=_string(_dict(run.config_snapshot).get("trigger_type"))
                    or "manual",
                    progress=(completed / run.total_cases if run.total_cases else 0.0),
                    duration_ms=duration_ms,
                    token_usage={"total": int(tokens)} if tokens is not None else None,
                    cost=float(cost) if cost is not None else None,
                    created_by_ref=users.get(run.created_by),
                )
        return summaries

    async def experiments(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, ExperimentSummaryMetrics]:
        summaries = {item_id: ExperimentSummaryMetrics() for item_id in ids}
        if not ids:
            return summaries
        async with self._session_factory() as session:
            result = await session.execute(
                select(ExperimentModel).where(
                    ExperimentModel.project_id == project_id,
                    ExperimentModel.id.in_(ids),
                )
            )
            experiments = list(result.scalars())
            run_refs = await _run_refs(
                session,
                project_id,
                [item.run_a_id for item in experiments] + [item.run_b_id for item in experiments],
            )
            for item in experiments:
                result_json = _dict(item.result_json)
                summary = _dict(result_json.get("summary"))
                summaries[item.id] = ExperimentSummaryMetrics(
                    baseline_run_ref=run_refs.get(item.run_a_id),
                    candidate_run_ref=run_refs.get(item.run_b_id),
                    case_count=_integer(summary.get("total_cases"), 0),
                    improved_count=_integer(summary.get("improved"), 0),
                    regressed_count=_integer(summary.get("degraded", summary.get("regressed")), 0),
                    pass_rate_delta=_optional_float(result_json.get("pass_rate_delta")),
                    score_delta=_optional_float(
                        result_json.get("score_delta", result_json.get("avg_score_delta"))
                    ),
                    cost_delta=_optional_float(result_json.get("cost_delta")),
                )
        return summaries
