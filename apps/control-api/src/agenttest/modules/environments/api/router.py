"""HTTP routes for project-scoped environment templates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse, Response

from agenttest.bootstrap.settings import Settings
from agenttest.modules.environments.api.schemas import (
    CreateEnvironmentTemplateRequest,
    EnvironmentTemplateListResponse,
    EnvironmentTemplateResponse,
    UpdateEnvironmentTemplateRequest,
)
from agenttest.modules.environments.application.commands import (
    CreateEnvironmentTemplateCommand,
    DeleteEnvironmentTemplateCommand,
    EnvironmentTemplateNotFoundError,
    UpdateEnvironmentTemplateCommand,
)
from agenttest.modules.environments.domain.entities import (
    EnvironmentTemplate,
    EnvironmentTemplateId,
)
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.shared.api.problem_details import ProblemDetails
from agenttest.shared.application.uow import UnitOfWorkFactory, null_uow_factory

CSRF_COOKIE_NAME = "agenttest_csrf"


class CurrentUserExecutor(Protocol):
    async def execute(self, session_token: str) -> User: ...


class CsrfExecutor(Protocol):
    async def execute(self, session_token: str, csrf_token: str) -> None: ...


class ListTemplatesExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[EnvironmentTemplate], str | None]: ...


class GetTemplateExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        template_id: EnvironmentTemplateId,
    ) -> EnvironmentTemplate: ...


class CreateTemplateExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        command: CreateEnvironmentTemplateCommand,
    ) -> EnvironmentTemplate: ...


class UpdateTemplateExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        command: UpdateEnvironmentTemplateCommand,
    ) -> EnvironmentTemplate: ...


class DeleteTemplateExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        command: DeleteEnvironmentTemplateCommand,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class EnvironmentApiDependencies:
    list_templates: ListTemplatesExecutor
    get_template: GetTemplateExecutor
    create_template: CreateTemplateExecutor
    update_template: UpdateTemplateExecutor
    delete_template: DeleteTemplateExecutor
    uow_factory: UnitOfWorkFactory = null_uow_factory


def create_environment_router(
    dependencies: EnvironmentApiDependencies,
    *,
    current_user: CurrentUserExecutor,
    csrf: CsrfExecutor,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/environment-templates",
        tags=["environment-templates"],
    )

    async def actor_for(request: Request) -> User | JSONResponse:
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return authentication_required()
        try:
            return await current_user.execute(token)
        except InvalidSessionError:
            return authentication_required()

    async def writer(request: Request, csrf_header: str | None) -> User | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        token = request.cookies.get(settings.session_cookie_name)
        cookie = request.cookies.get(CSRF_COOKIE_NAME)
        if not token or not csrf_header or not cookie or cookie != csrf_header:
            return csrf_failed()
        try:
            await csrf.execute(token, csrf_header)
        except InvalidSessionError:
            return csrf_failed()
        return actor

    async def project_template(
        actor: User,
        project_id: UUID,
        template_id: UUID,
    ) -> EnvironmentTemplate:
        template = await dependencies.get_template.execute(
            actor,
            EnvironmentTemplateId(template_id),
        )
        if template.project_id != ProjectId(project_id):
            raise EnvironmentTemplateNotFoundError(
                EnvironmentTemplateId(template_id)
            )
        return template

    @router.get("", response_model=EnvironmentTemplateListResponse)
    async def list_templates(
        request: Request,
        project_id: UUID,
        limit: int = Query(default=50, ge=1, le=100),
        cursor: str | None = None,
    ) -> EnvironmentTemplateListResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            items, next_cursor = await dependencies.list_templates.execute(
                actor,
                ProjectId(project_id),
                limit=limit,
                cursor=cursor,
            )
        except ProjectNotFoundError:
            return asset_not_found()
        return EnvironmentTemplateListResponse(
            items=[EnvironmentTemplateResponse.from_domain(item) for item in items],
            next_cursor=next_cursor,
        )

    @router.post("", response_model=EnvironmentTemplateResponse, status_code=201)
    async def create_template(
        request: Request,
        project_id: UUID,
        payload: CreateEnvironmentTemplateRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> EnvironmentTemplateResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            async with dependencies.uow_factory():
                template = await dependencies.create_template.execute(
                    actor,
                    CreateEnvironmentTemplateCommand(
                        project_id=ProjectId(project_id),
                        name=payload.name,
                        template_type=payload.template_type,
                        config=payload.config,
                        description=payload.description,
                    ),
                )
        except ProjectNotFoundError:
            return asset_not_found()
        except PermissionError:
            return permission_denied()
        except ValueError as error:
            return invalid_request(str(error))
        return EnvironmentTemplateResponse.from_domain(template)

    @router.get("/{template_id}", response_model=EnvironmentTemplateResponse)
    async def get_template(
        request: Request,
        project_id: UUID,
        template_id: UUID,
    ) -> EnvironmentTemplateResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            template = await project_template(actor, project_id, template_id)
        except (EnvironmentTemplateNotFoundError, ProjectNotFoundError):
            return asset_not_found()
        return EnvironmentTemplateResponse.from_domain(template)

    @router.patch("/{template_id}", response_model=EnvironmentTemplateResponse)
    async def update_template(
        request: Request,
        project_id: UUID,
        template_id: UUID,
        payload: UpdateEnvironmentTemplateRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> EnvironmentTemplateResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_template(actor, project_id, template_id)
            async with dependencies.uow_factory():
                template = await dependencies.update_template.execute(
                    actor,
                    UpdateEnvironmentTemplateCommand(
                        template_id=EnvironmentTemplateId(template_id),
                        name=payload.name,
                        description=payload.description,
                        config=payload.config,
                    ),
                )
        except (EnvironmentTemplateNotFoundError, ProjectNotFoundError):
            return asset_not_found()
        except PermissionError:
            return permission_denied()
        except ValueError as error:
            return invalid_request(str(error))
        return EnvironmentTemplateResponse.from_domain(template)

    @router.delete(
        "/{template_id}",
        status_code=204,
        response_model=None,
    )
    async def delete_template(
        request: Request,
        project_id: UUID,
        template_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> Response:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_template(actor, project_id, template_id)
            async with dependencies.uow_factory():
                await dependencies.delete_template.execute(
                    actor,
                    DeleteEnvironmentTemplateCommand(
                        template_id=EnvironmentTemplateId(template_id)
                    ),
                )
        except (EnvironmentTemplateNotFoundError, ProjectNotFoundError):
            return asset_not_found()
        except PermissionError:
            return permission_denied()
        return Response(status_code=204)

    return router


def authentication_required() -> JSONResponse:
    return problem_response(401, "Authentication required", "A valid session is required")


def csrf_failed() -> JSONResponse:
    return problem_response(403, "CSRF validation failed", "A valid CSRF token is required")


def permission_denied() -> JSONResponse:
    return problem_response(403, "Permission denied", "Project editor access is required")


def asset_not_found() -> JSONResponse:
    return problem_response(404, "Asset not found", "Asset was not found")


def invalid_request(detail: str) -> JSONResponse:
    return problem_response(400, "Invalid request", detail)


def problem_response(status: int, title: str, detail: str) -> JSONResponse:
    problem = ProblemDetails(title=title, status=status, detail=detail)
    return JSONResponse(
        status_code=status,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )
