"""项目级被测 Agent 对话测试 API。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agenttest.modules.agents.public import AgentId, AgentVersionId
from agenttest.modules.environments.public import EnvironmentTemplateId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.application.target_chat import TargetChatService
from agenttest.shared.api.auth_guard import require_actor, require_writer


class CreateTargetChatRequest(BaseModel):
    agent_version_id: UUID
    environment_template_id: UUID | None = None


class SendTargetMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)


def create_target_chat_router(
    *, service: TargetChatService, repository, agents, environments, actor_for, settings
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/test-agent/target-chats",
        tags=["target-agent-chat"],
    )

    @router.get("")
    async def list_sessions(request: Request, project_id: UUID):
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor
        items = await repository.list_sessions(ProjectId(project_id))
        return {"items": [_session(item) for item in items]}

    @router.post("", status_code=201)
    async def create_session(
        request: Request,
        project_id: UUID,
        body: CreateTargetChatRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            version = await agents.get_version.execute(actor, AgentVersionId(body.agent_version_id))
            agent = await agents.get_agent.execute(actor, AgentId(version.agent_id.value))
            environment = (
                await environments.get_template.execute(
                    actor, EnvironmentTemplateId(body.environment_template_id)
                )
                if body.environment_template_id
                else None
            )
            session = await service.create(
                actor=actor,
                project_id=ProjectId(project_id),
                version=version,
                version_project_id=agent.project_id,
                environment=environment,
            )
        except (ValueError, LookupError) as error:
            return JSONResponse(status_code=422, content={"detail": str(error)})
        return _session(session)

    @router.get("/{session_id}")
    async def get_session(request: Request, project_id: UUID, session_id: UUID):
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor
        session = await repository.get_session(ProjectId(project_id), session_id)
        if session is None:
            return JSONResponse(status_code=404, content={"detail": "被测 Agent 会话不存在"})
        return _session(session)

    @router.post("/{session_id}/messages")
    async def send_message(
        request: Request,
        project_id: UUID,
        session_id: UUID,
        body: SendTargetMessageRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        session = await repository.get_session(ProjectId(project_id), session_id)
        if session is None:
            return JSONResponse(status_code=404, content={"detail": "被测 Agent 会话不存在"})
        version = await agents.get_version.execute(actor, AgentVersionId(session.agent_version_id))
        environment = (
            await environments.get_template.execute(
                actor, EnvironmentTemplateId(session.environment_template_id)
            )
            if session.environment_template_id
            else None
        )
        try:
            turn = await service.send(
                project_id=ProjectId(project_id),
                session=session,
                version=version,
                environment=environment,
                message=body.message,
            )
        except Exception:
            return JSONResponse(status_code=502, content={"detail": "被测 Agent 调用失败"})
        return _turn(turn)

    return router


def _session(session) -> dict[str, object]:
    return {
        "session_id": str(session.session_id),
        "project_id": str(session.project_id),
        "agent_version_id": str(session.agent_version_id),
        "environment_template_id": (
            str(session.environment_template_id) if session.environment_template_id else None
        ),
        "status": session.status,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "turns": [_turn(item) for item in session.turns],
    }


def _turn(turn) -> dict[str, object]:
    return {
        "turn_id": str(turn.turn_id),
        "sequence": turn.sequence,
        "input": turn.input,
        "output": turn.output,
        "trace": turn.trace,
        "scores": turn.scores,
        "duration_ms": turn.duration_ms,
        "token_usage": turn.token_usage,
        "error": turn.error,
        "created_at": turn.created_at.isoformat(),
    }
