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
    _browser_profile_refs,
    _case_counts_for_versions,
    _dataset_version_refs,
    _dict,
    _environment_refs,
    _group_count,
    _integer,
    _list,
    _optional_integer,
    _run_ref,
    _string,
    _uuid,
)
from agenttest.modules.agents.infrastructure.persistence.models import (
    AgentModel,
    AgentVersionModel,
)
from agenttest.modules.datasets.infrastructure.persistence.models import (
    DatasetModel,
    DatasetVersionModel,
    TestCaseModel,
)
from agenttest.modules.environments.infrastructure.persistence.models import (
    EnvironmentTemplateModel,
    EnvironmentVersionModel,
)
from agenttest.modules.projects.infrastructure.persistence.models import ProjectMemberModel
from agenttest.modules.reviews.infrastructure.persistence.models import ReviewTaskModel
from agenttest.modules.runs.infrastructure.persistence.models import (
    RunEvaluationModel,
    RunModel,
)
from agenttest.modules.test_plans.infrastructure.persistence.models import (
    TestPlanModel,
    TestPlanVersionModel,
)
from agenttest.shared.application.core_summaries import (
    AgentSummaryMetrics,
    DatasetSummaryMetrics,
    EnvironmentSummaryMetrics,
    ProjectSummaryMetrics,
    TestPlanSummaryMetrics,
)
from agenttest.shared.application.resource_reference import (
    ResourceReference,
    ResourceType,
)


class AssetSummaryQueries:
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

            ranked_runs = (
                select(
                    RunModel.id.label("row_id"),
                    func.row_number()
                    .over(
                        partition_by=RunModel.project_id,
                        order_by=(RunModel.created_at.desc(), RunModel.id.desc()),
                    )
                    .label("row_rank"),
                )
                .where(RunModel.project_id.in_(ids))
                .subquery()
            )
            latest_runs = await session.execute(
                select(RunModel)
                .join(ranked_runs, ranked_runs.c.row_id == RunModel.id)
                .where(ranked_runs.c.row_rank == 1)
            )
            for run in latest_runs.scalars():
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
                ranked_runs = (
                    select(
                        RunModel.id.label("row_id"),
                        func.row_number()
                        .over(
                            partition_by=RunModel.agent_version_id,
                            order_by=(RunModel.created_at.desc(), RunModel.id.desc()),
                        )
                        .label("row_rank"),
                    )
                    .where(
                        RunModel.project_id == project_id,
                        RunModel.agent_version_id.in_(version_to_agent),
                    )
                    .subquery()
                )
                run_rows = await session.execute(
                    select(RunModel, RunEvaluationModel.pass_rate)
                    .join(ranked_runs, ranked_runs.c.row_id == RunModel.id)
                    .outerjoin(RunEvaluationModel, RunEvaluationModel.run_id == RunModel.id)
                    .where(ranked_runs.c.row_rank == 1)
                )
                for run, pass_rate in run_rows:
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
            ranked_versions = (
                select(
                    DatasetVersionModel.id.label("row_id"),
                    func.row_number()
                    .over(
                        partition_by=DatasetVersionModel.dataset_id,
                        order_by=(
                            DatasetVersionModel.version_number.desc(),
                            DatasetVersionModel.id.desc(),
                        ),
                    )
                    .label("row_rank"),
                )
                .join(DatasetModel, DatasetModel.id == DatasetVersionModel.dataset_id)
                .where(DatasetModel.project_id == project_id, DatasetModel.id.in_(ids))
                .subquery()
            )
            result = await session.execute(
                select(DatasetModel, DatasetVersionModel)
                .join(DatasetVersionModel, DatasetVersionModel.dataset_id == DatasetModel.id)
                .join(ranked_versions, ranked_versions.c.row_id == DatasetVersionModel.id)
                .where(ranked_versions.c.row_rank == 1)
            )
            version_to_dataset: dict[UUID, UUID] = {}
            for dataset, version in result:
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
            ranked_versions = (
                select(
                    TestPlanVersionModel.id.label("row_id"),
                    func.row_number()
                    .over(
                        partition_by=TestPlanVersionModel.test_plan_id,
                        order_by=(
                            TestPlanVersionModel.version_number.desc(),
                            TestPlanVersionModel.id.desc(),
                        ),
                    )
                    .label("row_rank"),
                )
                .join(TestPlanModel, TestPlanModel.id == TestPlanVersionModel.test_plan_id)
                .where(TestPlanModel.project_id == project_id, TestPlanModel.id.in_(ids))
                .subquery()
            )
            versions_result = await session.execute(
                select(TestPlanModel, TestPlanVersionModel)
                .join(TestPlanVersionModel, TestPlanVersionModel.test_plan_id == TestPlanModel.id)
                .join(ranked_versions, ranked_versions.c.row_id == TestPlanVersionModel.id)
                .where(ranked_versions.c.row_rank == 1)
            )
            latest = {plan.id: (plan, version) for plan, version in versions_result}
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
                ranked_runs = (
                    select(
                        RunModel.id.label("row_id"),
                        func.row_number()
                        .over(
                            partition_by=RunModel.test_plan_version_id,
                            order_by=(RunModel.created_at.desc(), RunModel.id.desc()),
                        )
                        .label("row_rank"),
                    )
                    .where(
                        RunModel.project_id == project_id,
                        RunModel.test_plan_version_id.in_(latest_version_to_plan),
                    )
                    .subquery()
                )
                run_rows = await session.execute(
                    select(RunModel, RunEvaluationModel.pass_rate)
                    .join(ranked_runs, ranked_runs.c.row_id == RunModel.id)
                    .outerjoin(RunEvaluationModel, RunEvaluationModel.run_id == RunModel.id)
                    .where(ranked_runs.c.row_rank == 1)
                )
                for run, pass_rate in run_rows:
                    version_id = run.test_plan_version_id
                    if version_id is None:
                        continue
                    summary = summaries[latest_version_to_plan[version_id]]
                    summary.last_run_status = run.status
                    summary.pass_rate = float(pass_rate) if pass_rate is not None else None
        return summaries

    async def environments(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, EnvironmentSummaryMetrics]:
        summaries = {item_id: EnvironmentSummaryMetrics() for item_id in ids}
        if not ids:
            return summaries
        async with self._session_factory() as session:
            ranked_versions = (
                select(
                    EnvironmentVersionModel.id.label("row_id"),
                    func.row_number()
                    .over(
                        partition_by=EnvironmentVersionModel.environment_template_id,
                        order_by=(
                            EnvironmentVersionModel.version_number.desc(),
                            EnvironmentVersionModel.id.desc(),
                        ),
                    )
                    .label("row_rank"),
                )
                .join(
                    EnvironmentTemplateModel,
                    EnvironmentTemplateModel.id == EnvironmentVersionModel.environment_template_id,
                )
                .where(
                    EnvironmentTemplateModel.project_id == project_id,
                    EnvironmentTemplateModel.id.in_(ids),
                )
                .subquery()
            )
            result = await session.execute(
                select(EnvironmentTemplateModel, EnvironmentVersionModel)
                .join(
                    EnvironmentVersionModel,
                    EnvironmentVersionModel.environment_template_id == EnvironmentTemplateModel.id,
                )
                .where(
                    ranked_versions.c.row_rank == 1,
                )
                .join(
                    ranked_versions,
                    ranked_versions.c.row_id == EnvironmentVersionModel.id,
                )
            )
            latest = {template.id: (template, version) for template, version in result}
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
            ranked_runs = (
                select(
                    TestPlanVersionModel.environment_template_id.label("template_id"),
                    RunModel.created_at.label("created_at"),
                    func.row_number()
                    .over(
                        partition_by=TestPlanVersionModel.environment_template_id,
                        order_by=(RunModel.created_at.desc(), RunModel.id.desc()),
                    )
                    .label("row_rank"),
                )
                .join(RunModel, RunModel.test_plan_version_id == TestPlanVersionModel.id)
                .where(
                    RunModel.project_id == project_id,
                    TestPlanVersionModel.environment_template_id.in_(ids),
                )
                .subquery()
            )
            run_rows = await session.execute(
                select(ranked_runs.c.template_id, ranked_runs.c.created_at).where(
                    ranked_runs.c.row_rank == 1
                )
            )
            for template_id, created_at in run_rows:
                if template_id is None:
                    continue
                summaries[template_id].last_run_at = created_at
        return summaries
