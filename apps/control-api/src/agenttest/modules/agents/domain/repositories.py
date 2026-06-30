"""Agent 领域仓库接口（Protocol）。

定义 AgentRepository 和 AgentVersionRepository 的抽象协议，
由基础设施层提供 SQLAlchemy 实现。
"""

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
    """Agent 聚合根的持久化仓库接口。"""

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

    async def delete(self, agent_id: AgentId) -> None: ...


class AgentVersionRepository(Protocol):
    """Agent 版本的持久化仓库接口。"""

    async def get_by_id(self, version_id: AgentVersionId) -> AgentVersion | None: ...

    async def list_by_agent(self, agent_id: AgentId) -> list[AgentVersion]: ...

    async def get_next_version_number(self, agent_id: AgentId) -> int: ...

    async def add(self, version: AgentVersion) -> None: ...

    async def save(self, version: AgentVersion) -> None: ...
