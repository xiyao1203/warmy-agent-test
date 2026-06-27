"""Review API 路由。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.reviews.domain.entities import ReviewTaskId
from agenttest.modules.reviews.infrastructure.persistence.repositories import (
    SqlAlchemyReviewTaskRepository,
)
from agenttest.shared.api.auth_guard import require_actor, require_writer


class ScoreReviewRequest(BaseModel):
    score: float
    opinion: str | None = None
    rubric_scores: dict[str, float] | None = None


class AutoEnqueueRequest(BaseModel):
    run_id: str
    confidence_threshold: float = 0.5


def create_review_router(
    *, session_factory, actor_for, check_project, settings,
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/reviews",
        tags=["reviews"],
    )

    repo = SqlAlchemyReviewTaskRepository(session_factory)

    # 固定路径放在参数化路径之前

    @router.get("")
    async def list_reviews(
        request: Request,
        project_id: UUID,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ):
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except (ProjectNotFoundError, Exception):
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        tasks, total = await repo.list_by_project(
            ProjectId(project_id), status=status, limit=limit, offset=offset,
        )
        return {
            "items": [_to_dict(t) for t in tasks],
            "total": total,
        }

    @router.get("/stats")
    async def review_stats(
        request: Request,
        project_id: UUID,
    ):
        """审核一致性统计。"""
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except (ProjectNotFoundError, Exception):
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        stats = await repo.get_stats(ProjectId(project_id))
        return stats

    @router.post("/auto-enqueue")
    async def auto_enqueue(
        request: Request,
        project_id: UUID,
        body: AutoEnqueueRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        """将低置信度用例自动入队。"""
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except (ProjectNotFoundError, Exception):
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        created = await repo.auto_enqueue_low_confidence(
            ProjectId(project_id), body.run_id, body.confidence_threshold,
        )
        return {
            "enqueued": len(created),
            "tasks": [_to_dict(t) for t in created],
        }

    # 参数化路径

    @router.post("/{task_id}/score")
    async def score_review(
        request: Request,
        project_id: UUID,
        task_id: UUID,
        body: ScoreReviewRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        """人工评分。"""
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        task = await repo.get_by_id_and_project(
            ReviewTaskId(task_id), ProjectId(project_id),
        )
        if task is None:
            return JSONResponse(status_code=404, content={"detail": "审核任务不存在"})
        if task.status.value != "pending":
            return JSONResponse(status_code=422, content={"detail": "该任务已审核"})
        try:
            task.approve(
                actor.user_id.value,
                score=body.score,
                opinion=body.opinion,
                rubric_scores=body.rubric_scores,
            )
        except ValueError as e:
            return JSONResponse(status_code=422, content={"detail": str(e)})
        await repo.save(task)
        return _to_dict(task)

    @router.post("/{task_id}/reject")
    async def reject_review(
        request: Request,
        project_id: UUID,
        task_id: UUID,
        opinion: str | None = None,
        x_csrf_token: str | None = Header(default=None),
    ):
        """拒绝审核。"""
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        task = await repo.get_by_id_and_project(
            ReviewTaskId(task_id), ProjectId(project_id),
        )
        if task is None:
            return JSONResponse(status_code=404, content={"detail": "审核任务不存在"})
        if task.status.value != "pending":
            return JSONResponse(status_code=422, content={"detail": "该任务已审核"})
        task.reject(actor.user_id.value, opinion=opinion)
        await repo.save(task)
        return _to_dict(task)

    @router.post("/{task_id}/skip")
    async def skip_review(
        request: Request,
        project_id: UUID,
        task_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        """跳过审核。"""
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
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
        return _to_dict(task)

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
