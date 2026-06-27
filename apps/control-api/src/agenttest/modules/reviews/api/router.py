"""Review API 路由。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.reviews.domain.entities import ReviewTaskId
from agenttest.modules.reviews.infrastructure.persistence.repositories import (
    SqlAlchemyReviewTaskRepository,
)


class ScoreReviewRequest(BaseModel):
    score: float
    opinion: str | None = None
    rubric_scores: dict[str, float] | None = None


class AutoEnqueueRequest(BaseModel):
    run_id: str
    confidence_threshold: float = 0.5


def create_review_router(
    *, session_factory, actor_for, check_project,
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/reviews",
        tags=["reviews"],
    )

    @router.get("")
    async def list_reviews(
        request: Request,
        project_id: UUID,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ):
        try:
            await check_project(project_id)
        except (ProjectNotFoundError, InvalidSessionError):
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        async with session_factory() as session:
            repo = SqlAlchemyReviewTaskRepository(session)
            tasks, total = await repo.list_by_project(
                ProjectId(project_id), status=status, limit=limit, offset=offset,
            )
            return {
                "items": [_to_dict(t) for t in tasks],
                "total": total,
            }

    @router.post("/auto-enqueue")
    async def auto_enqueue(
        request: Request,
        project_id: UUID,
        body: AutoEnqueueRequest,
    ):
        """将低置信度用例自动入队。"""
        try:
            await check_project(project_id)
        except (ProjectNotFoundError, InvalidSessionError):
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        async with session_factory() as session:
            repo = SqlAlchemyReviewTaskRepository(session)
            created = await repo.auto_enqueue_low_confidence(
                ProjectId(project_id), body.run_id, body.confidence_threshold,
            )
            await session.commit()
            return {
                "enqueued": len(created),
                "tasks": [_to_dict(t) for t in created],
            }

    @router.post("/{task_id}/score")
    async def score_review(
        request: Request,
        project_id: UUID,
        task_id: UUID,
        body: ScoreReviewRequest,
    ):
        """人工评分。"""
        async with session_factory() as session:
            repo = SqlAlchemyReviewTaskRepository(session)
            task = await repo.get_by_id_and_project(
                ReviewTaskId(task_id), ProjectId(project_id),
            )
            if task is None:
                return JSONResponse(status_code=404, content={"detail": "审核任务不存在"})
            if task.status.value != "pending":
                return JSONResponse(status_code=422, content={"detail": "该任务已审核"})
            try:
                # 使用当前用户的 session cookie 中的 user_id 作为 reviewer_id
                # 简化处理：使用 task_id 的前 16 字节模拟
                reviewer_id = UUID(int=0)  # placeholder
                task.approve(
                    reviewer_id,
                    score=body.score,
                    opinion=body.opinion,
                    rubric_scores=body.rubric_scores,
                )
            except ValueError as e:
                return JSONResponse(status_code=422, content={"detail": str(e)})
            await repo.save(task)
            await session.commit()
            return _to_dict(task)

    @router.post("/{task_id}/reject")
    async def reject_review(
        request: Request,
        project_id: UUID,
        task_id: UUID,
        opinion: str | None = None,
    ):
        """拒绝审核。"""
        async with session_factory() as session:
            repo = SqlAlchemyReviewTaskRepository(session)
            task = await repo.get_by_id_and_project(
                ReviewTaskId(task_id), ProjectId(project_id),
            )
            if task is None:
                return JSONResponse(status_code=404, content={"detail": "审核任务不存在"})
            if task.status.value != "pending":
                return JSONResponse(status_code=422, content={"detail": "该任务已审核"})
            reviewer_id = UUID(int=0)  # placeholder
            task.reject(reviewer_id, opinion=opinion)
            await repo.save(task)
            await session.commit()
            return _to_dict(task)

    @router.post("/{task_id}/skip")
    async def skip_review(
        request: Request,
        project_id: UUID,
        task_id: UUID,
    ):
        """跳过审核。"""
        async with session_factory() as session:
            repo = SqlAlchemyReviewTaskRepository(session)
            task = await repo.get_by_id_and_project(
                ReviewTaskId(task_id), ProjectId(project_id),
            )
            if task is None:
                return JSONResponse(status_code=404, content={"detail": "审核任务不存在"})
            try:
                task.skip()
            except ValueError as e:
                return JSONResponse(status_code=422, content={"detail": str(e)})
            await repo.save(task)
            await session.commit()
            return _to_dict(task)

    @router.get("/stats")
    async def review_stats(
        request: Request,
        project_id: UUID,
    ):
        """审核一致性统计。"""
        try:
            await check_project(project_id)
        except (ProjectNotFoundError, InvalidSessionError):
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        async with session_factory() as session:
            repo = SqlAlchemyReviewTaskRepository(session)
            stats = await repo.get_stats(ProjectId(project_id))
            return stats

    return router


def _to_dict(t) -> dict:
    return {
        "id": str(t.task_id.value),
        "project_id": str(t.project_id.value),
        "run_case_id": str(t.run_case_id),
        "status": t.status.value,
        "confidence": t.confidence,
        "reviewer_id": str(t.reviewer_id) if t.reviewer_id else None,
        "score": t.score,
        "opinion": t.opinion,
        "rubric_scores": t.rubric_scores,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
        "reviewed_at": t.reviewed_at.isoformat() if t.reviewed_at else None,
    }
