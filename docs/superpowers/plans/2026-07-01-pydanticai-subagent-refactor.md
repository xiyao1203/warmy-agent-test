# PydanticAI SubAgent 架构重构计划

## 概述

将当前自研的 SubAgent 路由/规划/编排层迁移到 PydanticAI 框架，利用其 Agent delegation、Structured Output、Dependency Injection、Tool Approval 等成熟能力，实现代码量减少 27%、架构更清晰、长期可维护。

## 核心映射

```
当前自研                          →  PydanticAI
─────────────────────────────────────────────────────────
SubAgentRouter (.route())        →  PydanticAI Agent 内置 tool calling 路由
SuperAgentConversation           →  PydanticAI Agent + run_stream()
_plan_actions_for_subagent()     →  PydanticAI @agent.tool 装饰器 + FunctionTool
CapabilityRegistry               →  @agent.tool 函数 + 底层 Handler 调用
AgentConfirmation                →  PydanticAI hook_tool_approval
SSE model-events                 →  run_stream() → stream_structured() delta 映射
CapabilitySpec + RiskLevel       →  tool metadata + require_approval
```

## 实施步骤

### Task 1: 安装 pydantic-ai + 创建 context.py
- `uv add pydantic-ai` 到 control-api
- 创建 `OrchestrationContext` dataclass（actor, project_id, session_id, platform_gateway, confirmation_handler, stream_callback）

### Task 2: 重写 sub_agents.py（9 个 PydanticAI Agent）
- 复用已有 prompt（TARGET_AGENT_PROMPT 等）
- 将 CapabilityRegistry 的 execute() 改为 `@agent.tool` 函数
- 删除 SubAgentRouter 类（389行 → 240行 Agent 定义）

### Task 3: 创建 super_agent.py（SuperAgent 入口）
- 定义 `super_agent` 作为 triage Agent
- 工具 = 9 个领域入口 tool（每个委托给对应 sub-agent）
- 精简 system prompt（复用现有）

### Task 4: 创建 confirmation.py（风险控制）
- 实现 PydanticAI `ToolApprovalRequest` hook
- 映射 RiskLevel（READ/DRAFT_WRITE/HIGH_IMPACT）到审批策略
- READ → 自动批准，DRAFT_WRITE/HIGH_IMPACT → 走现有 Orchestrator 确认

### Task 5: 重写 conversation.py（PydanticAI 集成）
- SuperAgentConversation 改为包装 PydanticAI Agent
- respond() 使用 agent.run_stream() + Temporal 模型适配
- 保留 generate_title()（独立能力）
- 删除 _route_and_plan / _plan_actions_for_subagent

### Task 6: 更新 bootstrap/app.py 依赖注入
- 用新的 PydanticAI agent 替换 SubAgentRouter
- 保持 SuperAgentOrchestrator 不变（确认流程保留）

### Task 7: 安装依赖 + 运行测试验证
- `uv add pydantic-ai`
- `ruff check` + `pytest` 全量验证
