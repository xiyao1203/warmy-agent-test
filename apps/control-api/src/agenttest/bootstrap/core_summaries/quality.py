"""SQLAlchemy read-side projections for decision-ready core lists.

The reader lives in the composition layer because it joins several bounded contexts.
It never mutates business data and every method applies an explicit project scope.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.bootstrap.core_summaries.lookups import (
    _age_seconds,
    _agent_version_refs,
    _case_refs,
    _run_refs,
    _security_profile_refs,
    _string,
    _user_refs,
)
from agenttest.modules.gates.infrastructure.persistence.models import (
    ReleaseDecisionModel,
    ReleaseGateModel,
)
from agenttest.modules.reviews.infrastructure.persistence.models import ReviewTaskModel
from agenttest.modules.runs.infrastructure.persistence.models import (
    RunCaseModel,
    ScoreModel,
)
from agenttest.modules.scorers.infrastructure.persistence.models import (
    ScorerModel,
    ScorerVersionModel,
)
from agenttest.modules.security.infrastructure.repositories import SecurityScanModel
from agenttest.shared.application.core_summaries import (
    GateSummaryMetrics,
    ReviewSummaryMetrics,
    ScorerSummaryMetrics,
    SecurityScanSummaryMetrics,
)
from agenttest.shared.application.resource_reference import (
    ResourceReference,
    ResourceType,
)


class QualitySummaryQueries:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def scorers(self, project_id: UUID, ids: list[UUID]) -> dict[UUID, ScorerSummaryMetrics]:
        summaries = {item_id: ScorerSummaryMetrics() for item_id in ids}
        if not ids:
            return summaries
        async with self._session_factory() as session:
            ranked_versions = (
                select(
                    ScorerVersionModel.id.label("row_id"),
                    func.row_number()
                    .over(
                        partition_by=ScorerVersionModel.scorer_id,
                        order_by=(
                            ScorerVersionModel.version_number.desc(),
                            ScorerVersionModel.id.desc(),
                        ),
                    )
                    .label("row_rank"),
                )
                .join(ScorerModel, ScorerModel.id == ScorerVersionModel.scorer_id)
                .where(ScorerModel.project_id == project_id, ScorerModel.id.in_(ids))
                .subquery()
            )
            result = await session.execute(
                select(ScorerModel, ScorerVersionModel)
                .join(ScorerVersionModel, ScorerVersionModel.scorer_id == ScorerModel.id)
                .join(ranked_versions, ranked_versions.c.row_id == ScorerVersionModel.id)
                .where(ranked_versions.c.row_rank == 1)
            )
            version_to_scorer: dict[UUID, UUID] = {}
            for scorer, version in result:
                version_to_scorer[version.id] = scorer.id
                summaries[scorer.id] = ScorerSummaryMetrics(
                    latest_version=ResourceReference.build(
                        resource_type=ResourceType.SCORER,
                        resource_id=scorer.id,
                        project_id=project_id,
                        name=scorer.name,
                        version=version.version_number,
                        status=version.status,
                    ),
                    version_status=version.status,
                )
            if version_to_scorer:
                usage_rows = await session.execute(
                    select(ScoreModel.scorer_version_id, func.count(ScoreModel.id))
                    .where(
                        ScoreModel.project_id == project_id,
                        ScoreModel.scorer_version_id.in_(version_to_scorer),
                    )
                    .group_by(ScoreModel.scorer_version_id)
                )
                for version_id, count in usage_rows:
                    if version_id is not None:
                        summaries[version_to_scorer[version_id]].usage_count = int(count)
        return summaries

    async def security_scans(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, SecurityScanSummaryMetrics]:
        summaries = {item_id: SecurityScanSummaryMetrics() for item_id in ids}
        if not ids:
            return summaries
        async with self._session_factory() as session:
            result = await session.execute(
                select(SecurityScanModel).where(
                    SecurityScanModel.project_id == project_id,
                    SecurityScanModel.id.in_(ids),
                )
            )
            scans = list(result.scalars())
            agent_refs = await _agent_version_refs(
                session, project_id, [scan.agent_version_id for scan in scans]
            )
            run_refs = await _run_refs(session, project_id, [scan.run_id for scan in scans])
            profile_refs = await _security_profile_refs(
                session, project_id, [scan.security_profile_id for scan in scans]
            )
            for scan in scans:
                severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
                findings: list[object] = scan.findings if isinstance(scan.findings, list) else []
                for finding in findings:
                    if not isinstance(finding, dict):
                        continue
                    level = _string(finding.get("severity"))
                    if level in severity:
                        severity[level] += 1
                duration_ms = None
                if scan.completed_at:
                    duration_ms = int((scan.completed_at - scan.created_at).total_seconds() * 1000)
                summaries[scan.id] = SecurityScanSummaryMetrics(
                    agent_ref=(
                        agent_refs.get(scan.agent_version_id) if scan.agent_version_id else None
                    ),
                    run_ref=run_refs.get(scan.run_id) if scan.run_id else None,
                    profile_ref=(
                        profile_refs.get(scan.security_profile_id)
                        if scan.security_profile_id
                        else None
                    ),
                    critical_count=severity["critical"],
                    high_count=severity["high"],
                    medium_count=severity["medium"],
                    low_count=severity["low"],
                    duration_ms=duration_ms,
                    started_at=scan.created_at,
                )
        return summaries

    async def reviews(self, project_id: UUID, ids: list[UUID]) -> dict[UUID, ReviewSummaryMetrics]:
        summaries = {item_id: ReviewSummaryMetrics() for item_id in ids}
        if not ids:
            return summaries
        async with self._session_factory() as session:
            result = await session.execute(
                select(ReviewTaskModel, RunCaseModel)
                .join(RunCaseModel, RunCaseModel.id == ReviewTaskModel.run_case_id)
                .where(
                    ReviewTaskModel.project_id == project_id,
                    ReviewTaskModel.id.in_(ids),
                )
            )
            rows = list(result)
            run_refs = await _run_refs(
                session, project_id, [run_case.run_id for _, run_case in rows]
            )
            case_refs = await _case_refs(
                session, project_id, [run_case.test_case_id for _, run_case in rows]
            )
            user_refs = await _user_refs(
                session, project_id, [task.reviewer_id for task, _ in rows]
            )
            now = datetime.now(UTC)
            for task, run_case in rows:
                summaries[task.id] = ReviewSummaryMetrics(
                    run_ref=run_refs.get(run_case.run_id),
                    case_ref=case_refs.get(run_case.test_case_id),
                    enqueue_reason="low_confidence",
                    priority=max(0, min(100, round((1.0 - task.confidence) * 100))),
                    assignee_ref=(user_refs.get(task.reviewer_id) if task.reviewer_id else None),
                    age_seconds=_age_seconds(now, task.created_at),
                )
        return summaries

    async def gates(self, project_id: UUID, ids: list[UUID]) -> dict[UUID, GateSummaryMetrics]:
        summaries = {item_id: GateSummaryMetrics() for item_id in ids}
        if not ids:
            return summaries
        async with self._session_factory() as session:
            gate_result = await session.execute(
                select(ReleaseGateModel).where(
                    ReleaseGateModel.project_id == project_id,
                    ReleaseGateModel.id.in_(ids),
                )
            )
            gates = list(gate_result.scalars())
            ranked_decisions = (
                select(
                    ReleaseDecisionModel.id.label("row_id"),
                    func.row_number()
                    .over(
                        partition_by=ReleaseDecisionModel.gate_id,
                        order_by=(
                            ReleaseDecisionModel.created_at.desc(),
                            ReleaseDecisionModel.id.desc(),
                        ),
                    )
                    .label("row_rank"),
                )
                .where(
                    ReleaseDecisionModel.project_id == project_id,
                    ReleaseDecisionModel.gate_id.in_(ids),
                )
                .subquery()
            )
            decision_result = await session.execute(
                select(ReleaseDecisionModel)
                .join(
                    ranked_decisions,
                    ranked_decisions.c.row_id == ReleaseDecisionModel.id,
                )
                .where(ranked_decisions.c.row_rank == 1)
            )
            latest = {item.gate_id: item for item in decision_result.scalars()}
            run_refs = await _run_refs(
                session,
                project_id,
                [decision.run_id for decision in latest.values()],
            )
            for gate in gates:
                latest_decision = latest.get(gate.id)
                costs = f"，成本≤{gate.cost_limit:g}" if gate.cost_limit is not None else ""
                summaries[gate.id] = GateSummaryMetrics(
                    scope="project",
                    rule_summary=(
                        f"通过率≥{gate.success_rate_threshold:.0%}，"
                        f"安全分≥{gate.security_threshold:.0%}，"
                        f"关键用例 {len(gate.critical_cases)} 个{costs}"
                    ),
                    last_decision=(latest_decision.status if latest_decision else None),
                    blocking_count=(len(latest_decision.failures) if latest_decision else 0),
                    last_run_ref=(
                        run_refs.get(latest_decision.run_id)
                        if latest_decision is not None
                        else None
                    ),
                    evaluated_at=(latest_decision.created_at if latest_decision else None),
                )
        return summaries
