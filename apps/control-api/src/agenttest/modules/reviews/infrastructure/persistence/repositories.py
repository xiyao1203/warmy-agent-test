"""ReviewTask 仓库 SQLAlchemy 实现。"""

from __future__ import annotations

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.projects.public import ProjectId
from agenttest.modules.reviews.domain.entities import (
    ReviewStatus,
    ReviewTask,
    ReviewTaskId,
)
from agenttest.modules.reviews.infrastructure.persistence.models import (
    ReviewTaskModel,
)
from agenttest.shared.infrastructure.database import session_scope, transaction_scope


class SqlAlchemyReviewTaskRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, task_id: ReviewTaskId) -> ReviewTask | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(ReviewTaskModel, task_id.value)
        return _to_entity(model) if model else None

    async def get_by_id_and_project(
        self, task_id: ReviewTaskId, project_id: ProjectId,
    ) -> ReviewTask | None:
        async with session_scope(self._session_factory) as session:
            model = await session.get(ReviewTaskModel, task_id.value)
            if model and model.project_id != project_id.value:
                return None
            return _to_entity(model) if model else None

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ReviewTask], int]:
        base = ReviewTaskModel.project_id == project_id.value
        if status:
            base = base & (ReviewTaskModel.status == status)

        async with session_scope(self._session_factory) as session:
            count_stmt = select(func.count()).select_from(ReviewTaskModel).where(base)
            total = (await session.execute(count_stmt)).scalar() or 0

            stmt = (
                select(ReviewTaskModel)
                .where(base)
                .order_by(ReviewTaskModel.created_at.asc())
                .limit(limit)
                .offset(offset)
            )
            models = list((await session.scalars(stmt)).all())
        return [_to_entity(m) for m in models], total

    async def add(self, task: ReviewTask) -> None:
        async with transaction_scope(self._session_factory) as session:
            session.add(_to_model(task))

    async def save(self, task: ReviewTask) -> None:
        async with transaction_scope(self._session_factory) as session:
            model = await session.get(ReviewTaskModel, task.task_id.value)
            if model:
                model.status = task.status.value
                model.reviewer_id = task.reviewer_id
                model.score = task.score
                model.opinion = task.opinion
                model.rubric_scores = task.rubric_scores
                model.reviewed_at = task.reviewed_at
                model.updated_at = task.updated_at

    async def auto_enqueue_low_confidence(
        self, project_id: ProjectId, run_id: str, confidence_threshold: float,
    ) -> list[ReviewTask]:
        """将低置信度用例自动入队。"""
        async with session_scope(self._session_factory) as session:
            # 查找低置信度用例（从 run_cases 的 trace 中提取 confidence）
            result = await session.execute(
                text(
                    "SELECT rc.id FROM run_cases rc "
                    "JOIN runs r ON rc.run_id = r.id "
                    "WHERE r.project_id = :pid AND r.id = :rid "
                    "AND rc.status IN ('passed', 'failed') "
                    "AND NOT EXISTS ("
                    "  SELECT 1 FROM review_tasks rt WHERE rt.run_case_id = rc.id"
                    ")"
                ),
                {"pid": project_id.value, "rid": run_id},
            )
            case_ids = [row[0] for row in result.all()]

            created: list[ReviewTask] = []
            for case_id in case_ids:
                task = ReviewTask.create(
                    task_id=ReviewTaskId.new(),
                    project_id=project_id,
                    run_case_id=case_id,
                    confidence=confidence_threshold,
                )
                session.add(_to_model(task))
                created.append(task)

            return created

    async def get_stats(self, project_id: ProjectId) -> dict[str, int]:
        """审核一致性统计。"""
        async with session_scope(self._session_factory) as session:
            stmt = (
                select(ReviewTaskModel.status, func.count())
                .where(ReviewTaskModel.project_id == project_id.value)
                .group_by(ReviewTaskModel.status)
            )
            rows = (await session.execute(stmt)).all()
            return {row[0]: row[1] for row in rows}


def _to_model(t: ReviewTask) -> ReviewTaskModel:
    return ReviewTaskModel(
        id=t.task_id.value,
        project_id=t.project_id.value,
        run_case_id=t.run_case_id,
        status=t.status.value,
        confidence=t.confidence,
        reviewer_id=t.reviewer_id,
        score=t.score,
        opinion=t.opinion,
        rubric_scores=t.rubric_scores,
        created_at=t.created_at,
        updated_at=t.updated_at,
        reviewed_at=t.reviewed_at,
    )


def _to_entity(m: ReviewTaskModel) -> ReviewTask:
    return ReviewTask(
        task_id=ReviewTaskId(m.id),
        project_id=ProjectId(m.project_id),
        run_case_id=m.run_case_id,
        status=ReviewStatus(m.status),
        confidence=m.confidence,
        reviewer_id=m.reviewer_id,
        score=m.score,
        opinion=m.opinion,
        rubric_scores=m.rubric_scores,
        created_at=m.created_at,
        updated_at=m.updated_at,
        reviewed_at=m.reviewed_at,
    )
