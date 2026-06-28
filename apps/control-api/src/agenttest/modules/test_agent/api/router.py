"""测试 Agent 对话 API 路由。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.modules.test_agent.adapters.playwright_agents import (
    AgentType,
    create_playwright_agent_adapter,
)
from agenttest.modules.test_agent.domain.entities import (
    ChatSession,
)
from agenttest.modules.test_agent.llm_adapters import create_llm_adapter
from agenttest.shared.api.auth_guard import require_actor, require_writer


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ConfirmRequest(BaseModel):
    session_id: str


class PlaywrightAgentRequest(BaseModel):
    """Playwright Agent 请求。"""
    agent_type: str  # planner | generator | healer
    prompt: str
    seed_test: str | None = None
    prd_path: str | None = None
    plan_path: str | None = None
    test_name: str | None = None


def create_test_agent_router(
    *, session_factory, actor_for, check_project, settings,
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/test-agent",
        tags=["test-agent"],
    )

    # In-memory session store (production should use DB)
    _sessions: dict[str, ChatSession] = {}
    _llm = create_llm_adapter()
    _playwright_adapter = create_playwright_agent_adapter()
    # 任务存储
    _tasks: dict[str, dict] = {}

    @router.post("/chat")
    async def chat(
        request: Request,
        project_id: UUID,
        body: ChatRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        """发送自然语言指令，返回 Agent 回复和计划草稿。"""
        actor = await require_writer(
            request, actor_for, settings, x_csrf_token,
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(
                status_code=404, content={"detail": "项目不存在"},
            )
        except InvalidSessionError:
            return JSONResponse(
                status_code=401, content={"detail": "认证失败"},
            )

        # Get or create session
        session: ChatSession | None = None
        if body.session_id and body.session_id in _sessions:
            session = _sessions[body.session_id]
        if session is None:
            session = ChatSession.create(project_id=project_id)
            _sessions[str(session.session_id.value)] = session

        session.add_user_message(body.message)

        # Generate plan via LLM adapter (OpenAI or Mock fallback)
        plan_draft = await _llm.generate_plan(body.message)
        response_text = (
            f"已为您生成测试计划草稿。包含 {plan_draft.get('estimated_cases', 0)} "
            f"个用例，预计执行 {plan_draft.get('estimated_duration_min', 0)} 分钟。"
        )
        session.add_assistant_message(response_text, plan_draft=plan_draft)

        return {
            "session_id": str(session.session_id.value),
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in session.messages
            ],
            "plan_draft": session.plan_draft,
            "status": session.status.value,
        }

    @router.post("/confirm")
    async def confirm(
        request: Request,
        project_id: UUID,
        body: ConfirmRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        """确认执行测试计划。"""
        actor = await require_writer(
            request, actor_for, settings, x_csrf_token,
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(
                status_code=404, content={"detail": "项目不存在"},
            )
        except InvalidSessionError:
            return JSONResponse(
                status_code=401, content={"detail": "认证失败"},
            )

        session = _sessions.get(body.session_id)
        if session is None:
            return JSONResponse(
                status_code=404, content={"detail": "会话不存在"},
            )
        if session.project_id != project_id:
            return JSONResponse(
                status_code=404, content={"detail": "会话不存在"},
            )

        try:
            plan = session.confirm_plan()
        except ValueError as e:
            return JSONResponse(status_code=422, content={"detail": str(e)})

        session.add_assistant_message("测试计划已确认，开始执行...")
        session.complete()

        return {
            "session_id": str(session.session_id.value),
            "status": session.status.value,
            "plan": plan,
            "message": "测试计划已确认并开始执行",
        }

    @router.get("/sessions/{session_id}")
    async def get_session(
        request: Request,
        project_id: UUID,
        session_id: str,
    ):
        """获取会话详情。"""
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor

        session = _sessions.get(session_id)
        if session is None or session.project_id != project_id:
            return JSONResponse(
                status_code=404, content={"detail": "会话不存在"},
            )

        return {
            "session_id": str(session.session_id.value),
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in session.messages
            ],
            "plan_draft": session.plan_draft,
            "status": session.status.value,
        }

    # ── Playwright Agent 端点 ─────────────────────────────────────────────────

    @router.post("/playwright/execute")
    async def execute_playwright_agent(
        request: Request,
        project_id: UUID,
        body: PlaywrightAgentRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        """执行 Playwright Test Agent。

        支持三种 Agent：
        - planner: 生成测试计划
        - generator: 生成测试代码
        - healer: 修复失败测试
        """
        actor = await require_writer(
            request, actor_for, settings, x_csrf_token,
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(
                status_code=404, content={"detail": "项目不存在"},
            )
        except InvalidSessionError:
            return JSONResponse(
                status_code=401, content={"detail": "认证失败"},
            )

        # 根据 agent 类型执行
        agent_type = body.agent_type.lower()
        if agent_type == AgentType.PLANNER:
            result = await _playwright_adapter.run_planner(
                prompt=body.prompt,
                seed_test=body.seed_test,
                prd_path=body.prd_path,
            )
        elif agent_type == AgentType.GENERATOR:
            if not body.plan_path:
                return JSONResponse(
                    status_code=422,
                    content={"detail": "Generator 需要 plan_path 参数"},
                )
            result = await _playwright_adapter.run_generator(
                plan_path=body.plan_path,
                seed_test=body.seed_test,
            )
        elif agent_type == AgentType.HEALER:
            if not body.test_name:
                return JSONResponse(
                    status_code=422,
                    content={"detail": "Healer 需要 test_name 参数"},
                )
            result = await _playwright_adapter.run_healer(
                test_name=body.test_name,
            )
        else:
            return JSONResponse(
                status_code=422,
                content={"detail": f"不支持的 agent 类型: {body.agent_type}"},
            )

        # 存储任务结果
        _tasks[result.task_id] = {
            "task_id": result.task_id,
            "agent_type": result.agent_type.value,
            "status": result.status.value,
            "output": result.output,
            "artifacts": result.artifacts,
            "error": result.error,
            "project_id": str(project_id),
        }

        return _tasks[result.task_id]

    @router.get("/playwright/tasks/{task_id}")
    async def get_playwright_task(
        request: Request,
        project_id: UUID,
        task_id: str,
    ):
        """获取 Playwright Agent 任务状态。"""
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor

        task = _tasks.get(task_id)
        if task is None or task.get("project_id") != str(project_id):
            return JSONResponse(
                status_code=404, content={"detail": "任务不存在"},
            )

        return task

    @router.get("/playwright/tasks")
    async def list_playwright_tasks(
        request: Request,
        project_id: UUID,
    ):
        """列出项目所有 Playwright Agent 任务。"""
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor

        project_tasks = [
            t for t in _tasks.values()
            if t.get("project_id") == str(project_id)
        ]

        return {"tasks": project_tasks, "total": len(project_tasks)}

    return router
