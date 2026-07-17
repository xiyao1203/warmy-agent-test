from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.api.client_ip import resolve_client_ip
from agenttest.modules.identity.api.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    UpdateProfileRequest,
    UserResponse,
)
from agenttest.modules.identity.application.commands.login import (
    InvalidCredentialsError,
    LoginCommand,
    LoginResult,
)
from agenttest.modules.identity.application.errors import DuplicateEmailError
from agenttest.modules.identity.application.queries.current_user import InvalidSessionError
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email
from agenttest.shared.api.problem_details import ProblemDetails
from agenttest.shared.application.uow import UnitOfWorkFactory, null_uow_factory

CSRF_COOKIE_NAME = "agenttest_csrf"


class LoginExecutor(Protocol):
    async def execute(self, command: LoginCommand) -> LoginResult: ...


class CurrentUserExecutor(Protocol):
    async def execute(self, session_token: str) -> User: ...


class LogoutExecutor(Protocol):
    async def execute(self, session_token: str) -> None: ...


class CsrfExecutor(Protocol):
    async def execute(self, session_token: str, csrf_token: str) -> None: ...


class UpdateProfileExecutor(Protocol):
    async def execute(self, user: User, display_name: str, email: Email) -> User: ...


class ChangePasswordExecutor(Protocol):
    async def execute(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None: ...


class UnavailableUpdateProfile:
    async def execute(self, user: User, display_name: str, email: Email) -> User:
        raise RuntimeError("Profile updates are not configured")


class UnavailableChangePassword:
    async def execute(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        raise RuntimeError("Password changes are not configured")


@dataclass(frozen=True, slots=True)
class AuthApiDependencies:
    login: LoginExecutor
    current_user: CurrentUserExecutor
    logout: LogoutExecutor
    csrf: CsrfExecutor
    update_profile: UpdateProfileExecutor = field(default_factory=UnavailableUpdateProfile)
    change_password: ChangePasswordExecutor = field(default_factory=UnavailableChangePassword)
    uow_factory: UnitOfWorkFactory = null_uow_factory


def create_auth_router(
    dependencies: AuthApiDependencies,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["identity"])

    @router.post("/login", response_model=UserResponse)
    async def login(
        payload: LoginRequest,
        response: Response,
        request: Request,
    ) -> UserResponse | JSONResponse:
        direct_peer = request.client.host if request.client is not None else "0.0.0.0"
        source_ip = resolve_client_ip(
            direct_peer,
            request.headers.get("X-Forwarded-For"),
            settings.trusted_proxy_networks,
        )
        try:
            async with dependencies.uow_factory():
                result = await dependencies.login.execute(
                    LoginCommand(
                        email=Email(payload.email),
                        password=payload.password,
                        source_ip=source_ip,
                    )
                )
        except (InvalidCredentialsError, ValueError):
            return problem_response(
                status=401,
                title="Authentication failed",
                detail="Invalid email or password",
            )
        response.set_cookie(
            settings.session_cookie_name,
            result.session_token,
            max_age=settings.session_ttl_seconds,
            secure=settings.session_cookie_secure,
            httponly=True,
            samesite="lax",
            path="/",
        )
        response.set_cookie(
            CSRF_COOKIE_NAME,
            result.csrf_token,
            max_age=settings.session_ttl_seconds,
            secure=settings.session_cookie_secure,
            httponly=False,
            samesite="lax",
            path="/",
        )
        return UserResponse.from_domain(result.user)

    @router.get("/me", response_model=UserResponse)
    async def current_user(request: Request) -> UserResponse | JSONResponse:
        session_token = request.cookies.get(settings.session_cookie_name)
        if not session_token:
            return authentication_required()
        try:
            user = await dependencies.current_user.execute(session_token)
        except InvalidSessionError:
            return authentication_required()
        return UserResponse.from_domain(user)

    @router.patch("/me", response_model=UserResponse)
    async def update_profile(
        request: Request,
        payload: UpdateProfileRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> UserResponse | JSONResponse:
        session_token = request.cookies.get(settings.session_cookie_name)
        if not session_token:
            return authentication_required()
        csrf_error = await validate_csrf(
            request=request,
            session_token=session_token,
            csrf_header=x_csrf_token,
            csrf=dependencies.csrf,
        )
        if csrf_error is not None:
            return csrf_error
        try:
            user = await dependencies.current_user.execute(session_token)
            async with dependencies.uow_factory():
                updated_user = await dependencies.update_profile.execute(
                    user=user,
                    display_name=payload.display_name,
                    email=Email(payload.email),
                )
        except InvalidSessionError:
            return authentication_required()
        except DuplicateEmailError:
            return problem_response(
                status=409,
                title="Email already in use",
                detail="The email address is already assigned to another user",
            )
        except ValueError as error:
            return problem_response(
                status=400,
                title="Validation error",
                detail=str(error),
            )
        return UserResponse.from_domain(updated_user)

    @router.post("/change-password", status_code=204)
    async def change_password(
        request: Request,
        payload: ChangePasswordRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> Response:
        session_token = request.cookies.get(settings.session_cookie_name)
        if not session_token:
            return authentication_required()
        csrf_error = await validate_csrf(
            request=request,
            session_token=session_token,
            csrf_header=x_csrf_token,
            csrf=dependencies.csrf,
        )
        if csrf_error is not None:
            return csrf_error
        try:
            user = await dependencies.current_user.execute(session_token)
            async with dependencies.uow_factory():
                await dependencies.change_password.execute(
                    user=user,
                    current_password=payload.current_password,
                    new_password=payload.new_password,
                )
        except InvalidSessionError:
            return authentication_required()
        except InvalidCredentialsError:
            return problem_response(
                status=400,
                title="Password change failed",
                detail="Current password is incorrect",
            )
        except ValueError as error:
            return problem_response(
                status=400,
                title="Validation error",
                detail=str(error),
            )
        return Response(status_code=204)

    @router.post("/logout", status_code=204)
    async def logout(
        request: Request,
        x_csrf_token: str | None = Header(default=None),
    ) -> Response:
        session_token = request.cookies.get(settings.session_cookie_name)
        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        if not session_token:
            return authentication_required()
        if not x_csrf_token or not csrf_cookie or x_csrf_token != csrf_cookie:
            return problem_response(
                status=403,
                title="CSRF validation failed",
                detail="A valid CSRF token is required",
            )
        try:
            await dependencies.csrf.execute(session_token, x_csrf_token)
            async with dependencies.uow_factory():
                await dependencies.logout.execute(session_token)
        except InvalidSessionError:
            return problem_response(
                status=403,
                title="CSRF validation failed",
                detail="A valid CSRF token is required",
            )
        response = Response(status_code=204)
        response.delete_cookie(
            settings.session_cookie_name,
            secure=settings.session_cookie_secure,
            httponly=True,
            samesite="lax",
            path="/",
        )
        response.delete_cookie(
            CSRF_COOKIE_NAME,
            secure=settings.session_cookie_secure,
            httponly=False,
            samesite="lax",
            path="/",
        )
        return response

    return router


def authentication_required() -> JSONResponse:
    return problem_response(
        status=401,
        title="Authentication required",
        detail="A valid session is required",
    )


async def validate_csrf(
    *,
    request: Request,
    session_token: str,
    csrf_header: str | None,
    csrf: CsrfExecutor,
) -> JSONResponse | None:
    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
    if not csrf_header or not csrf_cookie or csrf_header != csrf_cookie:
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
    return None


def problem_response(*, status: int, title: str, detail: str) -> JSONResponse:
    problem = ProblemDetails(title=title, status=status, detail=detail)
    return JSONResponse(
        status_code=status,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )
