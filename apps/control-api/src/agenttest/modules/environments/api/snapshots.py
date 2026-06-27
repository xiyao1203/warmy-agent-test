"""环境快照 API 端点。"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from agenttest.modules.environments.domain.entities import EnvironmentTemplateId
from agenttest.modules.environments.infrastructure.persistence.repositories import (
    SqlAlchemyEnvironmentTemplateRepository,
)
from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.projects.public import ProjectId as Pid
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.shared.api.auth_guard import require_actor, require_writer


def create_snapshot_router(
    *,
    session_factory,
    actor_for,
    check_project,
    settings,
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/environments/{template_id}/snapshots",
        tags=["environment-snapshots"],
    )

    repo = SqlAlchemyEnvironmentTemplateRepository(session_factory)

    @router.post("")
    async def create_snapshot(
        request: Request,
        project_id: UUID,
        template_id: UUID,
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

        template = await repo.get_by_id_and_project(
            EnvironmentTemplateId(template_id), Pid(project_id),
        )
        if template is None:
            return JSONResponse(status_code=404, content={"detail": "环境模板不存在"})

        snapshot_id = str(uuid4())
        snapshot = {
            "id": snapshot_id,
            "name": f"snapshot-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}",
            "config": dict(template.config),
            "created_at": datetime.now(UTC).isoformat(),
        }
        snapshots = list(template.config.get("snapshots", []))  # type: ignore[call-overload]
        snapshots.append(snapshot)
        template.config["snapshots"] = snapshots  # type: ignore[assignment]
        await repo.save(template)
        return {"id": snapshot_id, "name": snapshot["name"]}

    @router.get("")
    async def list_snapshots(
        request: Request,
        project_id: UUID,
        template_id: UUID,
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

        template = await repo.get_by_id_and_project(
            EnvironmentTemplateId(template_id), Pid(project_id),
        )
        if template is None:
            return JSONResponse(status_code=404, content={"detail": "环境模板不存在"})

        snapshots = list(template.config.get("snapshots", []))  # type: ignore[call-overload]
        return {
            "items": [
                {"id": s.get("id"), "name": s.get("name"), "created_at": s.get("created_at")}
                for s in snapshots
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
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})

        template = await repo.get_by_id_and_project(
            EnvironmentTemplateId(template_id), Pid(project_id),
        )
        if template is None:
            return JSONResponse(status_code=404, content={"detail": "环境模板不存在"})

        snapshots = list(template.config.get("snapshots", []))  # type: ignore[call-overload]
        snapshot = next((s for s in snapshots if s.get("id") == snapshot_id), None)
        if snapshot is None:
            return JSONResponse(status_code=404, content={"detail": "快照不存在"})

        template.config = dict(snapshot.get("config", {}))  # type: ignore[arg-type]
        template.config["snapshots"] = snapshots  # type: ignore[assignment]
        await repo.save(template)
        return {"status": "restored", "snapshot_id": snapshot_id}

    @router.delete("/{snapshot_id}")
    async def delete_snapshot(
        request: Request,
        project_id: UUID,
        template_id: UUID,
        snapshot_id: str,
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

        template = await repo.get_by_id_and_project(
            EnvironmentTemplateId(template_id), Pid(project_id),
        )
        if template is None:
            return JSONResponse(status_code=404, content={"detail": "环境模板不存在"})

        snapshots = list(template.config.get("snapshots", []))  # type: ignore[call-overload]
        snapshots = [s for s in snapshots if s.get("id") != snapshot_id]
        template.config["snapshots"] = snapshots  # type: ignore[assignment]
        await repo.save(template)
        return {"status": "deleted", "snapshot_id": snapshot_id}

    return router
