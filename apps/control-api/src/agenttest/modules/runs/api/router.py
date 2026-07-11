from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.runs.api.schemas import (
    ApplyRunResultRequest,
    CreateRunRequest,
    RunCaseListResponse,
    RunCaseResponse,
    RunListResponse,
    RunResponse,
)
from agenttest.modules.runs.application.commands import (
    ApplyRunCaseResult,
    ApplyRunCaseScore,
    ApplyRunResultCommand,
    CreateRunCommand,
    CreateRunResult,
    RunNotFoundError,
)
from agenttest.modules.runs.application.ports import RunRuntimeUnavailableError
from agenttest.modules.runs.domain.entities import Run, RunCase, RunCaseId, RunId
from agenttest.modules.runs.domain.value_objects import RunCaseStatus
from agenttest.modules.test_plans.public import TestPlanVersionId
from agenttest.shared.api.problem_details import ProblemDetails
from agenttest.shared.application.uow import UnitOfWorkFactory, null_uow_factory

CSRF_COOKIE_NAME = "agenttest_csrf"


class CurrentUserExecutor(Protocol):
    async def execute(self, session_token: str) -> User: ...


class CsrfExecutor(Protocol):
    async def execute(self, session_token: str, csrf_token: str) -> None: ...


class CreateRunExecutor(Protocol):
    async def execute(self, actor: User, command: CreateRunCommand) -> CreateRunResult: ...


class ListRunsExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        limit: int = 50,
    ) -> list[Run]: ...


class GetRunExecutor(Protocol):
    async def execute(self, actor: User, project_id: ProjectId, run_id: RunId) -> Run: ...


class ListCasesExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        project_id: ProjectId,
        run_id: RunId,
    ) -> list[RunCase]: ...


class CancelRunExecutor(Protocol):
    async def execute(self, actor: User, project_id: ProjectId, run_id: RunId) -> Run: ...


class ApplyResultExecutor(Protocol):
    async def execute(self, command: ApplyRunResultCommand) -> Run: ...


@dataclass(frozen=True, slots=True)
class RunApiDependencies:
    create_run: CreateRunExecutor
    list_runs: ListRunsExecutor
    get_run: GetRunExecutor
    list_cases: ListCasesExecutor
    cancel_run: CancelRunExecutor
    apply_result: ApplyResultExecutor
    uow_factory: UnitOfWorkFactory = null_uow_factory


def create_run_router(
    dependencies: RunApiDependencies,
    *,
    current_user: CurrentUserExecutor,
    csrf: CsrfExecutor,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(prefix="/projects/{project_id}/runs", tags=["runs"])

    async def actor_for(request: Request) -> User | JSONResponse:
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return problem(401, "Authentication required", "A valid session is required")
        try:
            return await current_user.execute(token)
        except InvalidSessionError:
            return problem(401, "Authentication required", "A valid session is required")

    async def writer(request: Request, csrf_header: str | None) -> User | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        token = request.cookies.get(settings.session_cookie_name)
        cookie = request.cookies.get(CSRF_COOKIE_NAME)
        if not token or not csrf_header or not cookie or cookie != csrf_header:
            return problem(403, "CSRF validation failed", "A valid CSRF token is required")
        try:
            await csrf.execute(token, csrf_header)
        except InvalidSessionError:
            return problem(403, "CSRF validation failed", "A valid CSRF token is required")
        return actor

    @router.post("", response_model=RunResponse, status_code=201)
    async def create_run(
        request: Request,
        response: Response,
        project_id: UUID,
        payload: CreateRunRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        x_csrf_token: str | None = Header(default=None),
    ) -> RunResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        if not idempotency_key:
            return invalid("Idempotency-Key is required")
        try:
            async with dependencies.uow_factory():
                result = await dependencies.create_run.execute(
                    actor,
                    CreateRunCommand(
                        project_id=ProjectId(project_id),
                        test_plan_version_id=TestPlanVersionId(payload.test_plan_version_id),
                        idempotency_key=idempotency_key,
                    ),
                )
        except ProjectNotFoundError:
            return not_found()
        except PermissionError:
            return denied()
        except RunRuntimeUnavailableError as error:
            return problem(503, "Run runtime unavailable", str(error))
        except ValueError as error:
            return invalid(str(error))
        if not result.created:
            response.status_code = 200
        return RunResponse.from_domain(result.run)

    @router.get("", response_model=RunListResponse)
    async def list_runs(
        request: Request,
        project_id: UUID,
        limit: int = Query(default=50, ge=1, le=100),
    ) -> RunListResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            runs = await dependencies.list_runs.execute(
                actor,
                ProjectId(project_id),
                limit=limit,
            )
        except ProjectNotFoundError:
            return not_found()
        return RunListResponse(items=[RunResponse.from_domain(run) for run in runs])

    @router.get("/{run_id}", response_model=RunResponse)
    async def get_run(
        request: Request,
        project_id: UUID,
        run_id: UUID,
    ) -> RunResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            run = await dependencies.get_run.execute(
                actor,
                ProjectId(project_id),
                RunId(run_id),
            )
        except (ProjectNotFoundError, RunNotFoundError):
            return not_found()
        return RunResponse.from_domain(run)

    @router.get("/{run_id}/cases", response_model=RunCaseListResponse)
    async def list_cases(
        request: Request,
        project_id: UUID,
        run_id: UUID,
    ) -> RunCaseListResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            cases = await dependencies.list_cases.execute(
                actor,
                ProjectId(project_id),
                RunId(run_id),
            )
        except (ProjectNotFoundError, RunNotFoundError):
            return not_found()
        return RunCaseListResponse(items=[RunCaseResponse.from_domain(case) for case in cases])

    @router.post("/{run_id}/cancel", response_model=RunResponse)
    async def cancel_run(
        request: Request,
        project_id: UUID,
        run_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> RunResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            async with dependencies.uow_factory():
                run = await dependencies.cancel_run.execute(
                    actor,
                    ProjectId(project_id),
                    RunId(run_id),
                )
        except (ProjectNotFoundError, RunNotFoundError):
            return not_found()
        except PermissionError:
            return denied()
        except RunRuntimeUnavailableError as error:
            return problem(503, "Run runtime unavailable", str(error))
        except ValueError as error:
            return invalid(str(error))
        return RunResponse.from_domain(run)

    @router.get("/{run_id}/events", response_model=None)
    async def events(
        request: Request,
        project_id: UUID,
        run_id: UUID,
    ) -> StreamingResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            run = await dependencies.get_run.execute(
                actor,
                ProjectId(project_id),
                RunId(run_id),
            )
        except (ProjectNotFoundError, RunNotFoundError):
            return not_found()

        async def stream():
            payload = RunResponse.from_domain(run).model_dump(mode="json")
            yield f"event: run.snapshot\ndata: {json.dumps(payload)}\n\n"

        return StreamingResponse(stream(), media_type="text/event-stream")

    @router.post("/{run_id}/result", response_model=RunResponse)
    async def apply_result(
        project_id: UUID,
        run_id: UUID,
        payload: ApplyRunResultRequest,
        x_internal_token: str | None = Header(default=None),
    ) -> RunResponse | JSONResponse:
        if x_internal_token != settings.internal_api_token:
            return problem(
                403,
                "Permission denied",
                "A valid internal token is required",
            )
        try:
            async with dependencies.uow_factory():
                run = await dependencies.apply_result.execute(
                    ApplyRunResultCommand(
                        project_id=ProjectId(project_id),
                        run_id=RunId(run_id),
                        cases=[
                            ApplyRunCaseResult(
                                run_case_id=RunCaseId(item.run_case_id),
                                status=RunCaseStatus(item.status),
                                output=item.output,
                                trace=item.trace,
                                error_type=item.error_type,
                                error_message=item.error_message,
                                duration_ms=item.duration_ms,
                                scores=[
                                    ApplyRunCaseScore(
                                        scorer_version_id=s.scorer_version_id,
                                        scorer_type=s.scorer_type,
                                        score=s.score,
                                        passed=s.passed,
                                        explanation=s.explanation,
                                        confidence=s.confidence,
                                    )
                                    for s in item.scores
                                ]
                                if item.scores
                                else None,
                                evidence=item.evidence,
                            )
                            for item in payload.cases
                        ],
                    )
                )
        except RunNotFoundError:
            return not_found()
        except ValueError as error:
            return invalid(str(error))
        return RunResponse.from_domain(run)

    return router


def problem(status: int, title: str, detail: str) -> JSONResponse:
    body = ProblemDetails(
        type="about:blank",
        title=title,
        status=status,
        detail=detail,
    )
    return JSONResponse(body.model_dump(), status_code=status)


def not_found() -> JSONResponse:
    return problem(404, "Run not found", "The requested run was not found")


def denied() -> JSONResponse:
    return problem(403, "Permission denied", "Project editor access is required")


def invalid(detail: str) -> JSONResponse:
    return problem(422, "Invalid run", detail)
