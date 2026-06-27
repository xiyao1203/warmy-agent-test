"""安全扫描 API 路由。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.modules.security.adapters import create_scanner
from agenttest.modules.security.domain.models import ScanStatus, SecurityScan
from agenttest.modules.security.infrastructure.repositories import (
    SqlAlchemySecurityScanRepository,
)
from agenttest.shared.api.auth_guard import require_actor, require_writer


def create_security_scan_router(
    *, session_factory, actor_for, check_project, settings,
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/security/scans",
        tags=["security-scans"],
    )

    repo = SqlAlchemySecurityScanRepository(session_factory)

    @router.get("")
    async def list_scans(request: Request, project_id: UUID, limit: int = 50):
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})

        scans = await repo.list_by_project(project_id, limit=limit)
        return {"items": [_scan_to_dict(s) for s in scans]}

    @router.post("")
    async def trigger_scan(
        request: Request,
        project_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        """触发安全扫描。"""
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})

        scan = SecurityScan.create(project_id=project_id, scan_type="promptfoo")
        await repo.add(scan)

        scan.status = ScanStatus.RUNNING
        await repo.save(scan)

        # 通过适配器执行扫描（自动选择 Promptfoo 或 Mock）
        scanner = create_scanner()
        try:
            findings = await scanner.run_scan(scan_type="full")
            scan.complete(findings)
        except Exception as e:
            scan.fail(str(e))
        await repo.save(scan)

        return _scan_to_dict(scan)

    @router.get("/{scan_id}")
    async def get_scan(
        request: Request, project_id: UUID, scan_id: UUID,
    ):
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor

        scan = await repo.get_by_id_and_project(scan_id, project_id)
        if scan is None:
            return JSONResponse(status_code=404, content={"detail": "扫描不存在"})
        return _scan_to_dict(scan)

    return router


def _scan_to_dict(scan: SecurityScan) -> dict:
    return {
        "id": str(scan.scan_id),
        "project_id": str(scan.project_id),
        "status": scan.status.value,
        "scan_type": scan.scan_type,
        "findings": scan.findings,
        "summary": scan.summary,
        "created_at": scan.created_at.isoformat(),
        "updated_at": scan.updated_at.isoformat(),
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
    }
