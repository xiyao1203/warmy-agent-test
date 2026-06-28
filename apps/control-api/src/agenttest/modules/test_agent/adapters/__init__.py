"""Playwright Test Agents 适配器模块。"""

from agenttest.modules.test_agent.adapters.playwright_agents import (
    AgentType,
    AgentTaskResult,
    PlaywrightAgentAdapter,
    TaskStatus,
    create_playwright_agent_adapter,
)

__all__ = [
    "AgentType",
    "AgentTaskResult",
    "PlaywrightAgentAdapter",
    "TaskStatus",
    "create_playwright_agent_adapter",
]
