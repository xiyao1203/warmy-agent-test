"""风险驱动的操作确认处理器（PydanticAI 兼容）。

将平台的 READ / DRAFT_WRITE / HIGH_IMPACT 三级风险模型
映射为统一的确认接口。

与 SuperAgentOrchestrator 的关系：
- confirmation.py 定义确认策略（什么风险需要确认）
- orchestrator.py 执行具体确认流程（创建 AgentTask、等待用户决策）

PydanticAI 集成路径（Phase 3）：
- SubAgent 的 READ 工具直接调用 PlatformGateway（无需 Orchestrator 确认）
- WRITE 操作继续通过 _ActionPlan → Orchestrator 确认流程
- tool_prepare 回调可注册到 PydanticAI Tool，用于运行时标记风险级别
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from agenttest.modules.test_agent.domain.entities import RiskLevel

if TYPE_CHECKING:
    from pydantic_ai.tools import RunContext, ToolDefinition

    from agenttest.modules.test_agent.application.context import (
        OrchestrationContext,
    )


class ApprovalDecision(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"


@dataclass(frozen=True, slots=True)
class ConfirmationRequest:
    """单次确认请求。

    Attributes:
        capability: 能力名称（如 runs.start）。
        child_agent: 子 Agent 标识。
        risk_level: 风险级别。
        rationale: 操作理由。
        arguments: 操作参数摘要。
    """

    capability: str
    child_agent: str
    risk_level: RiskLevel
    rationale: str
    arguments: dict[str, object]


class ConfirmationHandler:
    """风险驱动的确认决策器。

    核心规则：
    - READ → 自动批准（无需用户确认）
    - DRAFT_WRITE → 需要用户确认
    - HIGH_IMPACT → 需要用户显式批准
    """

    def classify(self, request: ConfirmationRequest) -> ApprovalDecision:
        """根据风险级别返回审批决定。

        READ 操作自动批准，其余返回 PENDING 等待用户决策。
        """
        if request.risk_level is RiskLevel.READ:
            return ApprovalDecision.APPROVED
        return ApprovalDecision.PENDING

    def requires_confirmation(self, risk_level: RiskLevel) -> bool:
        """判断给定风险级别是否需要用户确认。"""
        return risk_level is not RiskLevel.READ

    def requires_explicit_approval(self, risk_level: RiskLevel) -> bool:
        """判断是否需要显式批准（而非简单确认）。"""
        return risk_level is RiskLevel.HIGH_IMPACT


async def tool_prepare_read_only(
    ctx: RunContext[OrchestrationContext],
    tool_def: ToolDefinition,
) -> ToolDefinition | None:
    """PydanticAI Tool prepare 回调：仅当 platform_gateway 就绪时注册。

    用于 READ 工具的运行时条件注册。如果 platform_gateway 未配置
    （如测试环境），返回 None 以从当前 step 中省略该工具。

    在 super_agent.py 中创建 Tool 时作为 prepare 参数传入：
        Tool(my_read_tool, prepare=tool_prepare_read_only)
    """
    if ctx.deps.platform_gateway is None:
        return None
    return tool_def
