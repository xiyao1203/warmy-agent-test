"""项目级超级测试 Agent 对话与历史 API。"""

from __future__ import annotations

import json
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.model_configs.public import (
    ModelDefaultMissingError,
    ModelRuntimeUnavailableError,
)
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.test_agent.application.conversation import (
    ConversationResponse,
    SuperAgentConversation,
)
from agenttest.modules.test_agent.application.orchestrator import (
    OrchestrationContext,
    SuperAgentOrchestrator,
)
from agenttest.modules.test_agent.application.ports import (
    ChatSessionRepository,
    OrchestrationRepository,
)
from agenttest.modules.test_agent.domain.entities import ChatSession, ChatSessionId
from agenttest.shared.api.auth_guard import require_actor, require_writer


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    session_id: UUID | None = None


class ConfirmationDecision(BaseModel):
    approved: bool


class ConversationPort(Protocol):
    async def respond(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        history: list[tuple[str, str]],
    ) -> ConversationResponse: ...


def create_test_agent_router(
    *,
    sessions: ChatSessionRepository,
    orchestration: OrchestrationRepository,
    actor_for,
    check_project,
    settings,
    conversation: SuperAgentConversation | ConversationPort,
    agent_orchestrator: SuperAgentOrchestrator | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/projects/{project_id}/test-agent", tags=["test-agent"])

    async def authorize(request: Request, project_id: UUID):
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor
        project_error = await _check_project(project_id, check_project)
        return project_error or actor

    async def authorize_write(
        request: Request,
        project_id: UUID,
        csrf: str | None,
    ):
        actor = await require_writer(request, actor_for, settings, csrf)
        if isinstance(actor, JSONResponse):
            return actor
        project_error = await _check_project(project_id, check_project)
        return project_error or actor

    @router.get("/sessions")
    async def list_sessions(request: Request, project_id: UUID):
        actor = await authorize(request, project_id)
        if isinstance(actor, JSONResponse):
            return actor
        items = await sessions.list_by_project(ProjectId(project_id))
        return {"items": [_session_summary(item) for item in items]}

    @router.post("/sessions", status_code=201)
    async def create_session(
        request: Request,
        project_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await authorize_write(request, project_id, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        session = ChatSession.create(project_id=project_id, created_by=actor.user_id.value)
        await sessions.save(session)
        await orchestration.append_event(
            ProjectId(project_id),
            session.session_id,
            "session.created",
            {"session_id": str(session.session_id.value)},
        )
        return _session_response(session, [])

    @router.get("/sessions/{session_id}")
    async def get_session(request: Request, project_id: UUID, session_id: UUID):
        actor = await authorize(request, project_id)
        if isinstance(actor, JSONResponse):
            return actor
        session = await sessions.get(ProjectId(project_id), ChatSessionId(session_id))
        if session is None:
            return JSONResponse(status_code=404, content={"detail": "会话不存在"})
        links = await orchestration.list_artifact_links(
            ProjectId(project_id), session.session_id
        )
        return _session_response(session, links)

    @router.delete("/sessions/{session_id}", status_code=204)
    async def archive_session(
        request: Request,
        project_id: UUID,
        session_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await authorize_write(request, project_id, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        session = await sessions.get(ProjectId(project_id), ChatSessionId(session_id))
        if session is None:
            return JSONResponse(status_code=404, content={"detail": "会话不存在"})
        session.archive()
        await sessions.save(session)
        return None

    async def send_message(
        actor: User,
        project_id: UUID,
        session: ChatSession,
        message: str,
    ):
        session.add_user_message(message)
        if session.title == "新对话":
            session.title = message[:40]
        await sessions.save(session)
        await orchestration.append_event(
            ProjectId(project_id),
            session.session_id,
            "message.started",
            {"role": "assistant"},
        )
        try:
            result = await conversation.respond(
                actor,
                ProjectId(project_id),
                history=[(item.role, item.content) for item in session.messages],
            )
        except ModelDefaultMissingError:
            await orchestration.append_event(
                ProjectId(project_id),
                session.session_id,
                "error",
                {"detail": "项目尚未配置测试 Agent 默认模型"},
            )
            return JSONResponse(
                status_code=409,
                content={"detail": "项目尚未配置测试 Agent 默认模型"},
            )
        except ModelRuntimeUnavailableError as error:
            await orchestration.append_event(
                ProjectId(project_id), session.session_id, "error", {"detail": str(error)}
            )
            return JSONResponse(status_code=503, content={"detail": str(error)})
        except ValueError as error:
            await orchestration.append_event(
                ProjectId(project_id), session.session_id, "error", {"detail": str(error)}
            )
            return JSONResponse(status_code=422, content={"detail": str(error)})

        await orchestration.append_event(
            ProjectId(project_id),
            session.session_id,
            "message.delta",
            {"content": result.content},
        )
        session.add_assistant_message(result.content)
        await sessions.save(session)
        if agent_orchestrator is not None:
            context = OrchestrationContext(actor, ProjectId(project_id), session.session_id.value)
            for index, intent in enumerate(result.actions):
                await orchestration.append_event(
                    ProjectId(project_id),
                    session.session_id,
                    "agent.delegated",
                    {
                        "child_agent": intent.child_agent,
                        "capability": intent.capability,
                    },
                )
                await agent_orchestrator.delegate(
                    context,
                    intent,
                    child_agent=intent.child_agent,
                    idempotency_key=(
                        f"chat:{session.session_id.value}:"
                        f"{session.messages[-1].sequence}:{index}:{intent.capability}"
                    ),
                )
        await orchestration.append_event(
            ProjectId(project_id),
            session.session_id,
            "message.completed",
            {
                "content": result.content,
                "total_tokens": result.total_tokens,
                "latency_ms": result.latency_ms,
            },
        )
        links = await orchestration.list_artifact_links(
            ProjectId(project_id), session.session_id
        )
        return _session_response(session, links)

    @router.post("/sessions/{session_id}/messages")
    async def post_message(
        request: Request,
        project_id: UUID,
        session_id: UUID,
        body: ChatRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await authorize_write(request, project_id, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        session = await sessions.get(ProjectId(project_id), ChatSessionId(session_id))
        if session is None:
            return JSONResponse(status_code=404, content={"detail": "会话不存在"})
        return await send_message(actor, project_id, session, body.message)

    @router.post("/chat")
    async def legacy_chat(
        request: Request,
        project_id: UUID,
        body: ChatRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await authorize_write(request, project_id, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        session = None
        if body.session_id is not None:
            session = await sessions.get(
                ProjectId(project_id), ChatSessionId(body.session_id)
            )
        if session is None:
            session = ChatSession.create(
                project_id=project_id, created_by=actor.user_id.value
            )
            await sessions.save(session)
        return await send_message(actor, project_id, session, body.message)

    @router.get("/sessions/{session_id}/events")
    async def stream_events(
        request: Request,
        project_id: UUID,
        session_id: UUID,
        last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    ):
        actor = await authorize(request, project_id)
        if isinstance(actor, JSONResponse):
            return actor
        session = await sessions.get(ProjectId(project_id), ChatSessionId(session_id))
        if session is None:
            return JSONResponse(status_code=404, content={"detail": "会话不存在"})
        after = int(last_event_id) if last_event_id and last_event_id.isdigit() else 0
        events = await orchestration.list_events(
            ProjectId(project_id), session.session_id, after=after
        )

        async def generate():
            for event in events:
                payload = json.dumps(event.payload, ensure_ascii=False, separators=(",", ":"))
                yield f"id: {event.sequence}\nevent: {event.event_type}\ndata: {payload}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @router.post("/confirmations/{confirmation_id}")
    async def decide_confirmation(
        request: Request,
        project_id: UUID,
        confirmation_id: UUID,
        body: ConfirmationDecision,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await authorize_write(request, project_id, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        if agent_orchestrator is None:
            return JSONResponse(
                status_code=503,
                content={"detail": "超级 Agent 编排器未配置"},
            )
        session_id = request.query_params.get("session_id")
        if not session_id:
            return JSONResponse(status_code=422, content={"detail": "session_id is required"})
        task = await agent_orchestrator.decide_confirmation(
            OrchestrationContext(actor, ProjectId(project_id), UUID(session_id)),
            confirmation_id,
            approved=body.approved,
        )
        return {
            "task_id": str(task.task_id),
            "status": task.status.value,
            "output": task.output,
            "error": task.error,
        }

    return router


async def _check_project(project_id: UUID, check_project) -> JSONResponse | None:
    try:
        await check_project(project_id)
    except ProjectNotFoundError:
        return JSONResponse(status_code=404, content={"detail": "项目不存在"})
    except InvalidSessionError:
        return JSONResponse(status_code=401, content={"detail": "认证失败"})
    return None


def _session_summary(session: ChatSession) -> dict[str, object]:
    return {
        "session_id": str(session.session_id.value),
        "title": session.title,
        "status": session.status.value,
        "updated_at": session.updated_at.isoformat(),
    }


def _session_response(session: ChatSession, links) -> dict[str, object]:
    return {
        **_session_summary(session),
        "messages": [
            {
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
            }
            for message in session.messages
        ],
        "artifacts": [
            {
                "type": link.artifact_type,
                "id": str(link.artifact_id),
                "relation": link.relation,
            }
            for link in links
        ],
        "plan_draft": session.plan_draft,
        "protocol_version": session.protocol_version,
    }
