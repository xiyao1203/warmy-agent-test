from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse, Response

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import InvalidSessionError, User, UserId
from agenttest.modules.projects.api.schemas import (
    CreateProjectRequest,
    ProjectListResponse,
    ProjectMemberRequest,
    ProjectMemberResponse,
    ProjectMembersResponse,
    ProjectMemberUpdateRequest,
    ProjectResponse,
    RenameProjectRequest,
)
from agenttest.modules.projects.application.commands.create_project import (
    CreateProjectCommand,
)
from agenttest.modules.projects.application.commands.manage_members import (
    ProjectMemberCommand,
    RenameProjectCommand,
)
from agenttest.modules.projects.domain.entities import (
    Project,
    ProjectId,
    ProjectMemberRole,
)
from agenttest.modules.projects.domain.policies import (
    ProjectAccessDeniedError,
    ProjectNotFoundError,
)
from agenttest.shared.api.problem_details import ProblemDetails
from agenttest.shared.application.uow import UnitOfWorkFactory, null_uow_factory

CSRF_COOKIE_NAME = "agenttest_csrf"


class CurrentUserExecutor(Protocol):
    async def execute(self, session_token: str) -> User: ...


class CsrfExecutor(Protocol):
    async def execute(self, session_token: str, csrf_token: str) -> None: ...


class ListProjectsExecutor(Protocol):
    async def execute(self, actor: User) -> list[Project]: ...


class GetProjectExecutor(Protocol):
    async def execute(self, actor: User, project_id: ProjectId) -> Project: ...


class CreateProjectExecutor(Protocol):
    async def execute(self, actor: User, command: CreateProjectCommand) -> Project: ...


class RenameProjectExecutor(Protocol):
    async def execute(self, actor: User, command: RenameProjectCommand) -> Project: ...


class ArchiveProjectExecutor(Protocol):
    async def execute(self, actor: User, project_id: ProjectId) -> Project: ...


class ListMembersExecutor(Protocol):
    async def execute(self, actor: User, project_id: ProjectId) -> Project: ...


class ManageMemberExecutor(Protocol):
    async def execute(self, actor: User, command: ProjectMemberCommand) -> Project: ...


class RemoveMemberExecutor(Protocol):
    async def execute(self, actor: User, project_id: ProjectId, user_id: UserId) -> None: ...


@dataclass(frozen=True, slots=True)
class ProjectApiDependencies:
    list_projects: ListProjectsExecutor
    get_project: GetProjectExecutor
    create_project: CreateProjectExecutor
    rename_project: RenameProjectExecutor
    archive_project: ArchiveProjectExecutor
    list_members: ListMembersExecutor
    add_member: ManageMemberExecutor
    update_member: ManageMemberExecutor
    remove_member: RemoveMemberExecutor
    uow_factory: UnitOfWorkFactory = null_uow_factory


def create_project_router(
    dependencies: ProjectApiDependencies,
    *,
    current_user: CurrentUserExecutor,
    csrf: CsrfExecutor,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(prefix="/projects", tags=["projects"])

    async def actor_for(request: Request) -> User | JSONResponse:
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return authentication_required()
        try:
            return await current_user.execute(token)
        except InvalidSessionError:
            return authentication_required()

    async def writer(
        request: Request,
        csrf_header: str | None,
    ) -> User | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        token = request.cookies.get(settings.session_cookie_name)
        cookie = request.cookies.get(CSRF_COOKIE_NAME)
        if not token or not csrf_header or not cookie or csrf_header != cookie:
            return csrf_failed()
        try:
            await csrf.execute(token, csrf_header)
        except InvalidSessionError:
            return csrf_failed()
        return actor

    @router.get("", response_model=ProjectListResponse)
    async def list_projects(request: Request) -> ProjectListResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        projects = await dependencies.list_projects.execute(actor)
        return ProjectListResponse(
            items=[ProjectResponse.from_domain(project) for project in projects]
        )

    @router.post("", response_model=ProjectResponse, status_code=201)
    async def create_project(
        request: Request,
        payload: CreateProjectRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> ProjectResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            async with dependencies.uow_factory():
                project = await dependencies.create_project.execute(
                    actor, CreateProjectCommand(name=payload.name)
                )
        except ProjectAccessDeniedError:
            return permission_denied()
        return ProjectResponse.from_domain(project)

    @router.get("/{project_id}", response_model=ProjectResponse)
    async def get_project(request: Request, project_id: UUID) -> ProjectResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            project = await dependencies.get_project.execute(actor, ProjectId(project_id))
        except ProjectNotFoundError:
            return project_not_found()
        return ProjectResponse.from_domain(project)

    @router.patch("/{project_id}", response_model=ProjectResponse)
    async def rename_project(
        request: Request,
        project_id: UUID,
        payload: RenameProjectRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> ProjectResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            async with dependencies.uow_factory():
                project = await dependencies.rename_project.execute(
                    actor,
                    RenameProjectCommand(
                        project_id=ProjectId(project_id),
                        name=payload.name,
                    ),
                )
        except ProjectNotFoundError:
            return project_not_found()
        except ProjectAccessDeniedError:
            return permission_denied()
        return ProjectResponse.from_domain(project)

    @router.post("/{project_id}/archive", response_model=ProjectResponse)
    async def archive_project(
        request: Request,
        project_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> ProjectResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            async with dependencies.uow_factory():
                project = await dependencies.archive_project.execute(actor, ProjectId(project_id))
        except ProjectNotFoundError:
            return project_not_found()
        except ProjectAccessDeniedError:
            return permission_denied()
        return ProjectResponse.from_domain(project)

    @router.get("/{project_id}/members", response_model=ProjectMembersResponse)
    async def list_members(
        request: Request, project_id: UUID
    ) -> ProjectMembersResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            project = await dependencies.list_members.execute(actor, ProjectId(project_id))
        except ProjectNotFoundError:
            return project_not_found()
        return members_response(project)

    @router.post("/{project_id}/members", response_model=ProjectMembersResponse)
    async def add_member(
        request: Request,
        project_id: UUID,
        payload: ProjectMemberRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> ProjectMembersResponse | JSONResponse:
        return await change_member(
            request,
            project_id,
            payload.user_id,
            payload.role,
            x_csrf_token,
            dependencies.add_member,
        )

    @router.patch(
        "/{project_id}/members/{user_id}",
        response_model=ProjectMembersResponse,
    )
    async def update_member(
        request: Request,
        project_id: UUID,
        user_id: UUID,
        payload: ProjectMemberUpdateRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> ProjectMembersResponse | JSONResponse:
        return await change_member(
            request,
            project_id,
            user_id,
            payload.role,
            x_csrf_token,
            dependencies.update_member,
        )

    async def change_member(
        request: Request,
        project_id: UUID,
        user_id: UUID,
        role: ProjectMemberRole,
        csrf_header: str | None,
        executor: ManageMemberExecutor,
    ) -> ProjectMembersResponse | JSONResponse:
        actor = await writer(request, csrf_header)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            async with dependencies.uow_factory():
                project = await executor.execute(
                    actor,
                    ProjectMemberCommand(
                        project_id=ProjectId(project_id),
                        user_id=UserId(user_id),
                        role=role,
                    ),
                )
        except ProjectNotFoundError:
            return project_not_found()
        except ProjectAccessDeniedError:
            return permission_denied()
        return members_response(project)

    @router.delete("/{project_id}/members/{user_id}", status_code=204)
    async def remove_member(
        request: Request,
        project_id: UUID,
        user_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> Response:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            async with dependencies.uow_factory():
                await dependencies.remove_member.execute(
                    actor, ProjectId(project_id), UserId(user_id)
                )
        except ProjectNotFoundError:
            return project_not_found()
        except ProjectAccessDeniedError:
            return permission_denied()
        return Response(status_code=204)

    return router


def members_response(project: Project) -> ProjectMembersResponse:
    return ProjectMembersResponse(
        items=[
            ProjectMemberResponse(user_id=user_id.value, role=role)
            for user_id, role in project.members().items()
        ]
    )


def project_not_found() -> JSONResponse:
    return problem_response(
        status=404,
        title="Project not found",
        detail="Project was not found",
    )


def permission_denied() -> JSONResponse:
    return problem_response(
        status=403,
        title="Permission denied",
        detail="Super administrator access is required",
    )


def csrf_failed() -> JSONResponse:
    return problem_response(
        status=403,
        title="CSRF validation failed",
        detail="A valid CSRF token is required",
    )


def authentication_required() -> JSONResponse:
    return problem_response(
        status=401,
        title="Authentication required",
        detail="A valid session is required",
    )


def problem_response(*, status: int, title: str, detail: str) -> JSONResponse:
    problem = ProblemDetails(title=title, status=status, detail=detail)
    return JSONResponse(
        status_code=status,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )
