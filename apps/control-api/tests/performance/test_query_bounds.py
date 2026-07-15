from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import UUID, uuid4

import agenttest.bootstrap.wiring  # noqa: F401 - register all ORM metadata
import pytest
from agenttest.modules.experiments.application.service import ExperimentService
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
from agenttest.modules.runs.infrastructure.persistence.models import RunCaseModel, RunModel
from agenttest.modules.runs.infrastructure.persistence.repositories import SqlAlchemyRunRepository
from agenttest.shared.infrastructure.database import Base
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class AllowProjectAccess:
    async def ensure_member(self, _actor: User, _project_id: object) -> None:
        return None


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


def run_model(*, project_id: UUID, run_id: UUID, case_count: int) -> RunModel:
    now = datetime.now(UTC)
    return RunModel(
        id=run_id,
        project_id=project_id,
        test_plan_version_id=uuid4(),
        agent_version_id=uuid4(),
        dataset_version_id=uuid4(),
        idempotency_key=str(run_id),
        status="passed",
        config_snapshot={},
        plugin_snapshot={},
        total_cases=case_count,
        passed_cases=case_count,
        failed_cases=0,
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


def project_models(creator: UUID, indexes: range) -> list[ProjectModel | ProjectMemberModel]:
    now = datetime.now(UTC)
    models: list[ProjectModel | ProjectMemberModel] = []
    for index in indexes:
        project_id = uuid4()
        models.extend(
            [
                ProjectModel(
                    id=project_id,
                    name=f"project-{index}",
                    description=None,
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
