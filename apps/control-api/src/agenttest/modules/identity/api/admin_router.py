from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse, Response

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.api.router import (
    CSRF_COOKIE_NAME,
    CsrfExecutor,
    CurrentUserExecutor,
    authentication_required,
    problem_response,
)
from agenttest.modules.identity.api.schemas import (
    CreateUserRequest,
    ResetPasswordRequest,
    UpdateUserRequest,
    UserPageResponse,
    UserResponse,
)
from agenttest.modules.identity.application.commands.create_user import CreateUserCommand
from agenttest.modules.identity.application.commands.reset_password import ResetPasswordCommand
from agenttest.modules.identity.application.commands.set_user_status import (
    ProtectedAdministratorError,
    SetUserStatusCommand,
)
from agenttest.modules.identity.application.commands.update_user import UpdateUserCommand
from agenttest.modules.identity.application.errors import (
    DuplicateEmailError,
    PermissionDeniedError,
    UserNotFoundError,
)
from agenttest.modules.identity.application.queries.current_user import InvalidSessionError
from agenttest.modules.identity.application.queries.list_users import UserPage
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email, UserId


class ListUsersExecutor(Protocol):
    async def execute(
        self, actor: User, cursor: UUID | None, limit: int
    ) -> UserPage: ...


class GetUserExecutor(Protocol):
    async def execute(self, actor: User, user_id: UserId) -> User: ...


class CreateUserExecutor(Protocol):
    async def execute(self, actor: User, command: CreateUserCommand) -> User: ...


class UpdateUserExecutor(Protocol):
    async def execute(self, actor: User, command: UpdateUserCommand) -> User: ...


class ResetPasswordExecutor(Protocol):
    async def execute(self, actor: User, command: ResetPasswordCommand) -> None: ...


class SetStatusExecutor(Protocol):
    async def execute(self, actor: User, command: SetUserStatusCommand) -> User: ...


class DeleteUserExecutor(Protocol):
    async def execute(self, actor: User, user_id: UserId) -> None: ...


@dataclass(frozen=True, slots=True)
class AdminApiDependencies:
    list_users: ListUsersExecutor
    get_user: GetUserExecutor
    create_user: CreateUserExecutor
    update_user: UpdateUserExecutor
    reset_password: ResetPasswordExecutor
    set_status: SetStatusExecutor
    delete_user: DeleteUserExecutor


def create_admin_router(
    dependencies: AdminApiDependencies,
    *,
    current_user: CurrentUserExecutor,
    csrf: CsrfExecutor,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(prefix="/system/users", tags=["system-users"])

    async def actor_for(request: Request) -> User | JSONResponse:
        session_token = request.cookies.get(settings.session_cookie_name)
        if not session_token:
            return authentication_required()
        try:
            return await current_user.execute(session_token)
        except InvalidSessionError:
            return authentication_required()

    async def require_write_access(
        request: Request,
        csrf_header: str | None,
    ) -> User | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        session_token = request.cookies.get(settings.session_cookie_name)
        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        if (
            not session_token
            or not csrf_header
            or not csrf_cookie
            or csrf_header != csrf_cookie
        ):
            return problem_response(
                status=403,
                title="CSRF validation failed",
                detail="A valid CSRF token is required",
            )
        try:
            await csrf.execute(session_token, csrf_header)
        except InvalidSessionError:
            return problem_response(
                status=403,
                title="CSRF validation failed",
                detail="A valid CSRF token is required",
            )
        return actor

    @router.get("", response_model=UserPageResponse)
    async def list_users(
        request: Request,
        cursor: UUID | None = None,
        limit: int = Query(default=50, ge=1, le=100),
    ) -> UserPageResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            page = await dependencies.list_users.execute(actor, cursor, limit)
        except PermissionDeniedError:
            return permission_denied()
        return UserPageResponse(
            items=[UserResponse.from_domain(item) for item in page.items],
            next_cursor=page.next_cursor,
        )

    @router.get("/{user_id}", response_model=UserResponse)
    async def get_user(request: Request, user_id: UUID) -> UserResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            user = await dependencies.get_user.execute(actor, UserId(user_id))
        except PermissionDeniedError:
            return permission_denied()
        except UserNotFoundError:
            return user_not_found()
        return UserResponse.from_domain(user)

    @router.post("", response_model=UserResponse, status_code=201)
    async def create_user(
        request: Request,
        payload: CreateUserRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> UserResponse | JSONResponse:
        actor = await require_write_access(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            user = await dependencies.create_user.execute(
                actor,
                CreateUserCommand(
                    email=Email(payload.email),
                    display_name=payload.display_name,
                    role=payload.role,
                    initial_password=payload.initial_password,
                ),
            )
        except PermissionDeniedError:
            return permission_denied()
        except (DuplicateEmailError, ValueError):
            return conflict("Email is already in use")
        return UserResponse.from_domain(user)

    @router.patch("/{user_id}", response_model=UserResponse)
    async def update_user(
        request: Request,
        user_id: UUID,
        payload: UpdateUserRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> UserResponse | JSONResponse:
        actor = await require_write_access(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            user = await dependencies.update_user.execute(
                actor,
                UpdateUserCommand(
                    user_id=UserId(user_id),
                    email=Email(payload.email),
                    display_name=payload.display_name,
                    role=payload.role,
                ),
            )
        except PermissionDeniedError:
            return permission_denied()
        except UserNotFoundError:
            return user_not_found()
        except ProtectedAdministratorError:
            return protected_administrator()
        except (DuplicateEmailError, ValueError):
            return conflict("Email is already in use")
        return UserResponse.from_domain(user)

    @router.post("/{user_id}/reset-password", status_code=204)
    async def reset_password(
        request: Request,
        user_id: UUID,
        payload: ResetPasswordRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> Response:
        actor = await require_write_access(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await dependencies.reset_password.execute(
                actor,
                ResetPasswordCommand(
                    user_id=UserId(user_id),
                    new_password=payload.new_password,
                ),
            )
        except PermissionDeniedError:
            return permission_denied()
        except UserNotFoundError:
            return user_not_found()
        return Response(status_code=204)

    async def change_status(
        request: Request,
        user_id: UUID,
        enabled: bool,
        csrf_header: str | None,
    ) -> UserResponse | JSONResponse:
        actor = await require_write_access(request, csrf_header)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            user = await dependencies.set_status.execute(
                actor,
                SetUserStatusCommand(user_id=UserId(user_id), enabled=enabled),
            )
        except PermissionDeniedError:
            return permission_denied()
        except UserNotFoundError:
            return user_not_found()
        except ProtectedAdministratorError:
            return protected_administrator()
        return UserResponse.from_domain(user)

    @router.post("/{user_id}/disable", response_model=UserResponse)
    async def disable_user(
        request: Request,
        user_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> UserResponse | JSONResponse:
        return await change_status(request, user_id, False, x_csrf_token)

    @router.post("/{user_id}/enable", response_model=UserResponse)
    async def enable_user(
        request: Request,
        user_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> UserResponse | JSONResponse:
        return await change_status(request, user_id, True, x_csrf_token)

    @router.delete("/{user_id}", status_code=204)
    async def delete_user(
        request: Request,
        user_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> Response:
        actor = await require_write_access(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await dependencies.delete_user.execute(actor, UserId(user_id))
        except PermissionDeniedError:
            return permission_denied()
        except UserNotFoundError:
            return user_not_found()
        except ProtectedAdministratorError:
            return protected_administrator()
        return Response(status_code=204)

    return router


def permission_denied() -> JSONResponse:
    return problem_response(
        status=403,
        title="Permission denied",
        detail="Super administrator access is required",
    )


def user_not_found() -> JSONResponse:
    return problem_response(status=404, title="User not found", detail="User was not found")


def conflict(detail: str) -> JSONResponse:
    return problem_response(status=409, title="Conflict", detail=detail)


def protected_administrator() -> JSONResponse:
    return conflict("The protected administrator operation is not allowed")
