"""Scorer CRUD API 路由。"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.scorers.domain.entities import Scorer, ScorerId
from agenttest.modules.scorers.domain.value_objects import ScorerType
from agenttest.modules.scorers.infrastructure.persistence.repositories import (
    SqlAlchemyScorerRepository,
)
from agenttest.shared.api.auth_guard import require_actor, require_writer


class CreateScorerRequest(BaseModel):
    name: str
    scorer_type: str
    weight: float = 1.0
    threshold: float = 0.8
    config_json: dict[str, object] = {}
    description: str | None = None


class UpdateScorerRequest(BaseModel):
    name: str | None = None
    weight: float | None = None
    threshold: float | None = None
    config_json: dict[str, object] | None = None
    description: str | None = None
    enabled: bool | None = None


def create_scorer_router(
    *,
    session_factory,
    actor_for,
    check_project,
    settings,
) -> APIRouter:
    """创建评分器 CRUD 路由。"""
    router = APIRouter(
        prefix="/projects/{project_id}/scorers",
        tags=["scorers"],
    )

    repo = SqlAlchemyScorerRepository(session_factory)

    @router.get("")
    async def list_scorers(
        request: Request,
        project_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ):
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})

        scorers, total = await repo.list_by_project(
            ProjectId(project_id),
            limit=limit,
            offset=offset,
        )
        return {
            "items": [_scorer_to_dict(s) for s in scorers],
            "total": total,
        }

    @router.post("")
    async def create_scorer(
        request: Request,
        project_id: UUID,
        body: CreateScorerRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})

        try:
            scorer_type = ScorerType(body.scorer_type)
        except ValueError:
            return JSONResponse(
                status_code=422,
                content={"detail": f"无效的评分器类型: {body.scorer_type}"},
            )

        try:
            scorer = Scorer.create(
                scorer_id=ScorerId.new(),
                project_id=ProjectId(project_id),
                name=body.name,
                scorer_type=scorer_type,
                weight=body.weight,
                threshold=body.threshold,
                config_json=body.config_json,
                description=body.description,
            )
        except ValueError as e:
            return JSONResponse(status_code=422, content={"detail": str(e)})

        await repo.add(scorer)
        return _scorer_to_dict(scorer)

    @router.get("/{scorer_id}")
    async def get_scorer(
        request: Request,
        project_id: UUID,
        scorer_id: UUID,
    ):
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor

        scorer = await repo.get_by_id_and_project(
            ScorerId(scorer_id),
            ProjectId(project_id),
        )
        if scorer is None:
            return JSONResponse(status_code=404, content={"detail": "评分器不存在"})
        return _scorer_to_dict(scorer)

    @router.patch("/{scorer_id}")
    async def update_scorer(
        request: Request,
        project_id: UUID,
        scorer_id: UUID,
        body: UpdateScorerRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor

        scorer = await repo.get_by_id_and_project(
            ScorerId(scorer_id),
            ProjectId(project_id),
        )
        if scorer is None:
            return JSONResponse(status_code=404, content={"detail": "评分器不存在"})

        if body.name is not None:
            try:
                scorer.rename(body.name)
            except ValueError as e:
                return JSONResponse(status_code=422, content={"detail": str(e)})
        if body.weight is not None:
            try:
                scorer.update_weight(body.weight)
            except ValueError as e:
                return JSONResponse(status_code=422, content={"detail": str(e)})
        if body.threshold is not None:
            try:
                scorer.update_threshold(body.threshold)
            except ValueError as e:
                return JSONResponse(status_code=422, content={"detail": str(e)})
        if body.config_json is not None:
            scorer.config_json = body.config_json
            scorer.updated_at = datetime.now(UTC)
        if body.description is not None:
            scorer.description = body.description
            scorer.updated_at = datetime.now(UTC)
        if body.enabled is not None and body.enabled != scorer.enabled:
            scorer.toggle()

        await repo.save(scorer)
        return _scorer_to_dict(scorer)

    @router.delete("/{scorer_id}")
    async def delete_scorer(
        request: Request,
        project_id: UUID,
        scorer_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor

        scorer = await repo.get_by_id_and_project(
            ScorerId(scorer_id),
            ProjectId(project_id),
        )
        if scorer is None:
            return JSONResponse(status_code=404, content={"detail": "评分器不存在"})
        await repo.delete(ScorerId(scorer_id))
        return {"status": "deleted", "scorer_id": str(scorer_id)}

    return router


def _scorer_to_dict(s: Scorer) -> dict[str, object]:
    return {
        "id": str(s.scorer_id.value),
        "project_id": str(s.project_id.value),
        "name": s.name,
        "scorer_type": s.scorer_type.value,
        "weight": s.weight,
        "threshold": s.threshold,
        "config_json": s.config_json,
        "description": s.description,
        "enabled": s.enabled,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }
