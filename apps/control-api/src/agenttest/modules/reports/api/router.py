from __future__ import annotations

from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.reports.application.export import ExportedReport
from agenttest.modules.reports.application.service import (
    ReportNotFoundError,
)
from agenttest.modules.runs.public import RunId


class CurrentUserExecutor(Protocol):
    async def execute(self, session_token: str) -> User: ...


class ReportExporter(Protocol):
    """报告导出 Application 能力。"""

    async def export(
        self,
        actor: User,
        project_id: ProjectId,
        run_id: RunId,
        report_format: str,
    ) -> ExportedReport: ...


def create_report_router(
    *,
    exporter: ReportExporter,
    current_user: CurrentUserExecutor,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/runs",
        tags=["reports"],
    )

    @router.get("/{run_id}/export")
    async def export_run_report(
        request: Request,
        project_id: UUID,
        run_id: UUID,
        format: str = Query(default="json", pattern="^(json|junit|html)$"),
    ):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})
        try:
            actor = await current_user.execute(token)
            report = await exporter.export(
                actor,
                ProjectId(project_id),
                RunId(run_id),
                format,
            )
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})
        except (ProjectNotFoundError, ReportNotFoundError):
            return JSONResponse(status_code=404, content={"detail": "运行不存在"})

        if report.media_type == "text/html":
            return HTMLResponse(report.content)
        return PlainTextResponse(report.content, media_type=report.media_type)

    return router
