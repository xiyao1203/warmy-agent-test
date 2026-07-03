"""项目级超级测试 Agent 对话与历史 API。"""

from __future__ import annotations

import asyncio
import json
from typing import Protocol
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.model_configs.public import (
    ModelDefaultMissingError,
    ModelRuntimeUnavailableError,
    ModelStreamCallback,
    StreamContext,
)
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.modules.test_agent.application.conversation import (
    ConversationResponse,
    SuperAgentConversation,
)
from agenttest.modules.test_agent.application.generations import GenerationCoordinator
from agenttest.modules.test_agent.application.orchestrator import (
    OrchestrationContext,
    SuperAgentOrchestrator,
)
from agenttest.modules.test_agent.application.ports import (
    ChatSessionRepository,
    OrchestrationRepository,
)
from agenttest.modules.test_agent.domain.entities import (
    AgentEvent,
    AgentTask,
    ChatGeneration,
    ChatSession,
    ChatSessionId,
    TaskStatus,
)
from agenttest.shared.api.auth_guard import require_actor, require_writer


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20_000)
    generation_id: UUID = Field(default_factory=uuid4)


class RegenerateRequest(BaseModel):
    message: str | None = Field(default=None, min_length=1, max_length=20_000)


class EditMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)


class ConfirmationDecision(BaseModel):
    approved: bool


class BatchConfirmationDecision(BaseModel):
    confirmation_ids: list[UUID] = Field(min_length=1, max_length=50)
    approved: bool


class ModelDeltaCallback(BaseModel):
    content: str = Field(min_length=1, max_length=100_000)
    event_type: str = Field(default="message.delta", max_length=64)


class ConversationPort(Protocol):
    async def respond(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        history: list[tuple[str, str]],
        stream_callback: ModelStreamCallback | None = None,
        reasoning_stream_callback: ModelStreamCallback | None = None,
        action_context: dict[str, object] | None = None,
        stream_context: StreamContext | None = None,
    ) -> ConversationResponse: ...

    async def generate_title(
        self,
        actor: User,
        project_id: ProjectId,
        history: list[tuple[str, str]],
    ) -> str: ...


def create_test_agent_router(
    *,
    sessions: ChatSessionRepository,
    orchestration: OrchestrationRepository,
    actor_for,
    check_project,
    settings,
    conversation: SuperAgentConversation | ConversationPort,
    agent_orchestrator: SuperAgentOrchestrator | None = None,
    generation_coordinator: GenerationCoordinator | None = None,
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
        created_event = await orchestration.append_event(
            ProjectId(project_id),
            session.session_id,
            "session.created",
            {"session_id": str(session.session_id.value)},
        )
        return _session_response(session, [], [created_event], None)

    @router.get("/sessions/{session_id}")
    async def get_session(request: Request, project_id: UUID, session_id: UUID):
        actor = await authorize(request, project_id)
        if isinstance(actor, JSONResponse):
            return actor
        session = await sessions.get(ProjectId(project_id), ChatSessionId(session_id))
        if session is None:
            return JSONResponse(status_code=404, content={"detail": "会话不存在"})
        links = await orchestration.list_artifact_links(ProjectId(project_id), session.session_id)
        events = await orchestration.list_events(ProjectId(project_id), session.session_id, after=0)
        active = (
            await generation_coordinator.get_active(ProjectId(project_id), session.session_id)
            if generation_coordinator is not None
            else None
        )
        return _session_response(session, links, events, active)

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
        generation_id: UUID,
        add_user_message: bool = True,
    ):
        coordinator = generation_coordinator
        generation = None
        stream_context = None
        if coordinator is not None:
            try:
                generation = await coordinator.begin(
                    ProjectId(project_id), session.session_id, generation_id
                )
                generation = await coordinator.start(generation)
                stream_context = StreamContext(workflow_id=generation.workflow_id)
            except ValueError as error:
                return JSONResponse(status_code=409, content={"detail": str(error)})
        if add_user_message:
            session.add_user_message(message)
            await sessions.save(session)
        await orchestration.append_event(
            ProjectId(project_id),
            session.session_id,
            "message.started",
            {"role": "assistant", "generation_id": str(generation_id)},
            generation_id=generation_id if generation is not None else None,
        )
        # Build action_context from existing artifact links so the LLM
        # can reference IDs produced by earlier actions in the session.
        existing_links = await orchestration.list_artifact_links(
            ProjectId(project_id), session.session_id
        )
        action_context: dict[str, object] = {}
        if existing_links:
            action_context["_previous_artifacts"] = [
                {"type": link.artifact_type, "id": str(link.artifact_id)} for link in existing_links
            ]
        try:
            result = await conversation.respond(
                actor,
                ProjectId(project_id),
                history=[(item.role, item.content) for item in session.messages],
                stream_callback=ModelStreamCallback(
                    url=(
                        f"{str(settings.control_api_base_url).rstrip('/')}/api/v1/"
                        f"projects/{project_id}/test-agent/sessions/"
                        f"{session.session_id.value}/model-events"
                        f"?generation_id={generation_id}"
                    ),
                    internal_token=settings.internal_api_token,
                ),
                reasoning_stream_callback=ModelStreamCallback(
                    url=(
                        f"{str(settings.control_api_base_url).rstrip('/')}/api/v1/"
                        f"projects/{project_id}/test-agent/sessions/"
                        f"{session.session_id.value}/model-events/reasoning"
                        f"?generation_id={generation_id}"
                    ),
                    internal_token=settings.internal_api_token,
                ),
                action_context=action_context if action_context else None,
                stream_context=stream_context,
            )
        except ModelDefaultMissingError:
            if generation is not None and coordinator is not None:
                await coordinator.fail(generation, "项目尚未配置测试 Agent 默认模型")
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
            if generation is not None and coordinator is not None:
                await coordinator.fail(generation, str(error))
            await orchestration.append_event(
                ProjectId(project_id), session.session_id, "error", {"detail": str(error)}
            )
            return JSONResponse(status_code=503, content={"detail": str(error)})
        except ValueError as error:
            if generation is not None and coordinator is not None:
                await coordinator.fail(generation, str(error))
            await orchestration.append_event(
                ProjectId(project_id), session.session_id, "error", {"detail": str(error)}
            )
            return JSONResponse(status_code=422, content={"detail": str(error)})

        delegated_tasks: list[AgentTask] = []
        if not result.actions:
            await orchestration.append_event(
                ProjectId(project_id),
                session.session_id,
                "agent.reasoning",
                {"content": ""},
                generation_id=generation_id if generation is not None else None,
            )
        if agent_orchestrator is not None:
            context = OrchestrationContext(
                actor,
                ProjectId(project_id),
                session.session_id.value,
                generation_id=generation_id if generation is not None else None,
            )
            # Emit reasoning events before delegating actions (Codex-style
            # expandable thinking disclosure).
            for i, intent in enumerate(result.actions):
                if intent.rationale:
                    await orchestration.append_event(
                        ProjectId(project_id),
                        session.session_id,
                        "agent.reasoning",
                        {
                            "step": i + 1,
                            "total": len(result.actions),
                            "capability": intent.capability,
                            "child_agent": intent.child_agent,
                            "content": intent.rationale,
                        },
                        generation_id=generation_id if generation is not None else None,
                    )
            for index, intent in enumerate(result.actions):
                delegated_tasks.append(
                    await agent_orchestrator.delegate(
                        context,
                        intent,
                        child_agent=intent.child_agent,
                        idempotency_key=(
                            f"chat:{session.session_id.value}:"
                            f"{session.messages[-1].sequence}:{index}:{intent.capability}"
                        ),
                    )
                )
        if any(task.status is TaskStatus.WAITING_CONFIRMATION for task in delegated_tasks):
            await orchestration.append_event(
                ProjectId(project_id),
                session.session_id,
                "generation.waiting_confirmation",
                {"generation_id": str(generation_id)},
                generation_id=generation_id if generation is not None else None,
            )
            links = await orchestration.list_artifact_links(
                ProjectId(project_id), session.session_id
            )
            events = await orchestration.list_events(
                ProjectId(project_id), session.session_id, after=0
            )
            return _session_response(session, links, events, generation)

        final_content = _content_with_task_results(result.content, delegated_tasks)
        session.add_assistant_message(final_content)
        if session.title == "新对话" and session.messages:
            session.title = _instant_conversation_title(message)
        await sessions.save(session)
        await orchestration.append_event(
            ProjectId(project_id),
            session.session_id,
            "message.completed",
            {
                "content": final_content,
                "total_tokens": result.total_tokens,
                "latency_ms": result.latency_ms,
                "generation_id": str(generation_id),
            },
            generation_id=generation_id if generation is not None else None,
        )
        if generation is not None and coordinator is not None:
            if result.cancelled:
                await coordinator.mark_cancelled(generation, final_content)
            else:
                await coordinator.complete(generation, final_content)
        links = await orchestration.list_artifact_links(ProjectId(project_id), session.session_id)
        events = await orchestration.list_events(ProjectId(project_id), session.session_id, after=0)
        return _session_response(session, links, events, None)

    @router.post("/sessions/{session_id}/model-events", include_in_schema=False)
    async def append_model_delta(
        project_id: UUID,
        session_id: UUID,
        body: ModelDeltaCallback,
        x_internal_token: str | None = Header(default=None),
        generation_id: UUID | None = None,
    ):
        if x_internal_token != settings.internal_api_token:
            return JSONResponse(status_code=401, content={"detail": "Invalid internal token"})
        session = await sessions.get(ProjectId(project_id), ChatSessionId(session_id))
        if session is None:
            return JSONResponse(status_code=404, content={"detail": "会话不存在"})
        event_type = body.event_type if body.event_type else "message.delta"
        event = await orchestration.append_event(
            ProjectId(project_id),
            session.session_id,
            event_type,
            {"content": body.content},
            generation_id=generation_id,
        )
        return {"sequence": event.sequence}

    @router.post("/sessions/{session_id}/model-events/reasoning", include_in_schema=False)
    async def append_reasoning_delta(
        project_id: UUID,
        session_id: UUID,
        body: ModelDeltaCallback,
        x_internal_token: str | None = Header(default=None),
        generation_id: UUID | None = None,
    ):
        if x_internal_token != settings.internal_api_token:
            return JSONResponse(status_code=401, content={"detail": "Invalid internal token"})
        session = await sessions.get(ProjectId(project_id), ChatSessionId(session_id))
        if session is None:
            return JSONResponse(status_code=404, content={"detail": "会话不存在"})
        event = await orchestration.append_event(
            ProjectId(project_id),
            session.session_id,
            "agent.reasoning_delta",
            {"content": body.content},
            generation_id=generation_id,
        )
        return {"sequence": event.sequence}

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
        return await send_message(actor, project_id, session, body.message, body.generation_id)

    @router.post("/sessions/{session_id}/messages/regenerate")
    async def regenerate_message(
        request: Request,
        project_id: UUID,
        session_id: UUID,
        body: RegenerateRequest | None = None,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await authorize_write(request, project_id, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        session = await sessions.get(ProjectId(project_id), ChatSessionId(session_id))
        if session is None:
            return JSONResponse(status_code=404, content={"detail": "会话不存在"})

        messages = session.messages
        # Find the last user message and remove the last assistant response
        if not messages:
            return JSONResponse(status_code=422, content={"detail": "没有可重生成的消息"})

        last_user_msg = None
        for m in reversed(messages):
            if m.role == "user":
                last_user_msg = m
                break
        if last_user_msg is None:
            return JSONResponse(status_code=422, content={"detail": "没有可重生成的用户消息"})

        # Get the override message or use the original
        message = (body.message if body and body.message else None) or last_user_msg.content

        # Remove the last assistant message if it exists after the last user message
        last_msg = messages[-1]
        if last_msg.role == "assistant" and last_msg.sequence > last_user_msg.sequence:
            session.remove_messages_from(last_msg.sequence)
            await sessions.save(session)

        # If the message content changed (edit), update the user message too
        if message != last_user_msg.content:
            session.remove_messages_from(last_user_msg.sequence)
            session.add_user_message(message)
            await sessions.save(session)

        return await send_message(
            actor,
            project_id,
            session,
            message,
            uuid4(),
            add_user_message=False,
        )

    @router.get("/sessions/{session_id}/events")
    async def stream_events(
        request: Request,
        project_id: UUID,
        session_id: UUID,
        last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
        after: int | None = None,
    ):
        actor = await authorize(request, project_id)
        if isinstance(actor, JSONResponse):
            return actor
        session = await sessions.get(ProjectId(project_id), ChatSessionId(session_id))
        if session is None:
            return JSONResponse(status_code=404, content={"detail": "会话不存在"})
        if last_event_id and last_event_id.isdigit():
            cursor = int(last_event_id)
        elif after is not None:
            cursor = max(0, after)
        else:
            cursor = 0

        async def generate():
            last_seq = cursor
            idle_ticks = 0
            ready_payload = json.dumps({"cursor": cursor}, separators=(",", ":"))
            yield f"event: stream.ready\ndata: {ready_payload}\n\n"
            while idle_ticks < 40:
                events = await orchestration.list_events(
                    ProjectId(project_id), session.session_id, after=last_seq
                )
                if events:
                    idle_ticks = 0
                    for event in events:
                        last_seq = max(last_seq, event.sequence)
                        payload = json.dumps(
                            event.payload, ensure_ascii=False, separators=(",", ":")
                        )
                        yield (
                            f"id: {event.sequence}\nevent: {event.event_type}\ndata: {payload}\n\n"
                        )
                else:
                    idle_ticks += 1
                if await request.is_disconnected():
                    return
                await asyncio.sleep(0.5)

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @router.post("/sessions/{session_id}/generations/{generation_id}/cancel")
    async def cancel_generation(
        request: Request,
        project_id: UUID,
        session_id: UUID,
        generation_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await authorize_write(request, project_id, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        if generation_coordinator is None:
            return JSONResponse(status_code=503, content={"detail": "生成协调器未配置"})
        try:
            generation = await generation_coordinator.cancel(
                ProjectId(project_id), ChatSessionId(session_id), generation_id
            )
        except ValueError as error:
            return JSONResponse(status_code=404, content={"detail": str(error)})
        return _generation_response(generation)

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
            OrchestrationContext(
                actor,
                ProjectId(project_id),
                UUID(session_id),
                generation_id=(
                    UUID(request.query_params["generation_id"])
                    if request.query_params.get("generation_id")
                    else None
                ),
            ),
            confirmation_id,
            approved=body.approved,
        )
        response = {
            "task_id": str(task.task_id),
            "status": task.status.value,
            "output": task.output,
            "error": task.error,
        }
        generation_id = request.query_params.get("generation_id")
        if generation_id and generation_coordinator is not None:
            await _finish_confirmed_generation(
                project_id=project_id,
                session_id=UUID(session_id),
                generation_id=UUID(generation_id),
                task=task,
                sessions=sessions,
                orchestration=orchestration,
                coordinator=generation_coordinator,
            )
            response["generation_id"] = generation_id
        return response

    @router.post("/confirmations/batch")
    async def decide_confirmations_batch(
        request: Request,
        project_id: UUID,
        body: BatchConfirmationDecision,
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
        try:
            generation_id = request.query_params.get("generation_id")
            tasks = await agent_orchestrator.decide_confirmations_batch(
                OrchestrationContext(
                    actor,
                    ProjectId(project_id),
                    UUID(session_id),
                    generation_id=UUID(generation_id) if generation_id else None,
                ),
                body.confirmation_ids,
                approved=body.approved,
            )
        except ValueError as exc:
            return JSONResponse(status_code=422, content={"detail": str(exc)})
        if generation_id and generation_coordinator is not None and tasks:
            await _finish_confirmed_generation(
                project_id=project_id,
                session_id=UUID(session_id),
                generation_id=UUID(generation_id),
                task=tasks[-1],
                sessions=sessions,
                orchestration=orchestration,
                coordinator=generation_coordinator,
            )
        return {
            "results": [
                {
                    "task_id": str(t.task_id),
                    "status": t.status.value,
                    "output": t.output,
                    "error": t.error,
                }
                for t in tasks
            ]
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


def _session_response(
    session: ChatSession,
    links,
    events: list[AgentEvent],
    active_generation: ChatGeneration | None,
) -> dict[str, object]:
    return {
        **_session_summary(session),
        "messages": [
            {
                "message_id": str(message.message_id),
                "sequence": message.sequence,
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
        "timeline": _timeline(session, events),
        "event_cursor": max((event.sequence for event in events), default=0),
        "active_generation": (
            _generation_response(active_generation) if active_generation else None
        ),
    }


def _generation_response(generation: ChatGeneration) -> dict[str, object]:
    return {
        "generation_id": str(generation.generation_id),
        "status": generation.status.value,
        "partial_content": generation.partial_content,
        "workflow_id": generation.workflow_id,
    }


def _timeline(session: ChatSession, events: list[AgentEvent]) -> list[dict[str, object]]:
    raw_event_types = {"message.delta", "agent.reasoning_delta"}
    items = [
        {
            "kind": "message",
            "id": str(message.message_id),
            "timestamp": message.timestamp.isoformat(),
            "role": message.role,
            "content": message.content,
            "sequence": message.sequence,
        }
        for message in session.messages
    ]
    items.extend(
        {
            "kind": "event",
            "id": str(event.event_id),
            "timestamp": event.created_at.isoformat(),
            "event_type": event.event_type,
            "event_sequence": event.sequence,
            "generation_id": str(event.generation_id) if event.generation_id else None,
            "payload": event.payload,
        }
        for event in events
        if event.event_type not in raw_event_types
    )
    return sorted(items, key=lambda item: (str(item["timestamp"]), str(item["id"])))


def _content_with_task_results(content: str, tasks: list[AgentTask]) -> str:
    if not tasks:
        return content
    completed = [task for task in tasks if task.status is TaskStatus.COMPLETED]
    failed = [task for task in tasks if task.status is TaskStatus.FAILED]
    lines = [content.strip()] if content.strip() else []
    if completed:
        lines.append("已完成：" + "、".join(task.capability for task in completed))
    if failed:
        lines.append("未完成：" + "、".join(task.capability for task in failed))
    return "\n\n".join(lines)


def _instant_conversation_title(message: str) -> str:
    """Generate a stable first-turn title without another model round trip."""
    compact = " ".join(message.split())
    if not compact:
        return "新对话"
    return compact[:20]


async def _finish_confirmed_generation(
    *,
    project_id: UUID,
    session_id: UUID,
    generation_id: UUID,
    task: AgentTask,
    sessions: ChatSessionRepository,
    orchestration: OrchestrationRepository,
    coordinator: GenerationCoordinator,
) -> None:
    generation = await coordinator.get(ProjectId(project_id), generation_id)
    session = await sessions.get(ProjectId(project_id), ChatSessionId(session_id))
    if generation is None or session is None or generation.completed_at is not None:
        return
    if task.status is TaskStatus.COMPLETED:
        content = f"{task.capability} 已执行完成。"
    elif task.status is TaskStatus.CANCELLED:
        content = f"已取消 {task.capability}。"
    else:
        content = f"{task.capability} 执行失败。"
    session.add_assistant_message(content)
    await sessions.save(session)
    await orchestration.append_event(
        ProjectId(project_id),
        session.session_id,
        "message.completed",
        {"content": content, "generation_id": str(generation_id)},
        generation_id=generation_id,
    )
    await coordinator.complete(generation, content)
