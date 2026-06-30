from __future__ import annotations

from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.reports.application.service import (
    ReportNotFoundError,
    ReportService,
)
from agenttest.modules.reports.generators.html_report import HtmlReportGenerator
from agenttest.modules.reports.generators.json_report import JsonReportGenerator
from agenttest.modules.reports.generators.junit_report import JunitReportGenerator
from agenttest.modules.runs.public import RunId


class CurrentUserExecutor(Protocol):
    async def execute(self, session_token: str) -> User: ...


def create_report_router(
    *,
    service: ReportService,
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
            report = await service.build(actor, ProjectId(project_id), RunId(run_id))
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})
        except (ProjectNotFoundError, ReportNotFoundError):
            return JSONResponse(status_code=404, content={"detail": "运行不存在"})

        if format == "json":
            return PlainTextResponse(
                JsonReportGenerator().generate(report),
                media_type="application/json",
            )
        if format == "junit":
            return PlainTextResponse(
                JunitReportGenerator().generate(report),
                media_type="application/xml",
            )
        return HTMLResponse(HtmlReportGenerator().generate(report))

    return router
