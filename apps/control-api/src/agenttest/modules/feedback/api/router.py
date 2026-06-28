"""反馈 API 路由。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from agenttest.bootstrap.settings import Settings
from agenttest.modules.feedback.api.schemas import (
    CreateFeedbackRequest,
    FeedbackResponse,
    FeedbackType,
)
from agenttest.modules.identity.api.router import authentication_required
from agenttest.modules.identity.application.queries.current_user import InvalidSessionError
from agenttest.modules.identity.domain.entities import User
from agenttest.shared.application.uow import UnitOfWorkFactory, null_uow_factory


class CurrentUserExecutor(Protocol):
    async def execute(self, session_token: str) -> User: ...


class CreateFeedbackExecutor(Protocol):
    async def execute(
        self,
        *,
        feedback_type: FeedbackType,
        title: str,
        description: str,
        contact: str | None,
        user_id: UUID | None,
    ) -> UUID: ...


@dataclass(frozen=True, slots=True)
class FeedbackApiDependencies:
    current_user: CurrentUserExecutor
    create_feedback: CreateFeedbackExecutor
    uow_factory: UnitOfWorkFactory = null_uow_factory


def create_feedback_router(
    dependencies: FeedbackApiDependencies,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(prefix="/feedback", tags=["feedback"])

    @router.post("", response_model=FeedbackResponse, status_code=201)
    async def create_feedback(
        request: Request,
        payload: CreateFeedbackRequest,
    ) -> FeedbackResponse | JSONResponse:
        # 尝试获取当前用户（可选登录）
        user_id = None
        session_token = request.cookies.get(settings.session_cookie_name)
        if session_token:
            try:
                user = await dependencies.current_user.execute(session_token)
                user_id = user.user_id.value
            except InvalidSessionError:
                pass  # 允许匿名反馈

        try:
            feedback_id = await dependencies.create_feedback.execute(
                feedback_type=payload.type,
                title=payload.title,
                description=payload.description,
                contact=payload.contact,
                user_id=user_id,
            )
        except ValueError as e:
            return JSONResponse(
                status_code=400,
                content={"detail": str(e)},
            )

        from datetime import UTC, datetime

        return FeedbackResponse(
            id=feedback_id,
            type=payload.type,
            title=payload.title,
            description=payload.description,
            contact=payload.contact,
            user_id=user_id,
            created_at=datetime.now(UTC).isoformat(),
        )

    return router
