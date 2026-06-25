"""HTTP routes for project-scoped TestPlan assets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse

from agenttest.bootstrap.settings import Settings
from agenttest.modules.agents.public import AgentVersionId
from agenttest.modules.datasets.public import DatasetVersionId
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.test_plans.api.schemas import (
    CreateTestPlanRequest,
    CreateTestPlanVersionRequest,
    TestPlanListResponse,
    TestPlanResponse,
    TestPlanVersionListResponse,
    TestPlanVersionResponse,
    UpdateTestPlanRequest,
    UpdateTestPlanVersionRequest,
)
from agenttest.modules.test_plans.application.commands import (
    CreateTestPlanCommand,
    CreateTestPlanVersionCommand,
    PublishTestPlanVersionCommand,
    TestPlanNotFoundError,
    TestPlanVersionNotFoundError,
    UpdateTestPlanCommand,
    UpdateTestPlanVersionCommand,
)
from agenttest.modules.test_plans.domain.entities import (
    EnvironmentTemplateId,
    TestPlan,
    TestPlanId,
    TestPlanVersion,
    TestPlanVersionId,
)
from agenttest.shared.api.problem_details import ProblemDetails
from agenttest.shared.application.uow import UnitOfWorkFactory, null_uow_factory

CSRF_COOKIE_NAME = "agenttest_csrf"


class CurrentUserExecutor(Protocol):
    async def execute(self, session_token: str) -> User: ...


class CsrfExecutor(Protocol):
    async def execute(self, session_token: str, csrf_token: str) -> None: ...


class ListPlansExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[TestPlan], str | None]: ...


class GetPlanExecutor(Protocol):
    async def execute(self, actor: User, plan_id: TestPlanId) -> TestPlan: ...


class CreatePlanExecutor(Protocol):
    async def execute(self, actor: User, command: CreateTestPlanCommand) -> TestPlan: ...


class UpdatePlanExecutor(Protocol):
    async def execute(self, actor: User, command: UpdateTestPlanCommand) -> TestPlan: ...


class ListVersionsExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        plan_id: TestPlanId,
    ) -> list[TestPlanVersion]: ...


class GetVersionExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        version_id: TestPlanVersionId,
    ) -> TestPlanVersion: ...


class CreateVersionExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        command: CreateTestPlanVersionCommand,
    ) -> TestPlanVersion: ...


class UpdateVersionExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        command: UpdateTestPlanVersionCommand,
    ) -> TestPlanVersion: ...


class PublishVersionExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        command: PublishTestPlanVersionCommand,
    ) -> TestPlanVersion: ...


@dataclass(frozen=True, slots=True)
class TestPlanApiDependencies:
    list_plans: ListPlansExecutor
    get_plan: GetPlanExecutor
    create_plan: CreatePlanExecutor
    update_plan: UpdatePlanExecutor
    list_versions: ListVersionsExecutor
    get_version: GetVersionExecutor
    create_version: CreateVersionExecutor
    update_version: UpdateVersionExecutor
    publish_version: PublishVersionExecutor
    uow_factory: UnitOfWorkFactory = null_uow_factory


def create_test_plan_router(
    dependencies: TestPlanApiDependencies,
    *,
    current_user: CurrentUserExecutor,
    csrf: CsrfExecutor,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/test-plans",
        tags=["test-plans"],
    )

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

    async def scoped_plan(actor: User, project_id: UUID, plan_id: UUID) -> TestPlan:
        plan = await dependencies.get_plan.execute(actor, TestPlanId(plan_id))
        if plan.project_id != ProjectId(project_id):
            raise TestPlanNotFoundError(TestPlanId(plan_id))
        return plan

    async def scoped_version(
        actor: User,
        project_id: UUID,
        plan_id: UUID,
        version_id: UUID,
    ) -> TestPlanVersion:
        plan = await scoped_plan(actor, project_id, plan_id)
        version = await dependencies.get_version.execute(
            actor,
            TestPlanVersionId(version_id),
        )
        if version.test_plan_id != plan.test_plan_id:
            raise TestPlanVersionNotFoundError(TestPlanVersionId(version_id))
        return version

    @router.get("", response_model=TestPlanListResponse)
    async def list_plans(
        request: Request,
        project_id: UUID,
        limit: int = Query(default=50, ge=1, le=100),
        cursor: str | None = None,
    ) -> TestPlanListResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            items, next_cursor = await dependencies.list_plans.execute(
                actor,
                ProjectId(project_id),
                limit=limit,
                cursor=cursor,
            )
        except ProjectNotFoundError:
            return not_found()
        return TestPlanListResponse(
            items=[TestPlanResponse.from_domain(item) for item in items],
            next_cursor=next_cursor,
        )

    @router.post("", response_model=TestPlanResponse, status_code=201)
    async def create_plan(
        request: Request,
        project_id: UUID,
        payload: CreateTestPlanRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> TestPlanResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            async with dependencies.uow_factory():
                plan = await dependencies.create_plan.execute(
                    actor,
                    CreateTestPlanCommand(
                        project_id=ProjectId(project_id),
                        name=payload.name,
                        description=payload.description,
                    ),
                )
        except ProjectNotFoundError:
            return not_found()
        except PermissionError:
            return denied()
        except ValueError as error:
            return invalid(str(error))
        return TestPlanResponse.from_domain(plan)

    @router.get("/{plan_id}", response_model=TestPlanResponse)
    async def get_plan(
        request: Request,
        project_id: UUID,
        plan_id: UUID,
    ) -> TestPlanResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            plan = await scoped_plan(actor, project_id, plan_id)
        except (TestPlanNotFoundError, ProjectNotFoundError):
            return not_found()
        return TestPlanResponse.from_domain(plan)

    @router.patch("/{plan_id}", response_model=TestPlanResponse)
    async def update_plan(
        request: Request,
        project_id: UUID,
        plan_id: UUID,
        payload: UpdateTestPlanRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> TestPlanResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await scoped_plan(actor, project_id, plan_id)
            async with dependencies.uow_factory():
                plan = await dependencies.update_plan.execute(
                    actor,
                    UpdateTestPlanCommand(
                        test_plan_id=TestPlanId(plan_id),
                        name=payload.name,
                        description=payload.description,
                    ),
                )
        except (TestPlanNotFoundError, ProjectNotFoundError):
            return not_found()
        except PermissionError:
            return denied()
        except ValueError as error:
            return invalid(str(error))
        return TestPlanResponse.from_domain(plan)

    @router.get("/{plan_id}/versions", response_model=TestPlanVersionListResponse)
    async def list_versions(
        request: Request,
        project_id: UUID,
        plan_id: UUID,
    ) -> TestPlanVersionListResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await scoped_plan(actor, project_id, plan_id)
            items = await dependencies.list_versions.execute(actor, TestPlanId(plan_id))
        except (TestPlanNotFoundError, ProjectNotFoundError):
            return not_found()
        return TestPlanVersionListResponse(
            items=[TestPlanVersionResponse.from_domain(item) for item in items]
        )

    @router.post(
        "/{plan_id}/versions",
        response_model=TestPlanVersionResponse,
        status_code=201,
    )
    async def create_version(
        request: Request,
        project_id: UUID,
        plan_id: UUID,
        payload: CreateTestPlanVersionRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> TestPlanVersionResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await scoped_plan(actor, project_id, plan_id)
            async with dependencies.uow_factory():
                version = await dependencies.create_version.execute(
                    actor,
                    CreateTestPlanVersionCommand(
                        test_plan_id=TestPlanId(plan_id),
                        config=payload.config.to_domain(),
                        agent_version_id=(
                            AgentVersionId(payload.agent_version_id)
                            if payload.agent_version_id
                            else None
                        ),
                        dataset_version_id=(
                            DatasetVersionId(payload.dataset_version_id)
                            if payload.dataset_version_id
                            else None
                        ),
                        environment_template_id=(
                            EnvironmentTemplateId(payload.environment_template_id)
                            if payload.environment_template_id
                            else None
                        ),
                    ),
                )
        except (TestPlanNotFoundError, ProjectNotFoundError):
            return not_found()
        except PermissionError:
            return denied()
        except ValueError as error:
            return invalid(str(error))
        return TestPlanVersionResponse.from_domain(version)

    @router.get(
        "/{plan_id}/versions/{version_id}",
        response_model=TestPlanVersionResponse,
    )
    async def get_version(
        request: Request,
        project_id: UUID,
        plan_id: UUID,
        version_id: UUID,
    ) -> TestPlanVersionResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            version = await scoped_version(actor, project_id, plan_id, version_id)
        except (
            TestPlanNotFoundError,
            TestPlanVersionNotFoundError,
            ProjectNotFoundError,
        ):
            return not_found()
        return TestPlanVersionResponse.from_domain(version)

    @router.patch(
        "/{plan_id}/versions/{version_id}",
        response_model=TestPlanVersionResponse,
    )
    async def update_version(
        request: Request,
        project_id: UUID,
        plan_id: UUID,
        version_id: UUID,
        payload: UpdateTestPlanVersionRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> TestPlanVersionResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await scoped_version(actor, project_id, plan_id, version_id)
            async with dependencies.uow_factory():
                version = await dependencies.update_version.execute(
                    actor,
                    UpdateTestPlanVersionCommand(
                        version_id=TestPlanVersionId(version_id),
                        config=payload.config.to_domain() if payload.config else None,
                        agent_version_id=(
                            AgentVersionId(payload.agent_version_id)
                            if payload.agent_version_id
                            else None
                        ),
                        dataset_version_id=(
                            DatasetVersionId(payload.dataset_version_id)
                            if payload.dataset_version_id
                            else None
                        ),
                        environment_template_id=(
                            EnvironmentTemplateId(payload.environment_template_id)
                            if payload.environment_template_id
                            else None
                        ),
                    ),
                )
        except (
            TestPlanNotFoundError,
            TestPlanVersionNotFoundError,
            ProjectNotFoundError,
        ):
            return not_found()
        except PermissionError:
            return denied()
        except ValueError as error:
            return conflict(str(error))
        return TestPlanVersionResponse.from_domain(version)

    @router.post(
        "/{plan_id}/versions/{version_id}/publish",
        response_model=TestPlanVersionResponse,
    )
    async def publish_version(
        request: Request,
        project_id: UUID,
        plan_id: UUID,
        version_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> TestPlanVersionResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await scoped_version(actor, project_id, plan_id, version_id)
            async with dependencies.uow_factory():
                version = await dependencies.publish_version.execute(
                    actor,
                    PublishTestPlanVersionCommand(
                        version_id=TestPlanVersionId(version_id)
                    ),
                )
        except (
            TestPlanNotFoundError,
            TestPlanVersionNotFoundError,
            ProjectNotFoundError,
        ):
            return not_found()
        except PermissionError:
            return denied()
        except ValueError as error:
            return conflict(str(error))
        return TestPlanVersionResponse.from_domain(version)

    return router


def denied() -> JSONResponse:
    return problem(403, "Permission denied", "Project editor access is required")


def not_found() -> JSONResponse:
    return problem(404, "Asset not found", "Asset was not found")


def invalid(detail: str) -> JSONResponse:
    return problem(400, "Invalid request", detail)


def conflict(detail: str) -> JSONResponse:
    return problem(409, "Conflict", detail)


def problem(status: int, title: str, detail: str) -> JSONResponse:
    body = ProblemDetails(title=title, status=status, detail=detail)
    return JSONResponse(
        status_code=status,
        content=body.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )
