from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from agenttest.bootstrap.settings import Settings
from agenttest.modules.environments.application.snapshots import (
    EnvironmentSnapshotNotFound,
    EnvironmentSnapshotService,
    EnvironmentTemplateNotFound,
)
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.shared.api.auth_guard import require_actor, require_writer


class ActorResolver(Protocol):
    async def __call__(self, request: Request) -> User | None: ...


@dataclass(frozen=True, slots=True)
class SnapshotApiDependencies:
    service: EnvironmentSnapshotService
    actor_for: ActorResolver
    settings: Settings


def create_snapshot_router(dependencies: SnapshotApiDependencies) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/environments/{template_id}/snapshots",
        tags=["environment-snapshots"],
    )

    @router.post("")
    async def create_snapshot(
        request: Request,
        project_id: UUID,
        template_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            snapshot = await dependencies.service.create(actor, project_id, template_id)
        except Exception as error:
            response = _error_response(error)
            if response is not None:
                return response
            raise
        return {"id": snapshot.snapshot_id, "name": snapshot.name}

    @router.get("")
    async def list_snapshots(request: Request, project_id: UUID, template_id: UUID):
        actor = await require_actor(request, dependencies.actor_for, dependencies.settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            snapshots = await dependencies.service.list(actor, project_id, template_id)
        except Exception as error:
            response = _error_response(error)
            if response is not None:
                return response
            raise
        return {
            "items": [
                {
                    "id": item.snapshot_id,
                    "name": item.name,
                    "created_at": item.created_at,
                }
                for item in snapshots
            ]
        }

    @router.post("/{snapshot_id}/restore")
    async def restore_snapshot(
        request: Request,
        project_id: UUID,
        template_id: UUID,
        snapshot_id: str,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await dependencies.service.restore(actor, project_id, template_id, snapshot_id)
        except Exception as error:
            response = _error_response(error)
            if response is not None:
                return response
            raise
        return {"status": "restored", "snapshot_id": snapshot_id}

    @router.delete("/{snapshot_id}")
    async def delete_snapshot(
        request: Request,
        project_id: UUID,
        template_id: UUID,
        snapshot_id: str,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await dependencies.service.delete(actor, project_id, template_id, snapshot_id)
        except Exception as error:
            response = _error_response(error)
            if response is not None:
                return response
            raise
        return {"status": "deleted", "snapshot_id": snapshot_id}

    return router


def _error_response(error: Exception) -> JSONResponse | None:
    if isinstance(error, InvalidSessionError):
        return JSONResponse(status_code=401, content={"detail": "认证失败"})
    if isinstance(error, PermissionError):
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})
    if isinstance(error, ProjectNotFoundError):
        return JSONResponse(status_code=404, content={"detail": "项目不存在"})
    if isinstance(error, EnvironmentTemplateNotFound):
        return JSONResponse(status_code=404, content={"detail": "环境模板不存在"})
    if isinstance(error, EnvironmentSnapshotNotFound):
        return JSONResponse(status_code=404, content={"detail": "快照不存在"})
    return None
