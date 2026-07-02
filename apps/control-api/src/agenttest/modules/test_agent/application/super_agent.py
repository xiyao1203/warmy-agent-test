"""SuperAgent：PydanticAI Agent 实例 + 9 领域 SubAgent 委托。

核心架构（Phase 2）：
- 每个 SubAgent = 独立的 PydanticAI Agent（含特化 system_prompt + 领域工具）
- SuperAgent = 顶层 PydanticAI Agent，通过 delegation tool 把请求委托给对应 SubAgent
- 使用自定义 TemporalModel 适配器，所有 LLM 调用经 Temporal → Worker → Provider

对比 Phase 1：
- SubAgentRouter 静态类 → 原生 agent.run() delegation
- plan_actions_for_subagent() → PydanticAI @agent.tool 函数
- 手动 action context 拼接 → RunContext.deps 注入
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai._function_schema import FunctionSchema
from pydantic_ai.tools import Tool
from pydantic_core import SchemaValidator, core_schema

from agenttest.modules.test_agent.application.confirmation import (
    tool_prepare_read_only,
)
from agenttest.modules.test_agent.application.context import OrchestrationContext
from agenttest.modules.test_agent.application.sub_agents import (
    SubAgentName,
    get_sub_agent,
    list_sub_agents,
)
from agenttest.modules.test_agent.application.temporal_model import TemporalModel
from agenttest.modules.test_agent.domain.entities import RiskLevel

# ── 能力目录（用于构建领域工具）─────────────────────────────────────

try:
    from agenttest.modules.test_agent.application.platform_catalog import (
        CapabilitySpec,
        capability_specs,
    )
except ImportError:

    def capability_specs() -> list:  # type: ignore[no-redef]
        return []

    CapabilitySpec = None  # type: ignore[assignment]


# ── 超级 Agent system prompt ─────────────────────────────────────

SUPER_AGENT_SYSTEM_PROMPT = (
    "你是 AgentTest 项目的超级测试 Agent，负责引导用户完成 Agent 测试全流程。\n\n"
    "## 行为规范\n"
    "- 回复简洁直接，每次最多 3 句话，不寒暄、不客套\n"
    "- 对短问候只需一句话回应并询问需求，不要介绍平台功能\n"
    "- 用户没问到的功能不要主动列出来\n"
    "- 语气自然克制，像同事聊天，不要过于热情\n"
    "- 信息不足时主动追问，不要猜测\n"
    "- 不得宣称已创建/已执行任何资产，只有平台工具返回成功后才可表述\n"
    "- 高风险操作（如 runs.start）需向用户说明影响范围\n"
    "- 你拥有 9 个领域专家可以调用，根据用户意图选择最合适的专家委托任务"
)

# ── 路由专用 system prompt（保留供非 PydanticAI 回退路径使用）─────

_ROUTER_SYSTEM_PROMPT = (
    "你是 AgentTest 平台的任务路由器。"
    "根据用户最后一条消息，判断应该委托给哪个（或哪两个）领域专家处理。\n\n"
    "只输出 JSON：{\"sub_agents\": [\"target_agent\", ...]}\n"
    "可选值：target_agent, environment, test_data, test_plan, "
    "execution, evaluation, experiment, security, review_gate\n\n"
    "路由规则：\n"
    "- Agent 注册/配置/连接/版本/端点 → target_agent\n"
    "- 环境/模板/凭证/账号 → environment\n"
    "- 用例/数据集/测试数据/自动生成 → test_data\n"
    "- 测试计划/绑定/编排 → test_plan\n"
    "- 运行/执行/启动测试/报告/取消 → execution\n"
    "- 评分/评分器/评测配置 → evaluation\n"
    "- 对比/实验/A|B测试/版本对比 → experiment\n"
    "- 安全/扫描/红队/注入 → security\n"
    "- 审核/门禁/审批/发布 → review_gate\n"
    "- 问候/闲聊/问平台能力 → 返回空数组 []\n"
    "- 涉及多领域时最多选 2 个最相关的"
)

# ── PydanticAI 输出模型 ──────────────────────────────────────────

class _PlannedAction(BaseModel):
    child_agent: str = Field(min_length=1, max_length=64)
    capability: str = Field(min_length=1, max_length=128)
    arguments: dict[str, object]
    rationale: str = Field(min_length=1, max_length=1000)

class _ActionPlan(BaseModel):
    actions: list[_PlannedAction] = Field(default_factory=list, max_length=20)


@dataclass(frozen=True, slots=True)
class ActionIntent:
    """平台能力操作意图（供 Orchestrator 执行）。"""
    capability: str
    arguments: dict[str, object]
    rationale: str
    child_agent: str = ""


# ── SubAgent 工厂 ────────────────────────────────────────────────

def _create_sub_agent(
    name: SubAgentName,
    temporal_model: TemporalModel,
) -> Agent[OrchestrationContext]:
    """创建领域 SubAgent 的 PydanticAI Agent 实例。

    每个 SubAgent 使用其特化 system_prompt，并通过 READ 领域工具
    直接调用 PlatformGateway（跳过 Orchestrator 确认）。
    WRITE 操作继续通过 _ActionPlan 输出，由 Orchestrator 接管确认。
    """
    sub = get_sub_agent(name)
    tools = _build_domain_read_tools(name)
    return Agent(
        model=temporal_model,
        system_prompt=sub.system_prompt,
        deps_type=OrchestrationContext,
        name=name.value,
        output_type=_ActionPlan,
        tools=tools if tools else None,
    )


def _build_domain_read_tools(
    name: SubAgentName,
) -> list[Tool]:
    """为指定领域构建 READ 工具列表（Tool 对象，含精确 JSON Schema）。

    每个 READ 工具直接调用 ctx.deps.platform_gateway.execute()，
    无需 Orchestrator 确认。工具参数来自 capability 的 input_model。
    """
    specs = capability_specs()
    domain_specs = [
        s for s in specs
        if s.child_agent == name.value and s.risk == RiskLevel.READ
    ]
    tools: list[Tool] = []
    for spec in domain_specs:
        tools.append(_make_read_tool(spec.name, spec.input_model))
    return tools


def _make_read_tool(cap_name: str, input_model_cls: type[BaseModel]) -> Tool:
    """构建单个 READ 工具（Tool 对象，含从 input_model 生成的精确 JSON Schema）。

    LLM 看到的是 input_model 的完整字段类型和描述，而非空 Schema {}。
    """
    description = _tool_descriptions().get(cap_name, cap_name)
    json_schema = input_model_cls.model_json_schema()

    async def tool_fn(
        ctx: RunContext[OrchestrationContext],
        **kwargs: object,
    ) -> dict:
        """Execute a read-only platform capability."""
        payload = input_model_cls.model_validate(kwargs or {})
        gateway = ctx.deps.platform_gateway
        if gateway is None:
            return {"error": "platform_gateway not configured"}
        return await gateway.execute(cap_name, ctx.deps, payload)

    tool_fn.__name__ = cap_name.replace(".", "_")
    tool_fn.__qualname__ = f"read_{cap_name.replace('.', '_')}"

    function_schema = FunctionSchema(
        function=tool_fn,
        description=description,
        validator=SchemaValidator(schema=core_schema.any_schema()),
        json_schema=json_schema,
        takes_ctx=True,
        is_async=True,
    )

    return Tool(
        tool_fn,
        takes_ctx=True,
        name=cap_name.replace(".", "_"),
        description=description,
        prepare=tool_prepare_read_only,
        function_schema=function_schema,
    )


def _tool_descriptions() -> dict[str, str]:
    """能力名称到用户友好描述的映射。"""
    return {
        "agents.list": "浏览已注册的 Agent 列表。可选参数: query（搜索关键词）。",
        "environments.list": "浏览环境模板列表。可选参数: query（搜索关键词）。",
        "credentials.list": "浏览测试凭证列表。可选参数: query（搜索关键词）。",
        "datasets.list": "浏览数据集列表。可选参数: query（搜索关键词）。",
        "test_plans.list": "浏览测试计划列表。可选参数: query（搜索关键词）。",
        "runs.list": "浏览测试运行记录列表。可选参数: query（搜索关键词）。",
        "scorers.list": "浏览评分器列表。可选参数: query（搜索关键词）。",
        "experiments.list": "浏览实验对比列表。可选参数: query（搜索关键词）。",
        "security_scans.list": "浏览安全扫描记录列表。可选参数: query（搜索关键词）。",
        "reviews.list": "浏览人工审核任务列表。可选参数: query（搜索关键词）。",
        "release_gates.list": "浏览发布门禁列表。可选参数: query（搜索关键词）。",
        "agents.analyze_endpoint": (
            "探测 Agent API 端点，返回连接状态、延迟和响应结构。"
            "必填: agent_version_id。"
        ),
        "reports.generate": "生成测试运行报告。必填: run_id。",
    }


# ── SuperAgent 工厂 ──────────────────────────────────────────────

def create_super_agent(
    invoker,      # ModelInvoker
    config,       # ModelConfiguration
) -> Agent[OrchestrationContext]:
    """创建顶层 SuperAgent 的 PydanticAI Agent 实例。

    SuperAgent 拥有 9 个领域 delegation tool，每个 tool 将用户请求
    委托给对应 SubAgent 处理并返回结构化 ActionPlan。

    Args:
        invoker: TemporalModelInvoker 实例。
        config: 模型配置（含 model_name、project_id 等）。

    Returns:
        配置好的 PydanticAI Agent 实例。
    """
    model = TemporalModel(
        invoker=invoker,
        config=config,
        display_name=config.model_name,
    )

    # 预创建 9 个 SubAgent 实例（共享同一 TemporalModel）
    sub_agents: dict[SubAgentName, Agent[OrchestrationContext]] = {}
    for name in SubAgentName:
        sub_agents[name] = _create_sub_agent(name, model)

    # ── 9 个领域 delegation tool ──────────────────────────────

    async def delegate_target_agent(
        ctx: RunContext[OrchestrationContext], request: str,
    ) -> _ActionPlan:
        """委托给 Agent 管理专家：注册、配置、连接待测 Agent。"""
        result = await sub_agents[SubAgentName.TARGET_AGENT].run(
            request, deps=ctx.deps, usage=ctx.usage,
        )
        return result.data

    async def delegate_environment(
        ctx: RunContext[OrchestrationContext], request: str,
    ) -> _ActionPlan:
        """委托给环境与凭证专家：管理测试环境模板和认证凭证。"""
        result = await sub_agents[SubAgentName.ENVIRONMENT].run(
            request, deps=ctx.deps, usage=ctx.usage,
        )
        return result.data

    async def delegate_test_data(
        ctx: RunContext[OrchestrationContext], request: str,
    ) -> _ActionPlan:
        """委托给测试数据专家：创建和管理测试数据集与用例。"""
        result = await sub_agents[SubAgentName.TEST_DATA].run(
            request, deps=ctx.deps, usage=ctx.usage,
        )
        return result.data

    async def delegate_test_plan(
        ctx: RunContext[OrchestrationContext], request: str,
    ) -> _ActionPlan:
        """委托给测试计划专家：编排测试计划（绑定 Agent+数据集）。"""
        result = await sub_agents[SubAgentName.TEST_PLAN].run(
            request, deps=ctx.deps, usage=ctx.usage,
        )
        return result.data

    async def delegate_execution(
        ctx: RunContext[OrchestrationContext], request: str,
    ) -> _ActionPlan:
        """委托给执行与报告专家：启动测试运行并查看报告。"""
        result = await sub_agents[SubAgentName.EXECUTION].run(
            request, deps=ctx.deps, usage=ctx.usage,
        )
        return result.data

    async def delegate_evaluation(
        ctx: RunContext[OrchestrationContext], request: str,
    ) -> _ActionPlan:
        """委托给评分器专家：管理评分规则和评测配置。"""
        result = await sub_agents[SubAgentName.EVALUATION].run(
            request, deps=ctx.deps, usage=ctx.usage,
        )
        return result.data

    async def delegate_experiment(
        ctx: RunContext[OrchestrationContext], request: str,
    ) -> _ActionPlan:
        """委托给实验对比专家：对比不同 Agent 版本的测试差异。"""
        result = await sub_agents[SubAgentName.EXPERIMENT].run(
            request, deps=ctx.deps, usage=ctx.usage,
        )
        return result.data

    async def delegate_security(
        ctx: RunContext[OrchestrationContext], request: str,
    ) -> _ActionPlan:
        """委托给安全测试专家：执行安全扫描和红队测试。"""
        result = await sub_agents[SubAgentName.SECURITY].run(
            request, deps=ctx.deps, usage=ctx.usage,
        )
        return result.data

    async def delegate_review_gate(
        ctx: RunContext[OrchestrationContext], request: str,
    ) -> _ActionPlan:
        """委托给审核与门禁专家：管理人工审核队列和发布门禁。"""
        result = await sub_agents[SubAgentName.REVIEW_GATE].run(
            request, deps=ctx.deps, usage=ctx.usage,
        )
        return result.data

    return Agent(
        model=model,
        system_prompt=SUPER_AGENT_SYSTEM_PROMPT,
        deps_type=OrchestrationContext,
        name="super_agent",
        tools=[
            delegate_target_agent,
            delegate_environment,
            delegate_test_data,
            delegate_test_plan,
            delegate_execution,
            delegate_evaluation,
            delegate_experiment,
            delegate_security,
            delegate_review_gate,
        ],
    )


# ── 回退路由器（当 PydanticAI Agent 不可用时的静态路由）─────────

class SubAgentRouter:
    """基于 LLM 的轻量意图路由器（回退路径）。

    当 PydanticAI Agent 因模型配置不可用或初始化失败时，
    使用此静态路由作为降级方案。
    """

    @staticmethod
    async def route(
        invoker,
        config,
        *,
        user_message: str,
    ) -> list[SubAgentName]:
        """分析用户意图，返回匹配的子 Agent 名称列表。"""
        from agenttest.modules.model_configs.public import InvocationMessage

        messages = [
            InvocationMessage(role="system", content=_ROUTER_SYSTEM_PROMPT),
            InvocationMessage(role="user", content=user_message[:500]),
        ]
        result = await invoker.invoke(
            config, messages, timeout_seconds=10, max_tokens=64,
        )
        try:
            from pydantic import BaseModel as _BM
            from pydantic import Field as _F

            class _RD(_BM):
                sub_agents: list[str] = _F(default_factory=list, max_length=2)

            decision = _RD.model_validate_json(result.content)
        except Exception:
            return []
        names: list[SubAgentName] = []
        for raw in decision.sub_agents:
            try:
                names.append(SubAgentName(raw))
            except ValueError:
                continue
        return names


# ── 兼容函数 ──────────────────────────────────────────────────────

async def plan_actions_for_subagent(
    invoker,
    config,
    history: list[tuple[str, str]],
    *,
    subagent_name: SubAgentName,
    capabilities: list[dict[str, object]],
    action_context: dict[str, object] | None = None,
    stream_callback=None,
) -> list[ActionIntent]:
    """使用领域 sub-agent 的特化 prompt 和能力列表规划操作。

    保留此函数作为 PydanticAI Agent 的回退路径。
    """
    import json as _json

    from agenttest.modules.model_configs.public import InvocationMessage

    sub = get_sub_agent(subagent_name)
    allowed = {(str(item["child_agent"]), str(item["name"])) for item in capabilities}

    context_block = ""
    if action_context:
        context_lines = []
        for cap_name, result in action_context.items():
            if isinstance(result, dict):
                artifacts = result.get("artifacts", [])
                ids = [
                    f"{a.get('type','')}_id={a.get('id','')}"
                    for a in artifacts
                    if isinstance(a, dict)
                ]
                ids_display = ", ".join(ids) if ids else "completed"
                context_lines.append(f"  - {cap_name} -> {ids_display}")
            else:
                context_lines.append(f"  - {cap_name} -> {result}")
        if context_lines:
            context_block = (
                "先前已执行的操作及其产出（后续操作可直接引用这些 ID）:\n"
                + "\n".join(context_lines) + "\n"
            )

    prompt = (
        sub.system_prompt
        + "\n" + context_block
        + '返回 JSON：{"actions":[{"child_agent":"...",'
        + '"capability":"...","arguments":{},"rationale":"..."}]}.\n'
        + f"capabilities={_json.dumps(capabilities, ensure_ascii=False)}"
    )

    messages = [InvocationMessage(role="system", content=prompt)] + [
        InvocationMessage(role=role, content=content) for role, content in history
    ]

    if stream_callback is not None:
        result = await invoker.stream(
            config, messages, callback=stream_callback,
            timeout_seconds=60, max_tokens=2048,
        )
    else:
        result = await invoker.invoke(
            config, messages,
            response_format={"type": "json_object"},
            timeout_seconds=60, max_tokens=2048,
        )

    try:
        plan = _ActionPlan.model_validate_json(result.content)
    except Exception:
        return []

    return [
        ActionIntent(
            child_agent=item.child_agent,
            capability=item.capability,
            arguments=item.arguments,
            rationale=item.rationale,
        )
        for item in plan.actions
        if (item.child_agent, item.capability) in allowed
    ]


def describe_all_sub_agents() -> list[dict[str, str]]:
    """列出所有子 Agent 的路由描述。"""
    return [
        {"name": sa.name.value, "display": sa.display_name, "description": sa.description}
        for sa in list_sub_agents()
    ]
