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
    """Lightweight reference to a published agent version.

    Used by other modules (e.g. test_plans) to reference a specific
    agent version without loading the full entity.
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
        return cls(version.version_id, version.agent_id, version.version_number)
