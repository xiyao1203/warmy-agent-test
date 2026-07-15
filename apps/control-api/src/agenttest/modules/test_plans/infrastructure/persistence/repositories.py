"""TestPlan 仓库的 SQLAlchemy 实现。"""

from __future__ import annotations

from base64 import b64decode, b64encode
from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.agents.public import AgentVersionId
from agenttest.modules.datasets.public import DatasetVersionId
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_plans.application.dry_run import DryRunReadModel
from agenttest.modules.test_plans.domain.entities import (
    EnvironmentTemplateId,
    TestPlan,
    TestPlanId,
    TestPlanVersion,
    TestPlanVersionId,
)
from agenttest.modules.test_plans.domain.value_objects import (
    TestPlanConfig,
    VersionStatus,
)
from agenttest.modules.test_plans.infrastructure.persistence.models import (
    TestPlanModel,
    TestPlanVersionModel,
)
from agenttest.shared.infrastructure.database import session_scope, transaction_scope


class SqlAlchemyTestPlanRepository:
    """测试计划聚合根的 SQLAlchemy 仓库实现。"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, test_plan_id: TestPlanId) -> TestPlan | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(TestPlanModel, test_plan_id.value)
        return _to_plan(model) if model else None

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[TestPlan], str | None]:
        statement = (
            select(TestPlanModel)
            .where(TestPlanModel.project_id == project_id.value)
            .order_by(TestPlanModel.created_at.desc())
            .limit(limit + 1)
        )
        if cursor is not None:
            cursor_ts = _decode_cursor(cursor)
            statement = statement.where(TestPlanModel.created_at < cursor_ts)
        async with session_scope(self._session_factory) as session:
            models = list((await session.scalars(statement)).all())
        has_more = len(models) > limit
        if has_more:
            models = models[:limit]
        next_cursor = _encode_cursor(models[-1].created_at) if has_more and models else None
        return [_to_plan(m) for m in models], next_cursor

    async def add(self, plan: TestPlan) -> None:
        async with transaction_scope(self._session_factory) as session:
            session.add(
                TestPlanModel(
                    id=plan.test_plan_id.value,
                    project_id=plan.project_id.value,
                    name=plan.name,
                    description=plan.description,
                    created_at=plan.created_at,
                    updated_at=plan.updated_at,
                    created_by=plan.created_by.value,
                    updated_by=plan.updated_by.value,
                )
            )

    async def save(self, plan: TestPlan) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                update(TestPlanModel)
                .where(TestPlanModel.id == plan.test_plan_id.value)
                .values(
                    name=plan.name,
                    description=plan.description,
                    updated_at=plan.updated_at,
                    updated_by=plan.updated_by.value,
                )
            )

    async def delete(self, test_plan_id: TestPlanId) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                delete(TestPlanModel).where(TestPlanModel.id == test_plan_id.value)
            )


class SqlAlchemyTestPlanVersionRepository:
    """测试计划版本的 SQLAlchemy 仓库实现。"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, version_id: TestPlanVersionId) -> TestPlanVersion | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(TestPlanVersionModel, version_id.value)
        return _to_version(model) if model else None

    async def list_by_test_plan(self, test_plan_id: TestPlanId) -> list[TestPlanVersion]:
        statement = (
            select(TestPlanVersionModel)
            .where(TestPlanVersionModel.test_plan_id == test_plan_id.value)
            .order_by(TestPlanVersionModel.version_number.desc())
        )
        async with session_scope(self._session_factory) as session:
            models = list((await session.scalars(statement)).all())
        return [_to_version(m) for m in models]

    async def get_next_version_number(self, test_plan_id: TestPlanId) -> int:
        statement = select(func.max(TestPlanVersionModel.version_number)).where(
            TestPlanVersionModel.test_plan_id == test_plan_id.value
        )
        async with session_scope(self._session_factory) as session:
            result = await session.scalar(statement)
        return (result or 0) + 1

    async def add(self, version: TestPlanVersion) -> None:
        async with transaction_scope(self._session_factory) as session:
            av_id = version.agent_version_id
            dv_id = version.dataset_version_id
            et_id = version.environment_template_id
            session.add(
                TestPlanVersionModel(
                    id=version.version_id.value,
                    test_plan_id=version.test_plan_id.value,
                    version_number=version.version_number,
                    status=version.status.value,
                    config=version.config.to_dict(),
                    agent_version_id=av_id.value if av_id else None,
                    dataset_version_id=dv_id.value if dv_id else None,
                    environment_template_id=et_id.value if et_id else None,
                    published_at=version.published_at,
                    created_at=version.created_at,
                    updated_at=version.updated_at,
                    created_by=version.created_by.value,
                )
            )

    async def save(self, version: TestPlanVersion) -> None:
        async with transaction_scope(self._session_factory) as session:
            av_id = version.agent_version_id
            dv_id = version.dataset_version_id
            et_id = version.environment_template_id
            await session.execute(
                update(TestPlanVersionModel)
                .where(TestPlanVersionModel.id == version.version_id.value)
                .values(
                    status=version.status.value,
                    config=version.config.to_dict(),
                    agent_version_id=av_id.value if av_id else None,
                    dataset_version_id=dv_id.value if dv_id else None,
                    environment_template_id=et_id.value if et_id else None,
                    published_at=version.published_at,
                    updated_at=version.updated_at,
                )
            )

    async def get_dry_run_model(
        self,
        project_id: UUID,
        plan_id: UUID,
        version_id: UUID,
    ) -> DryRunReadModel | None:
        async with session_scope(self._session_factory) as session:
            model = await session.scalar(
                select(TestPlanVersionModel)
                .join(TestPlanModel, TestPlanModel.id == TestPlanVersionModel.test_plan_id)
                .where(
                    TestPlanVersionModel.id == version_id,
                    TestPlanModel.id == plan_id,
                    TestPlanModel.project_id == project_id,
                )
            )
            if model is None:
                return None
            version = _to_version(model)
            agent_ready = await _exists(
                session,
                "agent_versions",
                version.agent_version_id.value if version.agent_version_id else None,
                published=True,
            )
            dataset_ready = await _exists(
                session,
                "dataset_versions",
                version.dataset_version_id.value if version.dataset_version_id else None,
                published=True,
            )
            environment_ready = await _environment_exists(
                session,
                project_id,
                (
                    version.environment_template_id.value
                    if version.environment_template_id
                    else None
                ),
            )
            num_cases = 0
            if version.dataset_version_id is not None:
                num_cases = int(
                    await session.scalar(
                        text(
                            "SELECT COUNT(*) FROM test_cases WHERE dataset_version_id = :version_id"
                        ),
                        {"version_id": version.dataset_version_id.value},
                    )
                    or 0
                )
        return DryRunReadModel(
            version=version,
            agent_ready=agent_ready,
            dataset_ready=dataset_ready,
            environment_ready=environment_ready,
            num_cases=num_cases,
        )


async def _exists(
    session: AsyncSession,
    table_name: str,
    value: UUID | None,
    *,
    published: bool,
) -> bool:
    if value is None:
        return True
    if table_name not in {"agent_versions", "dataset_versions"}:
        raise ValueError("Unsupported dry-run asset table")
    status_clause = " AND status = 'published'" if published else ""
    statement = text(f"SELECT 1 FROM {table_name} WHERE id = :value{status_clause}")
    return await session.scalar(statement, {"value": value}) is not None


async def _environment_exists(
    session: AsyncSession,
    project_id: UUID,
    value: UUID | None,
) -> bool:
    if value is None:
        return True
    return (
        await session.scalar(
            text(
                "SELECT 1 FROM environment_templates WHERE id = :value AND project_id = :project_id"
            ),
            {"value": value, "project_id": project_id},
        )
        is not None
    )


# ── Mappers ─────────────────────────────────────────────────────────────────


def _to_plan(model: TestPlanModel) -> TestPlan:
    """ORM 模型 → 领域实体映射。"""
    return TestPlan(
        test_plan_id=TestPlanId(model.id),
        project_id=ProjectId(model.project_id),
        name=model.name,
        created_by=UserId(model.created_by),
        updated_by=UserId(model.updated_by),
        created_at=model.created_at,
        updated_at=model.updated_at,
        description=model.description,
    )


def _to_version(model: TestPlanVersionModel) -> TestPlanVersion:
    """ORM 模型 → 领域实体映射。"""
    return TestPlanVersion(
        version_id=TestPlanVersionId(model.id),
        test_plan_id=TestPlanId(model.test_plan_id),
        version_number=model.version_number,
        status=VersionStatus(model.status),
        config=TestPlanConfig.from_dict(model.config),
        created_by=UserId(model.created_by),
        created_at=model.created_at,
        updated_at=model.updated_at,
        agent_version_id=(
            AgentVersionId(model.agent_version_id) if model.agent_version_id else None
        ),
        dataset_version_id=(
            DatasetVersionId(model.dataset_version_id) if model.dataset_version_id else None
        ),
        environment_template_id=(
            EnvironmentTemplateId(model.environment_template_id)
            if model.environment_template_id
            else None
        ),
        published_at=model.published_at,
    )


# ── Cursor helpers ──────────────────────────────────────────────────────────


def _encode_cursor(ts: datetime) -> str:
    return b64encode(ts.isoformat().encode()).decode()


def _decode_cursor(cursor: str) -> datetime:
    return datetime.fromisoformat(b64decode(cursor.encode()).decode())
