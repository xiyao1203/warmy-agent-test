"""独立被测 Agent 多轮对话应用服务。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from agenttest.modules.agents.public import AgentVersion, VersionStatus
from agenttest.modules.environments.public import EnvironmentTemplate
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId


@dataclass(slots=True)
class TargetChatSession:
    session_id: UUID
    project_id: UUID
    agent_version_id: UUID
    environment_template_id: UUID | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    status: str = "active"
    turns: list[TargetChatTurn] = field(default_factory=list)


@dataclass(slots=True)
class TargetChatTurn:
    turn_id: UUID
    project_id: UUID
    session_id: UUID
    sequence: int
    input: dict[str, object]
    output: dict[str, object] | None
    trace: list[dict[str, object]] | None
    scores: list[dict[str, object]] | None
    duration_ms: int | None
    token_usage: dict[str, object] | None
    error: dict[str, object] | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class TargetInvocationResult:
    output: dict[str, object]
    trace: list[dict[str, object]]
    duration_ms: int
    token_usage: dict[str, object] | None = None


class TargetChatRepository(Protocol):
    async def add_session(self, session: TargetChatSession) -> None: ...
    async def get_session(
        self, project_id: ProjectId, session_id: UUID
    ) -> TargetChatSession | None: ...
    async def list_sessions(self, project_id: ProjectId) -> list[TargetChatSession]: ...
    async def add_turn(self, turn: TargetChatTurn) -> None: ...


class TargetAgentRuntime(Protocol):
    async def invoke(
        self,
        *,
        url: str,
        mode: str,
        headers: dict[str, str],
        input: dict[str, object],
        timeout_seconds: int,
    ) -> TargetInvocationResult: ...


class VersionReader(Protocol):
    async def execute(self, actor: User, version_id) -> AgentVersion: ...


class AgentReader(Protocol):
    async def execute(self, actor: User, agent_id): ...


class EnvironmentReader(Protocol):
    async def execute(self, actor: User, template_id) -> EnvironmentTemplate: ...


class TargetChatService:
    def __init__(self, repository: TargetChatRepository, runtime: TargetAgentRuntime) -> None:
        self._repository = repository
        self._runtime = runtime

    async def create(
        self,
        *,
        actor: User,
        project_id: ProjectId,
        version: AgentVersion,
        version_project_id: ProjectId,
        environment: EnvironmentTemplate | None,
    ) -> TargetChatSession:
        if version_project_id != project_id or version.status is not VersionStatus.PUBLISHED:
            raise ValueError("只能测试当前项目中已发布的 Agent 版本")
        if environment is not None and environment.project_id != project_id:
            raise ValueError("环境模板不属于当前项目")
        now = datetime.now(UTC)
        session = TargetChatSession(
            session_id=uuid4(),
            project_id=project_id.value,
            agent_version_id=version.version_id.value,
            environment_template_id=(environment.template_id.value if environment else None),
            created_by=actor.user_id.value,
            created_at=now,
            updated_at=now,
        )
        await self._repository.add_session(session)
        return session

    async def send(
        self,
        *,
        project_id: ProjectId,
        session: TargetChatSession,
        version: AgentVersion,
        environment: EnvironmentTemplate | None,
        message: str,
    ) -> TargetChatTurn:
        if session.project_id != project_id.value:
            raise ValueError("被测 Agent 会话不属于当前项目")
        history = [
            {"input": item.input, "output": item.output}
            for item in session.turns
            if item.error is None
        ]
        payload: dict[str, object] = {"message": message, "history": history}
        config = environment.config if environment is not None else {}
        headers_raw = config.get("headers", {})
        headers = (
            {str(key): str(value) for key, value in headers_raw.items()}
            if isinstance(headers_raw, dict)
            else {}
        )
        try:
            result = await self._runtime.invoke(
                url=version.config.api_url,
                mode=str(config.get("mode", "sync")),
                headers=headers,
                input=payload,
                timeout_seconds=version.config.timeout,
            )
            turn = self._turn(session, payload, result=result)
        except Exception as error:
            turn = self._turn(
                session,
                payload,
                error={"type": type(error).__name__, "message": "被测 Agent 调用失败"},
            )
            await self._repository.add_turn(turn)
            raise
        await self._repository.add_turn(turn)
        session.turns.append(turn)
        session.updated_at = datetime.now(UTC)
        return turn

    @staticmethod
    def _turn(
        session: TargetChatSession,
        input: dict[str, object],
        *,
        result: TargetInvocationResult | None = None,
        error: dict[str, object] | None = None,
    ) -> TargetChatTurn:
        return TargetChatTurn(
            turn_id=uuid4(),
            project_id=session.project_id,
            session_id=session.session_id,
            sequence=len(session.turns) + 1,
            input=input,
            output=result.output if result else None,
            trace=result.trace if result else None,
            scores=[],
            duration_ms=result.duration_ms if result else None,
            token_usage=result.token_usage if result else None,
            error=error,
            created_at=datetime.now(UTC),
        )
