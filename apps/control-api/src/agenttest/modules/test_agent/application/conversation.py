"""超级测试 Agent 的真实多轮对话服务。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from agenttest.modules.identity.public import User
from agenttest.modules.model_configs.public import (
    InvocationMessage,
    ModelConfiguration,
    ModelInvoker,
    ModelPurpose,
)
from agenttest.modules.projects.public import ProjectId


class DefaultModelResolver(Protocol):
    async def resolve_default(
        self,
        actor: User,
        project_id: ProjectId,
        purpose: ModelPurpose,
    ) -> ModelConfiguration: ...


@dataclass(frozen=True, slots=True)
class ActionIntent:
    capability: str
    arguments: dict[str, object]
    rationale: str


@dataclass(frozen=True, slots=True)
class ConversationResponse:
    content: str
    actions: list[ActionIntent] = field(default_factory=list)
    total_tokens: int = 0
    latency_ms: int = 0


class SuperAgentConversation:
    def __init__(self, models: DefaultModelResolver, invoker: ModelInvoker) -> None:
        self._models = models
        self._invoker = invoker

    async def respond(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        history: list[tuple[str, str]],
    ) -> ConversationResponse:
        config = await self._models.resolve_default(
            actor,
            project_id,
            ModelPurpose.TEST_AGENT_CHAT,
        )
        system_prompt = (
            "你是 AgentTest 项目的超级测试 Agent。"
            "你需要通过自然对话理解测试目标，信息不足时先追问。"
            "不得宣称已创建、已发布或已执行任何资产，"
            "只有平台工具返回成功后才能这样表述。"
            "对问候正常回应，不要无条件生成测试计划。"
        )
        result = await self._invoker.invoke(
            config,
            [InvocationMessage(role="system", content=system_prompt)]
            + [InvocationMessage(role=role, content=content) for role, content in history],
            timeout_seconds=60,
            max_tokens=2048,
        )
        content = result.content.strip()
        if not content:
            raise ValueError("模型返回了空回复")
        return ConversationResponse(
            content=content,
            total_tokens=result.total_tokens,
            latency_ms=result.latency_ms,
        )
