from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock
from uuid import UUID, uuid4

import pytest
from agenttest.bootstrap.core_summaries import SqlAlchemyCoreSummaryReader
from agenttest.bootstrap.model_registry import register_models
from agenttest.modules.agents.infrastructure.persistence.models import (
    AgentModel,
    AgentVersionModel,
)
from agenttest.modules.experiments.application.service import ExperimentService
from agenttest.modules.gates.infrastructure.persistence.models import (
    ReleaseDecisionModel,
    ReleaseGateModel,
)
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.application.queries.list_projects import ListProjectsHandler
from agenttest.modules.projects.infrastructure.persistence.models import (
    ProjectMemberModel,
    ProjectModel,
)
from agenttest.modules.projects.infrastructure.persistence.repositories import (
    SqlAlchemyProjectRepository,
)
from agenttest.modules.runs.application.comparison import RunComparisonService
from agenttest.modules.runs.infrastructure.persistence.models import (
    RunCaseModel,
    RunEvaluationModel,
    RunModel,
)
from agenttest.modules.runs.infrastructure.persistence.repositories import SqlAlchemyRunRepository
from agenttest.shared.infrastructure.database import Base
from sqlalchemy import event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.compiler import compiles

register_models()


class AllowProjectAccess:
    async def ensure_member(self, _actor: User, _project_id: object) -> None:
        return None


@compiles(JSONB, "sqlite")
def compile_jsonb_for_sqlite(_type, _compiler, **_kwargs) -> str:
    return "JSON"


def actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("performance@example.test"),
        display_name="Performance Tester",
        role=SystemRole.SUPER_ADMIN,
    )


async def database() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_connection: Base.metadata.create_all(
                sync_connection,
                tables=[
                    ProjectModel.__table__,
                    ProjectMemberModel.__table__,
                    RunModel.__table__,
                    RunCaseModel.__table__,
                ],
            )
        )
    return engine, async_sessionmaker(engine, expire_on_commit=False)


async def count_queries(engine: AsyncEngine, operation: Callable[[], Awaitable[object]]) -> int:
    statements: list[str] = []

    def record_query(_connection, _cursor, statement, _parameters, _context, _many) -> None:
        statements.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", record_query)
    try:
        await operation()
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", record_query)
    return len(statements)


def run_model(
    *,
    project_id: UUID,
    run_id: UUID,
    case_count: int,
    agent_version_id: UUID | None = None,
    created_at: datetime | None = None,
    status: str = "passed",
) -> RunModel:
    now = created_at or datetime.now(UTC)
    return RunModel(
        id=run_id,
        project_id=project_id,
        test_plan_version_id=uuid4(),
        agent_version_id=agent_version_id or uuid4(),
        dataset_version_id=uuid4(),
        idempotency_key=str(run_id),
        status=status,
        config_snapshot={},
        plugin_snapshot={},
        total_cases=case_count,
        passed_cases=case_count if status == "passed" else 0,
        failed_cases=case_count if status == "failed" else 0,
        error_cases=0,
        cancelled_cases=0,
        workflow_id=None,
        session_id=None,
        created_by=uuid4(),
        created_at=now,
        updated_at=now,
        started_at=now,
        completed_at=now,
    )


def case_models(run_id: UUID, count: int) -> list[RunCaseModel]:
    now = datetime.now(UTC)
    return [
        RunCaseModel(
            id=uuid4(),
            run_id=run_id,
            test_case_id=uuid4(),
            name=f"case-{index}",
            execution_mode="api",
            status="passed",
            input_snapshot={},
            assertion_snapshot=[],
            output={"ok": True},
            trace=[],
            duration_ms=index + 1,
            evidence={},
            quality_summary={},
            security_summary={},
            outcomes={},
            created_at=now,
            updated_at=now,
            started_at=now,
            completed_at=now,
        )
        for index in range(count)
    ]


@pytest.mark.asyncio
async def test_run_comparison_query_count_is_independent_of_case_count() -> None:
    engine, sessions = await database()
    project_id = uuid4()
    pairs: list[tuple[UUID, UUID]] = []
    try:
        async with sessions.begin() as session:
            for count in (1, 40):
                left, right = uuid4(), uuid4()
                pairs.append((left, right))
                session.add_all(
                    [
                        run_model(project_id=project_id, run_id=left, case_count=count),
                        run_model(project_id=project_id, run_id=right, case_count=count),
                        *case_models(left, count),
                        *case_models(right, count),
                    ]
                )
        service = RunComparisonService(
            runs=SqlAlchemyRunRepository(sessions),
            project_access=AllowProjectAccess(),
        )
        counts = [
            await count_queries(
                engine,
                lambda pair=pair: service.compare(actor(), project_id, pair[0], pair[1]),
            )
            for pair in pairs
        ]
        assert counts == [4, 4]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_experiment_statistics_query_count_is_independent_of_case_count() -> None:
    engine, sessions = await database()
    project_id = uuid4()
    run_ids: list[UUID] = []
    try:
        async with sessions.begin() as session:
            for count in (1, 40):
                run_id = uuid4()
                run_ids.append(run_id)
                session.add_all(
                    [
                        run_model(project_id=project_id, run_id=run_id, case_count=count),
                        *case_models(run_id, count),
                    ]
                )
        service = ExperimentService(
            experiments=Mock(),
            runs=SqlAlchemyRunRepository(sessions),
            project_access=AllowProjectAccess(),
        )
        counts = [
            await count_queries(
                engine,
                lambda run_id=run_id: service.statistics(
                    actor(), project_id, run_id=run_id, experiment_id=None
                ),
            )
            for run_id in run_ids
        ]
        assert counts == [2, 2]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_project_list_uses_two_queries_regardless_of_project_count() -> None:
    engine, sessions = await database()
    creator = uuid4()
    try:
        handler = ListProjectsHandler(projects=SqlAlchemyProjectRepository(sessions))
        query_counts = []
        async with sessions.begin() as session:
            session.add_all(project_models(creator, range(1)))
        query_counts.append(await count_queries(engine, lambda: handler.execute(actor())))
        async with sessions.begin() as session:
            session.add_all(project_models(creator, range(1, 40)))
        query_counts.append(await count_queries(engine, lambda: handler.execute(actor())))
        assert query_counts == [2, 2]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_core_agent_summaries_do_not_add_queries_per_list_row() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_connection: Base.metadata.create_all(
                sync_connection,
                tables=[
                    AgentModel.__table__,
                    AgentVersionModel.__table__,
                    RunModel.__table__,
                    RunEvaluationModel.__table__,
                ],
            )
        )
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    project_id = uuid4()
    creator = uuid4()
    ids: list[UUID] = []
    try:
        reader = SqlAlchemyCoreSummaryReader(sessions)
        query_counts: list[int] = []
        for start, stop in ((0, 1), (1, 40)):
            batch_ids, models = agent_history_models(
                project_id,
                creator,
                range(start, stop),
                history_count=12,
            )
            ids.extend(batch_ids)
            async with sessions.begin() as session:
                session.add_all(models)
            summaries = await reader.agents(project_id, ids)
            query_counts.append(await count_queries(engine, lambda: reader.agents(project_id, ids)))
            for agent_id in batch_ids:
                assert summaries[agent_id].current_version is not None
                assert summaries[agent_id].last_run_status == "failed"
                assert summaries[agent_id].pass_rate == 0.25
        assert query_counts == [2, 2]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_core_gate_summaries_select_only_the_latest_deep_history_decision() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_connection: Base.metadata.create_all(
                sync_connection,
                tables=[
                    RunModel.__table__,
                    ReleaseGateModel.__table__,
                    ReleaseDecisionModel.__table__,
                ],
            )
        )
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    project_id = uuid4()
    evaluator = uuid4()
    ids: list[UUID] = []
    try:
        reader = SqlAlchemyCoreSummaryReader(sessions)
        query_counts: list[int] = []
        for start, stop in ((0, 1), (1, 40)):
            batch_ids, models = gate_history_models(
                project_id,
                evaluator,
                range(start, stop),
                history_count=12,
            )
            ids.extend(batch_ids)
            async with sessions.begin() as session:
                session.add_all(models)
            summaries = await reader.gates(project_id, ids)
            query_counts.append(await count_queries(engine, lambda: reader.gates(project_id, ids)))
            for gate_id in batch_ids:
                assert summaries[gate_id].last_decision == "block"
                assert summaries[gate_id].blocking_count == 1
        assert query_counts == [3, 3]
    finally:
        await engine.dispose()


def project_models(creator: UUID, indexes: range) -> list[ProjectModel | ProjectMemberModel]:
    now = datetime.now(UTC)
    models: list[ProjectModel | ProjectMemberModel] = []
    for index in indexes:
        project_id = uuid4()
        models.extend(
            [
                ProjectModel(
                    id=project_id,
                    key=f"PRJ{index:06d}",
                    name=f"project-{index}",
                    description=None,
                    lead_user_id=None,
                    archived_at=None,
                    created_at=now,
                    updated_at=now,
                    created_by=creator,
                    updated_by=creator,
                ),
                ProjectMemberModel(
                    id=uuid4(),
                    project_id=project_id,
                    user_id=creator,
                    role="developer",
                    created_at=now,
                    updated_at=now,
                    created_by=creator,
                    updated_by=creator,
                ),
            ]
        )
    return models


def agent_history_models(
    project_id: UUID,
    creator: UUID,
    indexes: range,
    *,
    history_count: int,
) -> tuple[list[UUID], list[AgentModel | AgentVersionModel | RunModel | RunEvaluationModel]]:
    now = datetime.now(UTC)
    ids: list[UUID] = []
    models: list[AgentModel | AgentVersionModel | RunModel | RunEvaluationModel] = []
    for index in indexes:
        agent_id = uuid4()
        version_id = uuid4()
        ids.append(agent_id)
        models.extend(
            [
                AgentModel(
                    id=agent_id,
                    project_id=project_id,
                    name=f"agent-{index}",
                    description=None,
                    agent_type="generic_http",
                    current_version_id=version_id,
                    baseline_version_id=None,
                    created_at=now,
                    updated_at=now,
                    created_by=creator,
                    updated_by=creator,
                ),
                AgentVersionModel(
                    id=version_id,
                    agent_id=agent_id,
                    version_number=3,
                    status="published",
                    config={"protocol": "sync_json", "model": "gpt-5", "tools": ["run"]},
                    schema_version=1,
                    invocation_config=None,
                    readiness_status="ready",
                    published_at=now,
                    created_at=now,
                    updated_at=now,
                    created_by=creator,
                ),
            ]
        )
        for history_index in range(history_count):
            run_id = uuid4()
            run_created_at = now + timedelta(seconds=history_index)
            is_latest = history_index == history_count - 1
            models.append(
                run_model(
                    project_id=project_id,
                    run_id=run_id,
                    case_count=1,
                    agent_version_id=version_id,
                    created_at=run_created_at,
                    status="failed" if is_latest else "passed",
                )
            )
            if is_latest:
                models.append(
                    RunEvaluationModel(
                        id=uuid4(),
                        project_id=project_id,
                        run_id=run_id,
                        status="completed",
                        aggregate_score=0.25,
                        pass_rate=0.25,
                        total_cost=0.01,
                        token_usage={"total": 10},
                        summary={},
                        created_at=run_created_at,
                        updated_at=run_created_at,
                    )
                )
    return ids, models


def gate_history_models(
    project_id: UUID,
    evaluator: UUID,
    indexes: range,
    *,
    history_count: int,
) -> tuple[list[UUID], list[ReleaseGateModel | ReleaseDecisionModel | RunModel]]:
    now = datetime.now(UTC)
    ids: list[UUID] = []
    models: list[ReleaseGateModel | ReleaseDecisionModel | RunModel] = []
    for index in indexes:
        gate_id = uuid4()
        ids.append(gate_id)
        models.append(
            ReleaseGateModel(
                id=gate_id,
                project_id=project_id,
                name=f"gate-{index}",
                success_rate_threshold=0.9,
                critical_cases=[],
                cost_limit=1.0,
                security_threshold=0.9,
                enabled=True,
                created_at=now,
                updated_at=now,
            )
        )
        for history_index in range(history_count):
            created_at = now + timedelta(seconds=history_index)
            is_latest = history_index == history_count - 1
            run_id = uuid4()
            models.extend(
                [
                    run_model(
                        project_id=project_id,
                        run_id=run_id,
                        case_count=1,
                        created_at=created_at,
                    ),
                    ReleaseDecisionModel(
                        id=uuid4(),
                        project_id=project_id,
                        gate_id=gate_id,
                        run_id=run_id,
                        experiment_id=None,
                        status="block" if is_latest else "pass",
                        facts={},
                        failures=[{"code": "quality"}] if is_latest else [],
                        evidence={},
                        evaluated_by=evaluator,
                        created_at=created_at,
                        updated_at=created_at,
                    ),
                ]
            )
    return ids, models
