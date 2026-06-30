"""用户设置 API 路由。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import (
    CsrfExecutor,
    InvalidSessionError,
    User,
    authentication_required,
    problem_response,
    validate_csrf,
)
from agenttest.modules.user_settings.api.schemas import (
    UpdateSettingsRequest,
    UserSettingsResponse,
)
from agenttest.modules.user_settings.domain.entities import UserSettings
from agenttest.modules.user_settings.domain.value_objects import Language, Theme
from agenttest.shared.application.uow import UnitOfWorkFactory, null_uow_factory


class CurrentUserExecutor(Protocol):
    async def execute(self, session_token: str) -> User: ...


class GetSettingsExecutor(Protocol):
    async def execute(self, user_id: str) -> UserSettings | None: ...


class UpdateSettingsExecutor(Protocol):
    async def execute(
        self,
        user_id: str,
        *,
        theme: Theme | None = None,
        language: Language | None = None,
        email_notifications: bool | None = None,
        push_notifications: bool | None = None,
        test_complete_notifications: bool | None = None,
    ) -> UserSettings: ...


@dataclass(frozen=True, slots=True)
class UserSettingsApiDependencies:
    current_user: CurrentUserExecutor
    get_settings: GetSettingsExecutor
    update_settings: UpdateSettingsExecutor
    csrf: CsrfExecutor
    uow_factory: UnitOfWorkFactory = null_uow_factory


def create_user_settings_router(
    dependencies: UserSettingsApiDependencies,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(prefix="/users/me/settings", tags=["user-settings"])

    @router.get("", response_model=UserSettingsResponse)
    async def get_settings(request: Request) -> UserSettingsResponse | JSONResponse:
        session_token = request.cookies.get(settings.session_cookie_name)
        if not session_token:
            return authentication_required()
        try:
            user = await dependencies.current_user.execute(session_token)
        except InvalidSessionError:
            return authentication_required()

        user_settings = await dependencies.get_settings.execute(str(user.user_id.value))
        if user_settings is None:
            # 返回默认设置
            user_settings = UserSettings(user_id=user.user_id.value)
        return UserSettingsResponse.from_domain(user_settings)

    @router.patch("", response_model=UserSettingsResponse)
    async def update_settings(
        request: Request,
        payload: UpdateSettingsRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> UserSettingsResponse | JSONResponse:
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
        except InvalidSessionError:
            return authentication_required()

        try:
            updated_settings = await dependencies.update_settings.execute(
                user_id=str(user.user_id.value),
                theme=payload.theme,
                language=payload.language,
                email_notifications=payload.email_notifications,
                push_notifications=payload.push_notifications,
                test_complete_notifications=payload.test_complete_notifications,
            )
        except ValueError as e:
            return problem_response(status=400, title="Validation error", detail=str(e))
        return UserSettingsResponse.from_domain(updated_settings)

    return router
