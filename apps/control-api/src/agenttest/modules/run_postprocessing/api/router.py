from __future__ import annotations

from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.modules.run_postprocessing.api.schemas import (
    CalibrationResponse,
    DiagnosticListResponse,
    DiagnosticResponse,
    JointGateDecisionResponse,
    RegressionCandidateListResponse,
    RegressionCandidateResponse,
    TrustLoopResponse,
)
from agenttest.modules.run_postprocessing.queries import RunTrustLoopQueryService
from agenttest.modules.runs.public import RunNotFoundError
from agenttest.shared.api.problem_details import ProblemDetails


class CurrentUserExecutor(Protocol):
    async def execute(self, session_token: str) -> User: ...


def create_run_trust_loop_router(
    *,
    service: RunTrustLoopQueryService,
    current_user: CurrentUserExecutor,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(prefix="/projects/{project_id}/runs/{run_id}", tags=["run-trust-loop"])

    async def actor_for(request: Request) -> User | JSONResponse:
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return _problem(401, "Authentication required", "A valid session is required")
        try:
            return await current_user.execute(token)
        except InvalidSessionError:
            return _problem(401, "Authentication required", "A valid session is required")

    @router.get("/trust-loop", response_model=TrustLoopResponse)
    async def get_trust_loop(
        request: Request, project_id: UUID, run_id: UUID
    ) -> TrustLoopResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            value = await service.get_summary(actor, project_id, run_id)
        except (ProjectNotFoundError, RunNotFoundError):
            return _not_found()
        return TrustLoopResponse.model_validate(value)

    @router.get("/diagnostics", response_model=DiagnosticListResponse)
    async def list_diagnostics(
        request: Request,
        project_id: UUID,
        run_id: UUID,
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> DiagnosticListResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            items, total = await service.list_diagnostics(
                actor, project_id, run_id, limit=limit, offset=offset
            )
        except (ProjectNotFoundError, RunNotFoundError):
            return _not_found()
        return DiagnosticListResponse(
            items=[DiagnosticResponse.model_validate(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    @router.get("/regressions", response_model=RegressionCandidateListResponse)
    async def list_regressions(
        request: Request,
        project_id: UUID,
        run_id: UUID,
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> RegressionCandidateListResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            items, total = await service.list_regressions(
                actor, project_id, run_id, limit=limit, offset=offset
            )
        except (ProjectNotFoundError, RunNotFoundError):
            return _not_found()
        return RegressionCandidateListResponse(
            items=[RegressionCandidateResponse.model_validate(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    @router.get("/calibration", response_model=CalibrationResponse)
    async def get_calibration(
        request: Request, project_id: UUID, run_id: UUID
    ) -> CalibrationResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            value = await service.get_calibration(actor, project_id, run_id)
        except (ProjectNotFoundError, RunNotFoundError):
            return _not_found()
        return CalibrationResponse.model_validate(value)

    @router.get("/joint-gate", response_model=JointGateDecisionResponse)
    async def get_joint_gate(
        request: Request, project_id: UUID, run_id: UUID
    ) -> JointGateDecisionResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            value = await service.get_joint_gate(actor, project_id, run_id)
        except (ProjectNotFoundError, RunNotFoundError):
            return _not_found()
        return JointGateDecisionResponse.model_validate(value)

    return router


def _problem(status: int, title: str, detail: str) -> JSONResponse:
    body = ProblemDetails(type="about:blank", title=title, status=status, detail=detail)
    return JSONResponse(body.model_dump(), status_code=status)


def _not_found() -> JSONResponse:
    return _problem(404, "Run not found", "The requested run was not found")
