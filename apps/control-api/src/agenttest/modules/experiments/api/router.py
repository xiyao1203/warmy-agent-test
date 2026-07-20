from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agenttest.bootstrap.settings import Settings
from agenttest.modules.experiments.application.service import (
    ExperimentNotFound,
    ExperimentService,
    ExperimentValidationError,
)
from agenttest.modules.experiments.domain.entities import Experiment
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.shared.api.auth_guard import require_actor, require_writer
from agenttest.shared.api.pagination import resolve_page_request
from agenttest.shared.application.core_summaries import CoreSummaryReader, ExperimentSummaryMetrics
from agenttest.shared.application.pagination import paginate_items


class CreateExperimentRequest(BaseModel):
    name: str
    run_a_id: UUID
    run_b_id: UUID
    description: str | None = None


class ExperimentSummaryResponse(ExperimentSummaryMetrics):
    id: UUID
    project_id: UUID
    name: str
    run_a_id: UUID
    run_b_id: UUID
    status: str
    result_json: dict[str, object]
    description: str | None
    created_at: datetime
    updated_at: datetime


class ExperimentListResponse(BaseModel):
    items: list[ExperimentSummaryResponse]
    total: int
    page: int | None = None
    page_size: int = 50
    total_pages: int = 0


class ActorResolver(Protocol):
    async def __call__(self, request: Request) -> User | None: ...


@dataclass(frozen=True, slots=True)
class ExperimentApiDependencies:
    service: ExperimentService
    actor_for: ActorResolver
    settings: Settings
    summaries: CoreSummaryReader | None = None


def create_experiment_router(dependencies: ExperimentApiDependencies) -> APIRouter:
    router = APIRouter(prefix="/projects/{project_id}/experiments", tags=["experiments"])

    @router.get("", response_model=ExperimentListResponse)
    async def list_experiments(
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
            if page_request:
                all_items = await dependencies.service.list(actor, project_id, 10_000, 0)
                result = paginate_items(all_items, page_request)
                items = result.items
                total = result.total
                response_page = result.page
                response_page_size = result.page_size
                total_pages = result.total_pages
            else:
                items = await dependencies.service.list(actor, project_id, limit, offset)
                total = len(items)
                response_page = None
                response_page_size = limit
                total_pages = (total + limit - 1) // limit if total else 0
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        summaries = (
            await dependencies.summaries.experiments(
                project_id,
                [item.experiment_id.value for item in items],
            )
            if dependencies.summaries
            else {}
        )
        return {
            "items": [
                {
                    **_to_dict(item),
                    **summaries[item.experiment_id.value].model_dump(),
                }
                if item.experiment_id.value in summaries
                else _to_dict(item)
                for item in items
            ],
            "total": total,
            "page": response_page,
            "page_size": response_page_size,
            "total_pages": total_pages,
        }

    @router.post("")
    async def create_experiment(
        request: Request,
        project_id: UUID,
        body: CreateExperimentRequest,
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
                run_a_id=body.run_a_id,
                run_b_id=body.run_b_id,
                description=body.description,
            )
        except ExperimentValidationError as error:
            return JSONResponse(status_code=422, content={"detail": str(error)})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        return _to_dict(item)

    @router.get("/statistics")
    async def get_statistics(
        request: Request,
        project_id: UUID,
        run_id: UUID | None = None,
        experiment_id: UUID | None = None,
    ):
        """获取运行统计或实验对比统计。"""
        actor = await require_actor(request, dependencies.actor_for, dependencies.settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            result = await dependencies.service.statistics(
                actor,
                project_id,
                run_id=run_id,
                experiment_id=experiment_id,
            )
        except ExperimentNotFound:
            return JSONResponse(status_code=404, content={"detail": "实验不存在"})
        except ExperimentValidationError as error:
            return JSONResponse(status_code=422, content={"detail": str(error)})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        return result.payload

    @router.get("/{experiment_id}")
    async def get_experiment(request: Request, project_id: UUID, experiment_id: UUID):
        actor = await require_actor(request, dependencies.actor_for, dependencies.settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            return _to_dict(await dependencies.service.get(actor, project_id, experiment_id))
        except ExperimentNotFound:
            return JSONResponse(status_code=404, content={"detail": "实验不存在"})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise

    @router.post("/{experiment_id}/run")
    async def run_experiment(
        request: Request,
        project_id: UUID,
        experiment_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        """执行对比实验：逐用例对比 + 统计。"""
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            return _to_dict(await dependencies.service.run(actor, project_id, experiment_id))
        except ExperimentNotFound:
            return JSONResponse(status_code=404, content={"detail": "实验不存在"})
        except ExperimentValidationError as error:
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


def _to_dict(item: Experiment) -> dict[str, object]:
    return {
        "id": str(item.experiment_id.value),
        "project_id": str(item.project_id.value),
        "name": item.name,
        "run_a_id": str(item.run_a_id),
        "run_b_id": str(item.run_b_id),
        "status": item.status.value,
        "result_json": item.result_json,
        "description": item.description,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }
