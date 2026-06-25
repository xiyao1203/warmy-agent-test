from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from agenttest.bootstrap.settings import Settings
from agenttest.modules.audit.api.schemas import AuditEntryResponse, AuditListResponse
from agenttest.modules.audit.application.ports import AuditReader
from agenttest.modules.identity.public import InvalidSessionError, SystemRole, User
from agenttest.modules.projects.public import (
    ProjectAccessPolicy,
    ProjectId,
    ProjectNotFoundError,
)
from agenttest.shared.api.problem_details import ProblemDetails


class CurrentUserExecutor(Protocol):
    async def execute(self, session_token: str) -> User: ...


class ProjectReader(Protocol):
    async def get_by_id(self, project_id: ProjectId): ...


@dataclass(frozen=True, slots=True)
class AuditApiDependencies:
    audits: AuditReader
    projects: ProjectReader


def create_audit_router(
    dependencies: AuditApiDependencies,
    *,
    current_user: CurrentUserExecutor,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(tags=["audit"])

    async def actor_for(request: Request) -> User | JSONResponse:
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return authentication_required()
        try:
            return await current_user.execute(token)
        except InvalidSessionError:
            return authentication_required()

    @router.get("/system/audit", response_model=AuditListResponse)
    async def global_audit(
        request: Request,
        limit: int = Query(default=100, ge=1, le=500),
    ) -> AuditListResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        if actor.role is not SystemRole.SUPER_ADMIN:
            return permission_denied()
        entries = await dependencies.audits.list_global(limit=limit)
        return audit_response(entries)

    @router.get("/projects/{project_id}/audit", response_model=AuditListResponse)
    async def project_audit(
        request: Request,
        project_id: UUID,
        limit: int = Query(default=100, ge=1, le=500),
    ) -> AuditListResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        resolved_id = ProjectId(project_id)
        project = await dependencies.projects.get_by_id(resolved_id)
        if project is None:
            return project_not_found()
        try:
            ProjectAccessPolicy.ensure_can_view(actor, project)
        except ProjectNotFoundError:
            return project_not_found()
        entries = await dependencies.audits.list_project(
            project_id=resolved_id,
            limit=limit,
        )
        return audit_response(entries)

    return router


def audit_response(entries: list) -> AuditListResponse:
    return AuditListResponse(items=[AuditEntryResponse.from_entry(entry) for entry in entries])


def authentication_required() -> JSONResponse:
    return problem_response(401, "Authentication required", "A valid session is required")


def permission_denied() -> JSONResponse:
    return problem_response(403, "Permission denied", "Super administrator access is required")


def project_not_found() -> JSONResponse:
    return problem_response(404, "Project not found", "Project was not found")


def problem_response(status: int, title: str, detail: str) -> JSONResponse:
    problem = ProblemDetails(title=title, status=status, detail=detail)
    return JSONResponse(
        status_code=status,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )
