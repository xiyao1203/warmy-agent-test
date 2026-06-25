"""Agent domain repository protocols."""

from __future__ import annotations

from typing import Protocol

from agenttest.modules.agents.domain.entities import (
    Agent,
    AgentId,
    AgentVersion,
    AgentVersionId,
)
from agenttest.modules.projects.public import ProjectId


class AgentRepository(Protocol):
    async def get_by_id(self, agent_id: AgentId) -> Agent | None: ...

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Agent], str | None]: ...

    async def add(self, agent: Agent) -> None: ...

    async def save(self, agent: Agent) -> None: ...


class AgentVersionRepository(Protocol):
    async def get_by_id(self, version_id: AgentVersionId) -> AgentVersion | None: ...

    async def list_by_agent(self, agent_id: AgentId) -> list[AgentVersion]: ...

    async def get_next_version_number(self, agent_id: AgentId) -> int: ...

    async def add(self, version: AgentVersion) -> None: ...

    async def save(self, version: AgentVersion) -> None: ...
