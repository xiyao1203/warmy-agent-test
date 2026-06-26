"""Dataset 仓库的 SQLAlchemy 实现。

提供 Dataset、DatasetVersion 和 TestCase 的持久化实现，
遵循领域层定义的仓库接口。
"""

from __future__ import annotations

from base64 import b64decode, b64encode
from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.datasets.domain.entities import (
    Dataset,
    DatasetId,
    DatasetVersion,
    DatasetVersionId,
    TestCase,
    TestCaseId,
)
from agenttest.modules.datasets.domain.value_objects import (
    ExecutionMode,
    Priority,
    RiskLevel,
    TestGroup,
    VersionStatus,
)
from agenttest.modules.datasets.infrastructure.persistence.models import (
    DatasetModel,
    DatasetVersionModel,
    TestCaseModel,
)
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.shared.infrastructure.database import session_scope, transaction_scope


class SqlAlchemyDatasetRepository:
    """数据集聚合根的 SQLAlchemy 仓库实现。"""
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, dataset_id: DatasetId) -> Dataset | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(DatasetModel, dataset_id.value)
        return _to_dataset(model) if model else None

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Dataset], str | None]:
        statement = (
            select(DatasetModel)
            .where(DatasetModel.project_id == project_id.value)
            .order_by(DatasetModel.created_at.desc())
            .limit(limit + 1)
        )
        if cursor is not None:
            cursor_ts = _decode_cursor(cursor)
            statement = statement.where(DatasetModel.created_at < cursor_ts)
        async with session_scope(self._session_factory) as session:
            models = list((await session.scalars(statement)).all())
        has_more = len(models) > limit
        if has_more:
            models = models[:limit]
        next_cursor = _encode_cursor(models[-1].created_at) if has_more and models else None
        return [_to_dataset(m) for m in models], next_cursor

    async def add(self, dataset: Dataset) -> None:
        async with transaction_scope(self._session_factory) as session:
            session.add(
                DatasetModel(
                    id=dataset.dataset_id.value,
                    project_id=dataset.project_id.value,
                    name=dataset.name,
                    description=dataset.description,
                    created_at=dataset.created_at,
                    updated_at=dataset.updated_at,
                    created_by=dataset.created_by.value,
                    updated_by=dataset.updated_by.value,
                )
            )

    async def save(self, dataset: Dataset) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                update(DatasetModel)
                .where(DatasetModel.id == dataset.dataset_id.value)
                .values(
                    name=dataset.name,
                    description=dataset.description,
                    updated_at=dataset.updated_at,
                    updated_by=dataset.updated_by.value,
                )
            )

    async def delete(self, dataset_id: DatasetId) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                delete(DatasetModel).where(DatasetModel.id == dataset_id.value)
            )


class SqlAlchemyDatasetVersionRepository:
    """数据集版本的 SQLAlchemy 仓库实现。"""
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, version_id: DatasetVersionId) -> DatasetVersion | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(DatasetVersionModel, version_id.value)
        return _to_version(model) if model else None

    async def list_by_dataset(self, dataset_id: DatasetId) -> list[DatasetVersion]:
        statement = (
            select(DatasetVersionModel)
            .where(DatasetVersionModel.dataset_id == dataset_id.value)
            .order_by(DatasetVersionModel.version_number.desc())
        )
        async with session_scope(self._session_factory) as session:
            models = list((await session.scalars(statement)).all())
        return [_to_version(m) for m in models]

    async def get_next_version_number(self, dataset_id: DatasetId) -> int:
        statement = select(func.max(DatasetVersionModel.version_number)).where(
            DatasetVersionModel.dataset_id == dataset_id.value
        )
        async with session_scope(self._session_factory) as session:
            result = await session.scalar(statement)
        return (result or 0) + 1

    async def add(self, version: DatasetVersion) -> None:
        async with transaction_scope(self._session_factory) as session:
            session.add(
                DatasetVersionModel(
                    id=version.version_id.value,
                    dataset_id=version.dataset_id.value,
                    version_number=version.version_number,
                    status=version.status.value,
                    published_at=version.published_at,
                    created_at=version.created_at,
                    updated_at=version.updated_at,
                    created_by=version.created_by.value,
                )
            )

    async def save(self, version: DatasetVersion) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                update(DatasetVersionModel)
                .where(DatasetVersionModel.id == version.version_id.value)
                .values(
                    status=version.status.value,
                    published_at=version.published_at,
                    updated_at=version.updated_at,
                )
            )


class SqlAlchemyTestCaseRepository:
    """测试用例的 SQLAlchemy 仓库实现。"""
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, case_id: TestCaseId) -> TestCase | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(TestCaseModel, case_id.value)
        return _to_test_case(model) if model else None

    async def list_by_version(
        self,
        dataset_version_id: DatasetVersionId,
        *,
        limit: int = 200,
        cursor: str | None = None,
    ) -> tuple[list[TestCase], str | None]:
        statement = (
            select(TestCaseModel)
            .where(TestCaseModel.dataset_version_id == dataset_version_id.value)
            .order_by(TestCaseModel.sort_order.asc())
            .limit(limit + 1)
        )
        if cursor is not None:
            cursor_order = int(cursor)
            statement = statement.where(TestCaseModel.sort_order > cursor_order)
        async with session_scope(self._session_factory) as session:
            models = list((await session.scalars(statement)).all())
        has_more = len(models) > limit
        if has_more:
            models = models[:limit]
        next_cursor = str(models[-1].sort_order) if has_more and models else None
        return [_to_test_case(m) for m in models], next_cursor

    async def add(self, case: TestCase) -> None:
        async with transaction_scope(self._session_factory) as session:
            session.add(
                TestCaseModel(
                    id=case.case_id.value,
                    dataset_version_id=case.dataset_version_id.value,
                    name=case.name,
                    input=case.input,
                    execution_mode=case.execution_mode.value,
                    initial_state=case.initial_state,
                    expected_outcome=case.expected_outcome,
                    assertions=case.assertions,
                    scorers=case.scorers,
                    security_policies=case.security_policies,
                    tags=case.tags,
                    scenario=case.scenario,
                    priority=case.priority.value if case.priority else None,
                    risk_level=case.risk_level.value if case.risk_level else None,
                    difficulty=case.difficulty,
                    test_group=case.test_group.value if case.test_group else None,
                    sort_order=case.sort_order,
                    created_at=case.created_at,
                    updated_at=case.updated_at,
                )
            )

    async def save(self, case: TestCase) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                update(TestCaseModel)
                .where(TestCaseModel.id == case.case_id.value)
                .values(
                    name=case.name,
                    input=case.input,
                    execution_mode=case.execution_mode.value,
                    initial_state=case.initial_state,
                    expected_outcome=case.expected_outcome,
                    assertions=case.assertions,
                    scorers=case.scorers,
                    security_policies=case.security_policies,
                    tags=case.tags,
                    scenario=case.scenario,
                    priority=case.priority.value if case.priority else None,
                    risk_level=case.risk_level.value if case.risk_level else None,
                    difficulty=case.difficulty,
                    test_group=case.test_group.value if case.test_group else None,
                    sort_order=case.sort_order,
                    updated_at=case.updated_at,
                )
            )

    async def delete(self, case_id: TestCaseId) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                delete(TestCaseModel).where(TestCaseModel.id == case_id.value)
            )

    async def get_max_sort_order(self, dataset_version_id: DatasetVersionId) -> int:
        statement = select(func.max(TestCaseModel.sort_order)).where(
            TestCaseModel.dataset_version_id == dataset_version_id.value
        )
        async with session_scope(self._session_factory) as session:
            result = await session.scalar(statement)
        return result or 0

    async def count_by_version(self, dataset_version_id: DatasetVersionId) -> int:
        statement = select(func.count()).where(
            TestCaseModel.dataset_version_id == dataset_version_id.value
        )
        async with session_scope(self._session_factory) as session:
            result = await session.scalar(statement)
        return result or 0


# ── Mappers ─────────────────────────────────────────────────────────────────


def _to_dataset(model: DatasetModel) -> Dataset:
    """ORM 模型 → 领域实体映射。"""
    return Dataset(
        dataset_id=DatasetId(model.id),
        project_id=ProjectId(model.project_id),
        name=model.name,
        created_by=UserId(model.created_by),
        updated_by=UserId(model.updated_by),
        created_at=model.created_at,
        updated_at=model.updated_at,
        description=model.description,
    )


def _to_version(model: DatasetVersionModel) -> DatasetVersion:
    """ORM 模型 → 领域实体映射。"""
    return DatasetVersion(
        version_id=DatasetVersionId(model.id),
        dataset_id=DatasetId(model.dataset_id),
        version_number=model.version_number,
        status=VersionStatus(model.status),
        created_by=UserId(model.created_by),
        created_at=model.created_at,
        updated_at=model.updated_at,
        published_at=model.published_at,
    )


def _to_test_case(model: TestCaseModel) -> TestCase:
    """ORM 模型 → 领域实体映射。"""
    return TestCase(
        case_id=TestCaseId(model.id),
        dataset_version_id=DatasetVersionId(model.dataset_version_id),
        name=model.name,
        input=model.input,
        execution_mode=ExecutionMode(model.execution_mode),
        assertions=model.assertions,
        scorers=model.scorers,
        initial_state=model.initial_state,
        expected_outcome=model.expected_outcome,
        security_policies=model.security_policies,
        tags=model.tags,
        scenario=model.scenario,
        priority=Priority(model.priority) if model.priority else None,
        risk_level=RiskLevel(model.risk_level) if model.risk_level else None,
        difficulty=model.difficulty,
        test_group=TestGroup(model.test_group) if model.test_group else None,
        sort_order=model.sort_order or 0,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


# ── Cursor helpers ──────────────────────────────────────────────────────────


def _encode_cursor(ts: datetime) -> str:
    return b64encode(ts.isoformat().encode()).decode()


def _decode_cursor(cursor: str) -> datetime:
    return datetime.fromisoformat(b64decode(cursor.encode()).decode())
