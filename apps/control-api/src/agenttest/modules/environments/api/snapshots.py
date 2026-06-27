"""环境快照 API 端点。

提供环境模板的快照创建、列表和恢复功能。
快照存储在 environment_templates.config JSON 字段中。
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from agenttest.modules.environments.infrastructure.persistence.repositories import (
    SqlAlchemyEnvironmentTemplateRepository,
)
from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.projects.public import ProjectNotFoundError


def create_snapshot_router(
    *,
    session_factory,
    actor_for,
    check_project,
) -> APIRouter:
    """创建环境快照 API 路由。"""
    router = APIRouter(
        prefix="/projects/{project_id}/environments/{template_id}/snapshots",
        tags=["environment-snapshots"],
    )

    @router.post("")
    async def create_snapshot(
        request: Request,
        project_id: UUID,
        template_id: UUID,
    ):
        """创建环境快照（保存当前配置）。"""
        try:
            await check_project(project_id)
        except (ProjectNotFoundError, InvalidSessionError):
            return JSONResponse(
                status_code=404, content={"detail": "项目或环境不存在"}
            )

        async with session_factory() as session:
            repo = SqlAlchemyEnvironmentTemplateRepository(session)
            template = await repo.get(template_id, project_id=project_id)
            if template is None:
                return JSONResponse(
                    status_code=404, content={"detail": "环境模板不存在"}
                )

            snapshot_id = str(uuid4())
            snapshot = {
                "id": snapshot_id,
                "name": f"snapshot-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}",
                "config": dict(template.config),
                "created_at": datetime.now(UTC).isoformat(),
            }

            snapshots = list(template.config.get("snapshots", []))
            snapshots.append(snapshot)
            template.config["snapshots"] = snapshots
            await repo.save(template, project_id=project_id)
            await session.commit()

            return {"id": snapshot_id, "name": snapshot["name"]}

    @router.get("")
    async def list_snapshots(
        request: Request,
        project_id: UUID,
        template_id: UUID,
    ):
        """列出环境模板的所有快照。"""
        try:
            await check_project(project_id)
        except (ProjectNotFoundError, InvalidSessionError):
            return JSONResponse(
                status_code=404, content={"detail": "项目或环境不存在"}
            )

        async with session_factory() as session:
            repo = SqlAlchemyEnvironmentTemplateRepository(session)
            template = await repo.get(template_id, project_id=project_id)
            if template is None:
                return JSONResponse(
                    status_code=404, content={"detail": "环境模板不存在"}
                )

            snapshots = list(template.config.get("snapshots", []))
            return {
                "items": [
                    {
                        "id": s.get("id"),
                        "name": s.get("name"),
                        "created_at": s.get("created_at"),
                    }
                    for s in snapshots
                ]
            }

    @router.post("/{snapshot_id}/restore")
    async def restore_snapshot(
        request: Request,
        project_id: UUID,
        template_id: UUID,
        snapshot_id: str,
    ):
        """从快照恢复环境配置。"""
        try:
            await check_project(project_id)
        except (ProjectNotFoundError, InvalidSessionError):
            return JSONResponse(
                status_code=404, content={"detail": "项目或环境不存在"}
            )

        async with session_factory() as session:
            repo = SqlAlchemyEnvironmentTemplateRepository(session)
            template = await repo.get(template_id, project_id=project_id)
            if template is None:
                return JSONResponse(
                    status_code=404, content={"detail": "环境模板不存在"}
                )

            snapshots = list(template.config.get("snapshots", []))
            snapshot = next(
                (s for s in snapshots if s.get("id") == snapshot_id), None
            )
            if snapshot is None:
                return JSONResponse(
                    status_code=404, content={"detail": "快照不存在"}
                )

            template.config = dict(snapshot.get("config", {}))
            template.config["snapshots"] = snapshots
            await repo.save(template, project_id=project_id)
            await session.commit()

            return {"status": "restored", "snapshot_id": snapshot_id}

    @router.delete("/{snapshot_id}")
    async def delete_snapshot(
        request: Request,
        project_id: UUID,
        template_id: UUID,
        snapshot_id: str,
    ):
        """删除快照。"""
        try:
            await check_project(project_id)
        except (ProjectNotFoundError, InvalidSessionError):
            return JSONResponse(
                status_code=404, content={"detail": "项目或环境不存在"}
            )

        async with session_factory() as session:
            repo = SqlAlchemyEnvironmentTemplateRepository(session)
            template = await repo.get(template_id, project_id=project_id)
            if template is None:
                return JSONResponse(
                    status_code=404, content={"detail": "环境模板不存在"}
                )

            snapshots = list(template.config.get("snapshots", []))
            snapshots = [s for s in snapshots if s.get("id") != snapshot_id]
            template.config["snapshots"] = snapshots
            await repo.save(template, project_id=project_id)
            await session.commit()

            return {"status": "deleted", "snapshot_id": snapshot_id}

    return router
