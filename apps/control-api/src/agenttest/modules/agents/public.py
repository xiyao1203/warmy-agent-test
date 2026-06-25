"""Stable public interface for the agents module.

Other modules must only import from this file when referencing agents.
"""

from __future__ import annotations

from agenttest.modules.agents.domain.entities import (
    Agent,
    AgentId,
    AgentVersion,
    AgentVersionId,
)
from agenttest.modules.agents.domain.value_objects import (
    AgentConfig,
    AgentType,
    VersionStatus,
)

__all__ = [
    "Agent",
    "AgentConfig",
    "AgentId",
    "AgentType",
    "AgentVersion",
    "AgentVersionId",
    "AgentVersionRef",
    "VersionStatus",
]


class AgentVersionRef:
    """已发布 Agent 版本的轻量引用。

    供其他模块（如 test_plans）引用 Agent 版本时使用，
    避免加载完整实体。
    """

    __slots__ = ("agent_version_id", "agent_id", "version_number")

    def __init__(
        self,
        agent_version_id: AgentVersionId,
        agent_id: AgentId,
        version_number: int,
    ) -> None:
        self.agent_version_id = agent_version_id
        self.agent_id = agent_id
        self.version_number = version_number

    @classmethod
    def from_version(cls, version: AgentVersion) -> AgentVersionRef:
        """从完整 AgentVersion 实体创建引用。"""
        return cls(version.version_id, version.agent_id, version.version_number)
