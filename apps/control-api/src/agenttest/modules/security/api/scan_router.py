"""Security-scan HTTP adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.modules.security.application.scan_service import (
    InvalidSecurityTarget,
    SecurityScanNotFound,
    SecurityScanService,
)
from agenttest.modules.security.domain.models import SecurityScan
from agenttest.shared.api.auth_guard import require_actor, require_writer


class SecurityScanRequest(BaseModel):
    agent_version_id: UUID
    run_id: UUID | None = None
    environment_version_id: UUID | None = None
    security_profile_id: UUID | None = None
    scan_type: Literal["full", "quick"] = "full"


class ActorResolver(Protocol):
    async def __call__(self, request: Request) -> User | None: ...


@dataclass(frozen=True, slots=True)
class SecurityScanApiDependencies:
    service: SecurityScanService
    actor_for: ActorResolver
    settings: Settings


def create_security_scan_router(
    dependencies: SecurityScanApiDependencies,
) -> APIRouter:
    router = APIRouter(prefix="/projects/{project_id}/security/scans", tags=["security-scans"])

    @router.get("")
    async def list_scans(request: Request, project_id: UUID, limit: int = 50):
        actor = await require_actor(request, dependencies.actor_for, dependencies.settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            scans = await dependencies.service.list(actor, project_id, limit=limit)
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        return {"items": [_scan_to_dict(scan) for scan in scans]}

    @router.post("")
    async def trigger_scan(
        request: Request,
        project_id: UUID,
        body: SecurityScanRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            scan = await dependencies.service.trigger(
                actor,
                project_id,
                agent_version_id=body.agent_version_id,
                run_id=body.run_id,
                environment_version_id=body.environment_version_id,
                security_profile_id=body.security_profile_id,
                scan_type=body.scan_type,
            )
        except InvalidSecurityTarget:
            return JSONResponse(
                status_code=422,
                content={"detail": "请选择本项目已发布且可执行的 Agent 版本"},
            )
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        return _scan_to_dict(scan)

    @router.get("/{scan_id}")
    async def get_scan(request: Request, project_id: UUID, scan_id: UUID):
        actor = await require_actor(request, dependencies.actor_for, dependencies.settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            scan = await dependencies.service.get(actor, project_id, scan_id)
        except SecurityScanNotFound:
            return JSONResponse(status_code=404, content={"detail": "扫描不存在"})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        return _scan_to_dict(scan)

    return router


def _access_error(error: Exception) -> JSONResponse | None:
    if isinstance(error, InvalidSessionError):
        return JSONResponse(status_code=401, content={"detail": "认证失败"})
    if isinstance(error, PermissionError):
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})
    if isinstance(error, ProjectNotFoundError):
        return JSONResponse(status_code=404, content={"detail": "项目不存在"})
    return None


def _scan_to_dict(scan: SecurityScan) -> dict[str, object]:
    return {
        "id": str(scan.scan_id),
        "project_id": str(scan.project_id),
        "status": scan.status.value,
        "scan_type": scan.scan_type,
        "run_id": str(scan.run_id) if scan.run_id else None,
        "agent_version_id": str(scan.agent_version_id) if scan.agent_version_id else None,
        "environment_version_id": (
            str(scan.environment_version_id) if scan.environment_version_id else None
        ),
        "security_profile_id": (
            str(scan.security_profile_id) if scan.security_profile_id else None
        ),
        "findings": scan.findings,
        "summary": scan.summary,
        "created_at": scan.created_at.isoformat(),
        "updated_at": scan.updated_at.isoformat(),
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
    }
