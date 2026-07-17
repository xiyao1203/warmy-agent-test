from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.modules.reviews.application.service import (
    ReviewService,
    ReviewTaskAlreadyReviewed,
    ReviewTaskNotFound,
    ReviewValidationError,
)
from agenttest.modules.reviews.domain.entities import ReviewTask
from agenttest.shared.api.auth_guard import require_actor, require_writer
from agenttest.shared.application.core_summaries import CoreSummaryReader, ReviewSummaryMetrics


class ScoreReviewRequest(BaseModel):
    score: float
    opinion: str | None = None
    rubric_scores: dict[str, float] | None = None


class AutoEnqueueRequest(BaseModel):
    run_id: str
    confidence_threshold: float = 0.5


class ReviewSummaryResponse(ReviewSummaryMetrics):
    id: UUID
    project_id: UUID
    run_case_id: UUID
    status: str
    confidence: float
    reviewer_id: UUID | None
    score: float | None
    opinion: str | None
    rubric_scores: dict[str, float] | None
    created_at: datetime
    updated_at: datetime
    reviewed_at: datetime | None


class ReviewListResponse(BaseModel):
    items: list[ReviewSummaryResponse]
    total: int


class ActorResolver(Protocol):
    async def __call__(self, request: Request) -> User | None: ...


@dataclass(frozen=True, slots=True)
class ReviewApiDependencies:
    service: ReviewService
    actor_for: ActorResolver
    settings: Settings
    summaries: CoreSummaryReader | None = None


def create_review_router(dependencies: ReviewApiDependencies) -> APIRouter:
    router = APIRouter(prefix="/projects/{project_id}/reviews", tags=["reviews"])

    async def reader(request: Request) -> User | JSONResponse:
        return await require_actor(request, dependencies.actor_for, dependencies.settings)

    async def writer(
        request: Request,
        csrf_header: str | None,
    ) -> User | JSONResponse:
        return await require_writer(
            request,
            dependencies.actor_for,
            dependencies.settings,
            csrf_header,
        )

    @router.get("", response_model=ReviewListResponse)
    async def list_reviews(
        request: Request,
        project_id: UUID,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ):
        actor = await reader(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            tasks, total = await dependencies.service.list_reviews(
                actor,
                project_id,
                status=status,
                limit=limit,
                offset=offset,
            )
        except (ProjectNotFoundError, PermissionError) as error:
            return _access_error(error)
        summaries = (
            await dependencies.summaries.reviews(
                project_id,
                [task.task_id.value for task in tasks],
            )
            if dependencies.summaries
            else {}
        )
        return {
            "items": [
                {**_to_dict(task), **summaries[task.task_id.value].model_dump()}
                if task.task_id.value in summaries
                else _to_dict(task)
                for task in tasks
            ],
            "total": total,
        }

    @router.get("/stats")
    async def review_stats(request: Request, project_id: UUID):
        """审核一致性统计。"""
        actor = await reader(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            return await dependencies.service.stats(actor, project_id)
        except (ProjectNotFoundError, PermissionError) as error:
            return _access_error(error)

    @router.post("/auto-enqueue")
    async def auto_enqueue(
        request: Request,
        project_id: UUID,
        body: AutoEnqueueRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        """将低置信度用例自动入队。"""
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            tasks = await dependencies.service.auto_enqueue(
                actor,
                project_id,
                body.run_id,
                body.confidence_threshold,
            )
        except (ProjectNotFoundError, PermissionError) as error:
            return _access_error(error)
        return {"enqueued": len(tasks), "tasks": [_to_dict(task) for task in tasks]}

    @router.post("/{task_id}/score")
    async def score_review(
        request: Request,
        project_id: UUID,
        task_id: UUID,
        body: ScoreReviewRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        """人工评分。"""
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            task = await dependencies.service.score(
                actor,
                project_id,
                task_id,
                score=body.score,
                opinion=body.opinion,
                rubric_scores=body.rubric_scores,
            )
        except Exception as error:
            response = _service_error(error)
            if response is not None:
                return response
            raise
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
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            task = await dependencies.service.reject(actor, project_id, task_id, opinion)
        except Exception as error:
            response = _service_error(error)
            if response is not None:
                return response
            raise
        return _to_dict(task)

    @router.post("/{task_id}/skip")
    async def skip_review(
        request: Request,
        project_id: UUID,
        task_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        """跳过审核。"""
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            task = await dependencies.service.skip(actor, project_id, task_id)
        except Exception as error:
            response = _service_error(error)
            if response is not None:
                return response
            raise
        return _to_dict(task)

    return router


def _access_error(error: Exception) -> JSONResponse:
    if isinstance(error, PermissionError):
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})
    return JSONResponse(status_code=404, content={"detail": "项目不存在"})


def _service_error(error: Exception) -> JSONResponse | None:
    if isinstance(error, (ProjectNotFoundError, PermissionError)):
        return _access_error(error)
    if isinstance(error, ReviewTaskNotFound):
        return JSONResponse(status_code=404, content={"detail": "审核任务不存在"})
    if isinstance(error, ReviewTaskAlreadyReviewed):
        return JSONResponse(status_code=422, content={"detail": "该任务已审核"})
    if isinstance(error, ReviewValidationError):
        return JSONResponse(status_code=422, content={"detail": str(error)})
    return None


def _to_dict(task: ReviewTask) -> dict[str, object]:
    return {
        "id": str(task.task_id.value),
        "project_id": str(task.project_id.value),
        "run_case_id": str(task.run_case_id),
        "status": task.status.value,
        "confidence": task.confidence,
        "reviewer_id": str(task.reviewer_id) if task.reviewer_id else None,
        "score": task.score,
        "opinion": task.opinion,
        "rubric_scores": task.rubric_scores,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "reviewed_at": task.reviewed_at.isoformat() if task.reviewed_at else None,
    }
