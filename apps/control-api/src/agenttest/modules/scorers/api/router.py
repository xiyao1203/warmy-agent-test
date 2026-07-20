"""Scorer HTTP adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.modules.scorers.application.service import (
    PublishedVersion,
    ScorerNotFound,
    ScorerRuntimeUnavailable,
    ScorerService,
    ScorerValidationError,
)
from agenttest.modules.scorers.domain.entities import Scorer
from agenttest.shared.api.auth_guard import require_actor, require_writer
from agenttest.shared.api.pagination import resolve_page_request
from agenttest.shared.application.core_summaries import CoreSummaryReader, ScorerSummaryMetrics


class CreateScorerRequest(BaseModel):
    name: str
    scorer_type: str
    weight: float = 1.0
    threshold: float = 0.8
    config_json: dict[str, object] = Field(default_factory=dict)
    description: str | None = None


class UpdateScorerRequest(BaseModel):
    name: str | None = None
    weight: float | None = None
    threshold: float | None = None
    config_json: dict[str, object] | None = None
    description: str | None = None
    enabled: bool | None = None


class TrialScorerRequest(BaseModel):
    output: object
    input: object | None = None
    reference: object | None = None


class ScorerSummaryResponse(ScorerSummaryMetrics):
    id: UUID
    project_id: UUID
    name: str
    scorer_type: str
    weight: float
    threshold: float
    config_json: dict[str, object]
    description: str | None
    enabled: bool
    latest_published_version_id: UUID | None
    latest_published_version_number: int | None
    created_at: datetime
    updated_at: datetime


class ScorerListResponse(BaseModel):
    items: list[ScorerSummaryResponse]
    total: int
    page: int | None = None
    page_size: int = 50
    total_pages: int = 0


class ActorResolver(Protocol):
    async def __call__(self, request: Request) -> User | None: ...


@dataclass(frozen=True, slots=True)
class ScorerApiDependencies:
    service: ScorerService
    actor_for: ActorResolver
    settings: Settings
    summaries: CoreSummaryReader | None = None


def create_scorer_router(dependencies: ScorerApiDependencies) -> APIRouter:
    router = APIRouter(prefix="/projects/{project_id}/scorers", tags=["scorers"])

    @router.get("", response_model=ScorerListResponse)
    async def list_scorers(
        request: Request,
        project_id: UUID,
        limit: int = 50,
        offset: int = 0,
        page: int | None = Query(default=None),
        page_size: int | None = Query(default=None),
    ):
        actor = await require_actor(request, dependencies.actor_for, dependencies.settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            page_request = resolve_page_request(page=page, page_size=page_size)
            result = await dependencies.service.list(
                actor,
                project_id,
                limit=page_request.page_size if page_request else limit,
                offset=page_request.offset if page_request else offset,
            )
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        summaries = (
            await dependencies.summaries.scorers(
                project_id,
                [item.scorer.scorer_id.value for item in result.items],
            )
            if dependencies.summaries
            else {}
        )
        return {
            "items": [
                {
                    **_scorer_to_dict(item.scorer, item.published_version),
                    **summaries[item.scorer.scorer_id.value].model_dump(),
                }
                if item.scorer.scorer_id.value in summaries
                else _scorer_to_dict(item.scorer, item.published_version)
                for item in result.items
            ],
            "total": result.total,
            "page": page_request.page if page_request else None,
            "page_size": page_request.page_size if page_request else limit,
            "total_pages": (
                (result.total + (page_request.page_size if page_request else limit) - 1)
                // (page_request.page_size if page_request else limit)
                if result.total
                else 0
            ),
        }

    @router.post("")
    async def create_scorer(
        request: Request,
        project_id: UUID,
        body: CreateScorerRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            item = await dependencies.service.create(
                actor,
                project_id,
                name=body.name,
                scorer_type=body.scorer_type,
                weight=body.weight,
                threshold=body.threshold,
                config_json=body.config_json,
                description=body.description,
            )
        except ScorerValidationError as error:
            return JSONResponse(status_code=422, content={"detail": str(error)})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        return _scorer_to_dict(item.scorer, item.published_version)

    @router.get("/{scorer_id}")
    async def get_scorer(request: Request, project_id: UUID, scorer_id: UUID):
        actor = await require_actor(request, dependencies.actor_for, dependencies.settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            scorer = await dependencies.service.get(actor, project_id, scorer_id)
        except ScorerNotFound:
            return JSONResponse(status_code=404, content={"detail": "评分器不存在"})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        return _scorer_to_dict(scorer)

    @router.patch("/{scorer_id}")
    async def update_scorer(
        request: Request,
        project_id: UUID,
        scorer_id: UUID,
        body: UpdateScorerRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            item = await dependencies.service.update(
                actor,
                project_id,
                scorer_id,
                name=body.name,
                weight=body.weight,
                threshold=body.threshold,
                config_json=body.config_json,
                description=body.description,
                enabled=body.enabled,
            )
        except ScorerNotFound:
            return JSONResponse(status_code=404, content={"detail": "评分器不存在"})
        except ScorerValidationError as error:
            return JSONResponse(status_code=422, content={"detail": str(error)})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        return _scorer_to_dict(item.scorer, item.published_version)

    @router.delete("/{scorer_id}")
    async def delete_scorer(
        request: Request,
        project_id: UUID,
        scorer_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await dependencies.service.delete(actor, project_id, scorer_id)
        except ScorerNotFound:
            return JSONResponse(status_code=404, content={"detail": "评分器不存在"})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        return {"status": "deleted", "scorer_id": str(scorer_id)}

    @router.post("/{scorer_id}/trial")
    async def trial_scorer(
        request: Request,
        project_id: UUID,
        scorer_id: UUID,
        body: TrialScorerRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            return await dependencies.service.trial(
                actor,
                project_id,
                scorer_id,
                output=body.output,
                input_value=body.input,
                reference=body.reference,
            )
        except ScorerNotFound:
            return JSONResponse(status_code=404, content={"detail": "评分器不存在"})
        except ScorerRuntimeUnavailable:
            return JSONResponse(status_code=503, content={"detail": "模型评分运行时不可用"})
        except ScorerValidationError as error:
            return JSONResponse(status_code=422, content={"detail": str(error)})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise

    return router


def _access_error(error: Exception) -> JSONResponse | None:
    if isinstance(error, InvalidSessionError):
        return JSONResponse(status_code=401, content={"detail": "认证失败"})
    if isinstance(error, PermissionError):
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})
    if isinstance(error, ProjectNotFoundError):
        return JSONResponse(status_code=404, content={"detail": "项目不存在"})
    return None


def _scorer_to_dict(
    scorer: Scorer, published_version: PublishedVersion | None = None
) -> dict[str, object]:
    version_id, version_number = published_version or (None, None)
    return {
        "id": str(scorer.scorer_id.value),
        "project_id": str(scorer.project_id.value),
        "name": scorer.name,
        "scorer_type": scorer.scorer_type.value,
        "weight": scorer.weight,
        "threshold": scorer.threshold,
        "config_json": scorer.config_json,
        "description": scorer.description,
        "enabled": scorer.enabled,
        "latest_published_version_id": str(version_id) if version_id else None,
        "latest_published_version_number": version_number,
        "created_at": scorer.created_at.isoformat(),
        "updated_at": scorer.updated_at.isoformat(),
    }
