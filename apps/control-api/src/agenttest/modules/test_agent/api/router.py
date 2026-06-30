"""项目级测试 Agent 对话 API。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.model_configs.public import (
    ModelDefaultMissingError,
    ModelRuntimeUnavailableError,
)
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.test_agent.application.model_planner import (
    InvalidModelPlanError,
    ModelTestPlanGenerator,
)
from agenttest.modules.test_agent.application.ports import ChatSessionRepository
from agenttest.modules.test_agent.domain.entities import ChatSession, ChatSessionId
from agenttest.shared.api.auth_guard import require_actor, require_writer


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    session_id: UUID | None = None


class ConfirmRequest(BaseModel):
    session_id: UUID


def create_test_agent_router(
    *,
    sessions: ChatSessionRepository,
    actor_for,
    check_project,
    settings,
    plan_generator: ModelTestPlanGenerator,
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/test-agent",
        tags=["test-agent"],
    )

    @router.post("/chat")
    async def chat(
        request: Request,
        project_id: UUID,
        body: ChatRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        project_error = await _check_project(project_id, check_project)
        if project_error is not None:
            return project_error

        session = None
        if body.session_id is not None:
            session = await sessions.get(
                ProjectId(project_id),
                ChatSessionId(body.session_id),
            )
            if session is None:
                return JSONResponse(status_code=404, content={"detail": "会话不存在"})
        if session is None:
            session = ChatSession.create(
                project_id=project_id,
                created_by=actor.user_id.value,
            )

        session.add_user_message(body.message)
        await sessions.save(session)
        try:
            plan_draft = await plan_generator.generate(
                actor,
                ProjectId(project_id),
                body.message,
            )
        except ModelDefaultMissingError:
            return JSONResponse(
                status_code=409,
                content={"detail": "项目尚未配置测试 Agent 默认模型"},
            )
        except InvalidModelPlanError as error:
            return JSONResponse(status_code=422, content={"detail": str(error)})
        except ModelRuntimeUnavailableError as error:
            return JSONResponse(status_code=503, content={"detail": str(error)})

        response_text = (
            f"已生成测试计划草稿，包含 {plan_draft.get('estimated_cases', 0)} 个用例，"
            f"预计执行 {plan_draft.get('estimated_duration_min', 0)} 分钟。"
        )
        session.add_assistant_message(response_text, plan_draft=plan_draft)
        await sessions.save(session)
        return _session_response(session)

    @router.post("/confirm")
    async def confirm(
        request: Request,
        project_id: UUID,
        body: ConfirmRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        project_error = await _check_project(project_id, check_project)
        if project_error is not None:
            return project_error
        session = await sessions.get(ProjectId(project_id), ChatSessionId(body.session_id))
        if session is None:
            return JSONResponse(status_code=404, content={"detail": "会话不存在"})
        try:
            plan = session.confirm_plan()
        except ValueError as error:
            return JSONResponse(status_code=422, content={"detail": str(error)})
        session.add_assistant_message("计划草稿已确认。请保存为测试计划并发布版本后再启动运行。")
        await sessions.save(session)
        return {
            "session_id": str(session.session_id.value),
            "status": session.status.value,
            "plan": plan,
            "message": "计划草稿已确认，尚未启动运行",
        }

    @router.get("/sessions/{session_id}")
    async def get_session(
        request: Request,
        project_id: UUID,
        session_id: UUID,
    ):
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor
        session = await sessions.get(ProjectId(project_id), ChatSessionId(session_id))
        if session is None:
            return JSONResponse(status_code=404, content={"detail": "会话不存在"})
        return _session_response(session)

    return router


async def _check_project(project_id: UUID, check_project) -> JSONResponse | None:
    try:
        await check_project(project_id)
    except ProjectNotFoundError:
        return JSONResponse(status_code=404, content={"detail": "项目不存在"})
    except InvalidSessionError:
        return JSONResponse(status_code=401, content={"detail": "认证失败"})
    return None


def _session_response(session: ChatSession) -> dict[str, object]:
    return {
        "session_id": str(session.session_id.value),
        "messages": [
            {
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
            }
            for message in session.messages
        ],
        "plan_draft": session.plan_draft,
        "status": session.status.value,
    }
