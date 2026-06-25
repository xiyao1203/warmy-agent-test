"""Agent application query handlers."""

from __future__ import annotations

from agenttest.modules.agents.application.commands import (
    _required_agent,
    _required_version,
)
from agenttest.modules.agents.application.ports import ProjectAccessPort
from agenttest.modules.agents.domain.entities import (
    Agent,
    AgentId,
    AgentVersion,
    AgentVersionId,
)
from agenttest.modules.agents.domain.repositories import (
    AgentRepository,
    AgentVersionRepository,
)
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId


class ListAgentsHandler:
    def __init__(
        self,
        *,
        agents: AgentRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._agents = agents
        self._project_access = project_access

    async def execute(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Agent], str | None]:
        await self._project_access.ensure_member(actor, project_id)
        return await self._agents.list_by_project(
            project_id,
            limit=limit,
            cursor=cursor,
        )


class GetAgentHandler:
    def __init__(
        self,
        *,
        agents: AgentRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._agents = agents
        self._project_access = project_access

    async def execute(self, actor: User, agent_id: AgentId) -> Agent:
        agent = await _required_agent(self._agents, agent_id)
        await self._project_access.ensure_member(actor, agent.project_id)
        return agent


class ListAgentVersionsHandler:
    def __init__(
        self,
        *,
        agents: AgentRepository,
        versions: AgentVersionRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._agents = agents
        self._versions = versions
        self._project_access = project_access

    async def execute(self, actor: User, agent_id: AgentId) -> list[AgentVersion]:
        agent = await _required_agent(self._agents, agent_id)
        await self._project_access.ensure_member(actor, agent.project_id)
        return await self._versions.list_by_agent(agent.agent_id)


class GetAgentVersionHandler:
    def __init__(
        self,
        *,
        agents: AgentRepository,
        versions: AgentVersionRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._agents = agents
        self._versions = versions
        self._project_access = project_access

    async def execute(self, actor: User, version_id: AgentVersionId) -> AgentVersion:
        version = await _required_version(self._versions, version_id)
        agent = await _required_agent(self._agents, version.agent_id)
        await self._project_access.ensure_member(actor, agent.project_id)
        return version
