"""SQLAlchemy read-side projections for decision-ready core lists.

The reader lives in the composition layer because it joins several bounded contexts.
It never mutates business data and every method applies an explicit project scope.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.agents.infrastructure.persistence.models import (
    AgentModel,
    AgentVersionModel,
)
from agenttest.modules.browser_profiles.infrastructure.models import BrowserProfileModel
from agenttest.modules.datasets.infrastructure.persistence.models import (
    DatasetModel,
    DatasetVersionModel,
    TestCaseModel,
)
from agenttest.modules.environments.infrastructure.persistence.models import (
    EnvironmentTemplateModel,
    EnvironmentVersionModel,
)
from agenttest.modules.experiments.infrastructure.persistence.models import ExperimentModel
from agenttest.modules.gates.infrastructure.persistence.models import (
    ReleaseDecisionModel,
    ReleaseGateModel,
)
from agenttest.modules.identity.infrastructure.persistence.models import UserModel
from agenttest.modules.projects.infrastructure.persistence.models import ProjectMemberModel
from agenttest.modules.reviews.infrastructure.persistence.models import ReviewTaskModel
from agenttest.modules.runs.infrastructure.persistence.models import (
    RunCaseModel,
    RunEvaluationModel,
    RunEventModel,
    RunModel,
    ScoreModel,
)
from agenttest.modules.scorers.infrastructure.persistence.models import (
    ScorerModel,
    ScorerVersionModel,
)
from agenttest.modules.security.infrastructure.models import SecurityProfileModel
from agenttest.modules.security.infrastructure.repositories import SecurityScanModel
from agenttest.modules.test_plans.infrastructure.persistence.models import (
    TestPlanModel,
    TestPlanVersionModel,
)
from agenttest.shared.application.core_summaries import (
    AgentSummaryMetrics,
    DatasetSummaryMetrics,
    EnvironmentSummaryMetrics,
    ExperimentSummaryMetrics,
    GateSummaryMetrics,
    ProjectSummaryMetrics,
    ReviewSummaryMetrics,
    RunSummaryMetrics,
    ScorerSummaryMetrics,
    SecurityScanSummaryMetrics,
    TestPlanSummaryMetrics,
)
from agenttest.shared.application.resource_reference import (
    ResourceReference,
    ResourceType,
)


class SqlAlchemyCoreSummaryReader:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def projects(self, ids: list[UUID]) -> dict[UUID, ProjectSummaryMetrics]:
        summaries = {item_id: ProjectSummaryMetrics() for item_id in ids}
        if not ids:
            return summaries
        async with self._session_factory() as session:
            for model, field in (
                (ProjectMemberModel, "member_count"),
                (AgentModel, "agent_count"),
                (DatasetModel, "dataset_count"),
                (TestPlanModel, "test_plan_count"),
                (EnvironmentTemplateModel, "active_environment_count"),
            ):
                rows = await _group_count(session, model, model.project_id, ids)
                for project_id, count in rows.items():
                    setattr(summaries[project_id], field, count)

            case_rows = await session.execute(
                select(DatasetModel.project_id, func.count(TestCaseModel.id))
                .join(DatasetVersionModel, DatasetVersionModel.dataset_id == DatasetModel.id)
                .join(TestCaseModel, TestCaseModel.dataset_version_id == DatasetVersionModel.id)
                .where(DatasetModel.project_id.in_(ids))
                .group_by(DatasetModel.project_id)
            )
            for project_id, count in case_rows:
                summaries[project_id].test_case_count = int(count)

            review_rows = await session.execute(
                select(ReviewTaskModel.project_id, func.count(ReviewTaskModel.id))
                .where(
                    ReviewTaskModel.project_id.in_(ids),
                    ReviewTaskModel.status == "pending",
                )
                .group_by(ReviewTaskModel.project_id)
            )
            for project_id, count in review_rows:
                summaries[project_id].open_review_count = int(count)

            latest_runs = await session.execute(
                select(RunModel)
                .where(RunModel.project_id.in_(ids))
                .order_by(RunModel.project_id, RunModel.created_at.desc())
            )
            seen: set[UUID] = set()
            for run in latest_runs.scalars():
                if run.project_id in seen:
                    continue
                seen.add(run.project_id)
                summary = summaries[run.project_id]
                summary.last_run = _run_ref(run)
                summary.last_run_status = run.status
                summary.last_run_at = run.created_at
        return summaries

    async def agents(self, project_id: UUID, ids: list[UUID]) -> dict[UUID, AgentSummaryMetrics]:
        summaries = {item_id: AgentSummaryMetrics() for item_id in ids}
        if not ids:
            return summaries
        async with self._session_factory() as session:
            result = await session.execute(
                select(AgentModel, AgentVersionModel)
                .outerjoin(AgentVersionModel, AgentVersionModel.id == AgentModel.current_version_id)
                .where(AgentModel.project_id == project_id, AgentModel.id.in_(ids))
            )
            version_to_agent: dict[UUID, UUID] = {}
            for agent, version in result:
                if version is None:
                    continue
                config = _dict(version.config)
                version_to_agent[version.id] = agent.id
                summaries[agent.id] = AgentSummaryMetrics(
                    current_version=ResourceReference.build(
                        resource_type=ResourceType.AGENT_VERSION,
                        resource_id=version.id,
                        project_id=project_id,
                        parent_id=agent.id,
                        name=agent.name,
                        version=version.version_number,
                        status=version.status,
                    ),
                    version_status=version.status,
                    protocol=_string(config.get("protocol")),
                    model=_string(config.get("model")),
                    tool_count=len(_list(config.get("tools"))),
                    credential_binding_count=len(_list(config.get("credential_binding_ids"))),
                    connection_status=version.readiness_status,
                )

            if version_to_agent:
                run_rows = await session.execute(
                    select(RunModel, RunEvaluationModel.pass_rate)
                    .outerjoin(RunEvaluationModel, RunEvaluationModel.run_id == RunModel.id)
                    .where(
                        RunModel.project_id == project_id,
                        RunModel.agent_version_id.in_(version_to_agent),
                    )
                    .order_by(RunModel.agent_version_id, RunModel.created_at.desc())
                )
                seen_versions: set[UUID] = set()
                for run, pass_rate in run_rows:
                    if run.agent_version_id in seen_versions:
                        continue
                    seen_versions.add(run.agent_version_id)
                    summary = summaries[version_to_agent[run.agent_version_id]]
                    summary.last_run_status = run.status
                    summary.pass_rate = float(pass_rate) if pass_rate is not None else None
        return summaries

    async def datasets(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, DatasetSummaryMetrics]:
        summaries = {item_id: DatasetSummaryMetrics() for item_id in ids}
        if not ids:
            return summaries
        async with self._session_factory() as session:
            result = await session.execute(
                select(DatasetModel, DatasetVersionModel)
                .join(DatasetVersionModel, DatasetVersionModel.dataset_id == DatasetModel.id)
                .where(DatasetModel.project_id == project_id, DatasetModel.id.in_(ids))
                .order_by(DatasetModel.id, DatasetVersionModel.version_number.desc())
            )
            version_to_dataset: dict[UUID, UUID] = {}
            seen: set[UUID] = set()
            for dataset, version in result:
                if dataset.id in seen:
                    continue
                seen.add(dataset.id)
                version_to_dataset[version.id] = dataset.id
                summaries[dataset.id] = DatasetSummaryMetrics(
                    latest_version=ResourceReference.build(
                        resource_type=ResourceType.DATASET_VERSION,
                        resource_id=version.id,
                        project_id=project_id,
                        parent_id=dataset.id,
                        name=dataset.name,
                        version=version.version_number,
                        status=version.status,
                    ),
                    version_status=version.status,
                    published_at=version.published_at,
                )

            if version_to_dataset:
                case_rows = await session.execute(
                    select(
                        TestCaseModel.dataset_version_id,
                        TestCaseModel.case_status,
                        TestCaseModel.execution_mode,
                        TestCaseModel.priority,
                        TestCaseModel.source,
                        func.count(TestCaseModel.id),
                    )
                    .where(TestCaseModel.dataset_version_id.in_(version_to_dataset))
                    .group_by(
                        TestCaseModel.dataset_version_id,
                        TestCaseModel.case_status,
                        TestCaseModel.execution_mode,
                        TestCaseModel.priority,
                        TestCaseModel.source,
                    )
                )
                for version_id, status, mode, priority, source, count in case_rows:
                    summary = summaries[version_to_dataset[version_id]]
                    amount = int(count)
                    summary.case_count += amount
                    if status == "ready":
                        summary.ready_count += amount
                    if mode == "api":
                        summary.api_count += amount
                    elif mode == "browser":
                        summary.browser_count += amount
                    elif mode == "codex_explore":
                        summary.codex_explore_count += amount
                    if priority:
                        summary.priority_coverage[priority] = (
                            summary.priority_coverage.get(priority, 0) + amount
                        )
                    summary.source_distribution[source] = (
                        summary.source_distribution.get(source, 0) + amount
                    )
        return summaries

    async def test_plans(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, TestPlanSummaryMetrics]:
        summaries = {item_id: TestPlanSummaryMetrics() for item_id in ids}
        if not ids:
            return summaries
        async with self._session_factory() as session:
            versions_result = await session.execute(
                select(TestPlanModel, TestPlanVersionModel)
                .join(TestPlanVersionModel, TestPlanVersionModel.test_plan_id == TestPlanModel.id)
                .where(TestPlanModel.project_id == project_id, TestPlanModel.id.in_(ids))
                .order_by(TestPlanModel.id, TestPlanVersionModel.version_number.desc())
            )
            latest: dict[UUID, tuple[TestPlanModel, TestPlanVersionModel]] = {}
            for plan, version in versions_result:
                latest.setdefault(plan.id, (plan, version))
            agent_refs = await _agent_version_refs(
                session,
                project_id,
                [version.agent_version_id for _, version in latest.values()],
            )
            dataset_refs = await _dataset_version_refs(
                session,
                project_id,
                [version.dataset_version_id for _, version in latest.values()],
            )
            environment_refs = await _environment_refs(
                session,
                project_id,
                [version.environment_template_id for _, version in latest.values()],
            )
            case_counts = await _case_counts_for_versions(
                session,
                [version.dataset_version_id for _, version in latest.values()],
            )
            latest_version_to_plan: dict[UUID, UUID] = {}
            for plan_id, (plan, version) in latest.items():
                config = _dict(version.config)
                latest_version_to_plan[version.id] = plan_id
                scorer_count = len(_list(config.get("scorer_ids"))) or len(
                    _list(config.get("scorers"))
                )
                summaries[plan_id] = TestPlanSummaryMetrics(
                    latest_version=ResourceReference.build(
                        resource_type=ResourceType.TEST_PLAN_VERSION,
                        resource_id=version.id,
                        project_id=project_id,
                        parent_id=plan.id,
                        name=plan.name,
                        version=version.version_number,
                        status=version.status,
                    ),
                    version_status=version.status,
                    agent_ref=(
                        agent_refs.get(version.agent_version_id)
                        if version.agent_version_id
                        else None
                    ),
                    dataset_ref=(
                        dataset_refs.get(version.dataset_version_id)
                        if version.dataset_version_id
                        else None
                    ),
                    environment_ref=(
                        environment_refs.get(version.environment_template_id)
                        if version.environment_template_id
                        else None
                    ),
                    case_count=(
                        case_counts.get(version.dataset_version_id, 0)
                        if version.dataset_version_id
                        else 0
                    ),
                    repeat_count=_integer(config.get("runs_per_case"), 1),
                    concurrency=_integer(config.get("concurrency"), 1),
                    timeout_seconds=_optional_integer(config.get("timeout")),
                    retry_count=_integer(config.get("max_retries"), 0),
                    scorer_count=scorer_count,
                )
            if latest_version_to_plan:
                run_rows = await session.execute(
                    select(RunModel, RunEvaluationModel.pass_rate)
                    .outerjoin(RunEvaluationModel, RunEvaluationModel.run_id == RunModel.id)
                    .where(
                        RunModel.project_id == project_id,
                        RunModel.test_plan_version_id.in_(latest_version_to_plan),
                    )
                    .order_by(RunModel.test_plan_version_id, RunModel.created_at.desc())
                )
                seen_versions: set[UUID] = set()
                for run, pass_rate in run_rows:
                    version_id = run.test_plan_version_id
                    if version_id is None or version_id in seen_versions:
                        continue
                    seen_versions.add(version_id)
                    summary = summaries[latest_version_to_plan[version_id]]
                    summary.last_run_status = run.status
                    summary.pass_rate = float(pass_rate) if pass_rate is not None else None
        return summaries

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

    async def environments(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, EnvironmentSummaryMetrics]:
        summaries = {item_id: EnvironmentSummaryMetrics() for item_id in ids}
        if not ids:
            return summaries
        async with self._session_factory() as session:
            result = await session.execute(
                select(EnvironmentTemplateModel, EnvironmentVersionModel)
                .join(
                    EnvironmentVersionModel,
                    EnvironmentVersionModel.environment_template_id == EnvironmentTemplateModel.id,
                )
                .where(
                    EnvironmentTemplateModel.project_id == project_id,
                    EnvironmentTemplateModel.id.in_(ids),
                )
                .order_by(
                    EnvironmentTemplateModel.id,
                    EnvironmentVersionModel.version_number.desc(),
                )
            )
            latest: dict[UUID, tuple[EnvironmentTemplateModel, EnvironmentVersionModel]] = {}
            for template, version in result:
                latest.setdefault(template.id, (template, version))
            browser_ids: list[UUID | None] = []
            for _, version in latest.values():
                raw = _dict(version.config).get("browser_profile_id")
                browser_ids.append(_uuid(raw))
            browser_refs = await _browser_profile_refs(session, project_id, browser_ids)
            for template_id, (template, version) in latest.items():
                config = _dict(version.config)
                credential_ids = _list(config.get("credential_binding_ids"))
                browser_id = _uuid(config.get("browser_profile_id"))
                summaries[template_id] = EnvironmentSummaryMetrics(
                    current_version=ResourceReference.build(
                        resource_type=ResourceType.ENVIRONMENT_VERSION,
                        resource_id=version.id,
                        project_id=project_id,
                        parent_id=template.id,
                        name=template.name,
                        version=version.version_number,
                        status=version.status,
                    ),
                    version_status=version.status,
                    credential_binding_count=len(credential_ids),
                    browser_profile_ref=(browser_refs.get(browser_id) if browser_id else None),
                    validation_status=_string(config.get("validation_status")),
                    last_validated_at=None,
                )
            run_rows = await session.execute(
                select(TestPlanVersionModel.environment_template_id, RunModel.created_at)
                .join(RunModel, RunModel.test_plan_version_id == TestPlanVersionModel.id)
                .where(
                    RunModel.project_id == project_id,
                    TestPlanVersionModel.environment_template_id.in_(ids),
                )
                .order_by(
                    TestPlanVersionModel.environment_template_id,
                    RunModel.created_at.desc(),
                )
            )
            seen: set[UUID] = set()
            for template_id, created_at in run_rows:
                if template_id is None or template_id in seen:
                    continue
                seen.add(template_id)
                summaries[template_id].last_run_at = created_at
        return summaries

    async def scorers(self, project_id: UUID, ids: list[UUID]) -> dict[UUID, ScorerSummaryMetrics]:
        summaries = {item_id: ScorerSummaryMetrics() for item_id in ids}
        if not ids:
            return summaries
        async with self._session_factory() as session:
            result = await session.execute(
                select(ScorerModel, ScorerVersionModel)
                .join(ScorerVersionModel, ScorerVersionModel.scorer_id == ScorerModel.id)
                .where(ScorerModel.project_id == project_id, ScorerModel.id.in_(ids))
                .order_by(ScorerModel.id, ScorerVersionModel.version_number.desc())
            )
            version_to_scorer: dict[UUID, UUID] = {}
            seen: set[UUID] = set()
            for scorer, version in result:
                if scorer.id in seen:
                    continue
                seen.add(scorer.id)
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
            decision_result = await session.execute(
                select(ReleaseDecisionModel)
                .where(
                    ReleaseDecisionModel.project_id == project_id,
                    ReleaseDecisionModel.gate_id.in_(ids),
                )
                .order_by(
                    ReleaseDecisionModel.gate_id,
                    ReleaseDecisionModel.created_at.desc(),
                )
            )
            latest: dict[UUID, ReleaseDecisionModel] = {}
            for decision_row in decision_result.scalars():
                latest.setdefault(decision_row.gate_id, decision_row)
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


async def _group_count(
    session: AsyncSession, model: Any, project_column: Any, ids: list[UUID]
) -> dict[UUID, int]:
    result = await session.execute(
        select(project_column, func.count(model.id))
        .where(project_column.in_(ids))
        .group_by(project_column)
    )
    return {project_id: int(count) for project_id, count in result}


async def _agent_version_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(AgentVersionModel, AgentModel)
        .join(AgentModel, AgentModel.id == AgentVersionModel.agent_id)
        .where(AgentModel.project_id == project_id, AgentVersionModel.id.in_(values))
    )
    return {
        version.id: ResourceReference.build(
            resource_type=ResourceType.AGENT_VERSION,
            resource_id=version.id,
            project_id=project_id,
            parent_id=agent.id,
            name=agent.name,
            version=version.version_number,
            status=version.status,
        )
        for version, agent in result
    }


async def _dataset_version_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(DatasetVersionModel, DatasetModel)
        .join(DatasetModel, DatasetModel.id == DatasetVersionModel.dataset_id)
        .where(DatasetModel.project_id == project_id, DatasetVersionModel.id.in_(values))
    )
    return {
        version.id: ResourceReference.build(
            resource_type=ResourceType.DATASET_VERSION,
            resource_id=version.id,
            project_id=project_id,
            parent_id=dataset.id,
            name=dataset.name,
            version=version.version_number,
            status=version.status,
        )
        for version, dataset in result
    }


async def _plan_version_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(TestPlanVersionModel, TestPlanModel)
        .join(TestPlanModel, TestPlanModel.id == TestPlanVersionModel.test_plan_id)
        .where(TestPlanModel.project_id == project_id, TestPlanVersionModel.id.in_(values))
    )
    return {
        version.id: ResourceReference.build(
            resource_type=ResourceType.TEST_PLAN_VERSION,
            resource_id=version.id,
            project_id=project_id,
            parent_id=plan.id,
            name=plan.name,
            version=version.version_number,
            status=version.status,
        )
        for version, plan in result
    }


async def _environment_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(EnvironmentTemplateModel).where(
            EnvironmentTemplateModel.project_id == project_id,
            EnvironmentTemplateModel.id.in_(values),
        )
    )
    return {
        item.id: ResourceReference.build(
            resource_type=ResourceType.ENVIRONMENT,
            resource_id=item.id,
            project_id=project_id,
            name=item.name,
        )
        for item in result.scalars()
    }


async def _case_counts_for_versions(
    session: AsyncSession, ids: Iterable[UUID | None]
) -> dict[UUID, int]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(TestCaseModel.dataset_version_id, func.count(TestCaseModel.id))
        .where(TestCaseModel.dataset_version_id.in_(values))
        .group_by(TestCaseModel.dataset_version_id)
    )
    return {version_id: int(count) for version_id, count in result}


async def _case_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(TestCaseModel)
        .join(DatasetVersionModel, DatasetVersionModel.id == TestCaseModel.dataset_version_id)
        .join(DatasetModel, DatasetModel.id == DatasetVersionModel.dataset_id)
        .where(DatasetModel.project_id == project_id, TestCaseModel.id.in_(values))
    )
    return {
        item.id: ResourceReference.build(
            resource_type=ResourceType.TEST_CASE,
            resource_id=item.id,
            project_id=project_id,
            name=item.name,
            key=item.case_key,
            status=item.case_status,
        )
        for item in result.scalars()
    }


async def _user_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(select(UserModel).where(UserModel.id.in_(values)))
    return {
        user.id: ResourceReference.build(
            resource_type=ResourceType.USER,
            resource_id=user.id,
            project_id=project_id,
            name=user.display_name,
            status=user.status,
        )
        for user in result.scalars()
    }


async def _browser_profile_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(BrowserProfileModel).where(
            BrowserProfileModel.project_id == project_id,
            BrowserProfileModel.id.in_(values),
        )
    )
    return {
        item.id: ResourceReference.build(
            resource_type=ResourceType.ENVIRONMENT,
            resource_id=item.id,
            project_id=project_id,
            name=item.name,
            status=item.auth_state_status,
        )
        for item in result.scalars()
    }


async def _run_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(RunModel).where(RunModel.project_id == project_id, RunModel.id.in_(values))
    )
    return {run.id: _run_ref(run) for run in result.scalars()}


async def _security_profile_refs(
    session: AsyncSession, project_id: UUID, ids: Iterable[UUID | None]
) -> dict[UUID, ResourceReference]:
    values = _ids(ids)
    if not values:
        return {}
    result = await session.execute(
        select(SecurityProfileModel).where(
            SecurityProfileModel.project_id == project_id,
            SecurityProfileModel.id.in_(values),
        )
    )
    return {
        profile.id: ResourceReference.build(
            resource_type=ResourceType.SECURITY_PROFILE,
            resource_id=profile.id,
            project_id=project_id,
            name=profile.name,
            status=profile.status,
        )
        for profile in result.scalars()
    }


def _run_ref(run: RunModel) -> ResourceReference:
    return ResourceReference.build(
        resource_type=ResourceType.RUN,
        resource_id=run.id,
        project_id=run.project_id,
        name=f"RUN-{str(run.id).split('-')[0].upper()}",
        status=run.status,
    )


def _ids(values: Iterable[UUID | None]) -> list[UUID]:
    return list({value for value in values if value is not None})


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _string(value: object) -> str | None:
    return str(value) if value is not None and str(value) else None


def _integer(value: object, default: int) -> int:
    if not isinstance(value, (str, bytes, bytearray, int, float)):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _optional_integer(value: object) -> int | None:
    return _integer(value, 0) if value is not None else None


def _optional_float(value: object) -> float | None:
    if not isinstance(value, (str, int, float)):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _age_seconds(now: datetime, created_at: datetime) -> int:
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    return max(0, int((now - created_at).total_seconds()))


def _uuid(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if isinstance(value, str) and value:
        try:
            return UUID(value)
        except ValueError:
            return None
    return None
