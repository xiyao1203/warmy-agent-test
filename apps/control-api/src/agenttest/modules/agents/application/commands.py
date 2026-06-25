"""Agent application command handlers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

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
from agenttest.modules.agents.domain.value_objects import AgentConfig, AgentType
from agenttest.modules.audit.public import AuditWriter
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId

# ── Commands ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class CreateAgentCommand:
    project_id: ProjectId
    name: str
    agent_type: AgentType
    description: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateAgentCommand:
    agent_id: AgentId
    name: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class CreateAgentVersionCommand:
    agent_id: AgentId
    config: AgentConfig


@dataclass(frozen=True, slots=True)
class UpdateAgentVersionCommand:
    version_id: AgentVersionId
    config: AgentConfig


@dataclass(frozen=True, slots=True)
class PublishAgentVersionCommand:
    version_id: AgentVersionId


# ── Handlers ──────────────────────────────────────────────────────────────────


class CreateAgentHandler:
    def __init__(
        self,
        *,
        agents: AgentRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._agents = agents
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: CreateAgentCommand) -> Agent:
        await self._project_access.ensure_editor(actor, command.project_id)
        agent = Agent.create(
            agent_id=AgentId.new(),
            project_id=command.project_id,
            name=command.name,
            agent_type=command.agent_type,
            created_by=actor.user_id,
            description=command.description,
        )
        await self._agents.add(agent)
        await _record(
            self._audit,
            actor=actor,
            action="agents.created",
            project_id=command.project_id,
            object_type="agent",
            object_id=agent.agent_id.value,
            changes={
                "name": {"after": agent.name},
                "agent_type": {"after": agent.agent_type.value},
            },
        )
        return agent


class UpdateAgentHandler:
    def __init__(
        self,
        *,
        agents: AgentRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._agents = agents
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: UpdateAgentCommand) -> Agent:
        agent = await _required_agent(self._agents, command.agent_id)
        await self._project_access.ensure_editor(actor, agent.project_id)
        changes: dict[str, dict[str, str]] = {}
        if command.name is not None:
            before = agent.name
            agent.rename(command.name)
            changes["name"] = {"before": before, "after": agent.name}
        if command.description is not None:
            before = agent.description or ""
            agent.update_description(command.description)
            changes["description"] = {"before": before, "after": agent.description or ""}
        await self._agents.save(agent)
        await _record(
            self._audit,
            actor=actor,
            action="agents.updated",
            project_id=agent.project_id,
            object_type="agent",
            object_id=agent.agent_id.value,
            changes=changes,
        )
        return agent


class CreateAgentVersionHandler:
    def __init__(
        self,
        *,
        agents: AgentRepository,
        versions: AgentVersionRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._agents = agents
        self._versions = versions
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: CreateAgentVersionCommand) -> AgentVersion:
        agent = await _required_agent(self._agents, command.agent_id)
        await self._project_access.ensure_editor(actor, agent.project_id)
        next_number = await self._versions.get_next_version_number(agent.agent_id)
        version = AgentVersion.create_draft(
            version_id=AgentVersionId.new(),
            agent_id=agent.agent_id,
            version_number=next_number,
            config=command.config,
            created_by=actor.user_id,
        )
        await self._versions.add(version)
        await _record(
            self._audit,
            actor=actor,
            action="agents.version.created",
            project_id=agent.project_id,
            object_type="agent_version",
            object_id=version.version_id.value,
            changes={"version_number": {"after": version.version_number}},
        )
        return version


class UpdateAgentVersionHandler:
    def __init__(
        self,
        *,
        agents: AgentRepository,
        versions: AgentVersionRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._agents = agents
        self._versions = versions
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: UpdateAgentVersionCommand) -> AgentVersion:
        version = await _required_version(self._versions, command.version_id)
        agent = await _required_agent(self._agents, version.agent_id)
        await self._project_access.ensure_editor(actor, agent.project_id)
        version.update_config(command.config)
        await self._versions.save(version)
        await _record(
            self._audit,
            actor=actor,
            action="agents.version.updated",
            project_id=agent.project_id,
            object_type="agent_version",
            object_id=version.version_id.value,
            changes={},
        )
        return version


class PublishAgentVersionHandler:
    def __init__(
        self,
        *,
        agents: AgentRepository,
        versions: AgentVersionRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._agents = agents
        self._versions = versions
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: PublishAgentVersionCommand) -> AgentVersion:
        version = await _required_version(self._versions, command.version_id)
        agent = await _required_agent(self._agents, version.agent_id)
        await self._project_access.ensure_editor(actor, agent.project_id)
        version.publish()
        await self._versions.save(version)
        await _record(
            self._audit,
            actor=actor,
            action="agents.version.published",
            project_id=agent.project_id,
            object_type="agent_version",
            object_id=version.version_id.value,
            changes={
                "status": {"after": "published"},
                "version_number": {"after": version.version_number},
            },
        )
        return version


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _required_agent(agents: AgentRepository, agent_id: AgentId) -> Agent:
    agent = await agents.get_by_id(agent_id)
    if agent is None:
        raise AgentNotFoundError(agent_id)
    return agent


async def _required_version(
    versions: AgentVersionRepository,
    version_id: AgentVersionId,
) -> AgentVersion:
    version = await versions.get_by_id(version_id)
    if version is None:
        raise AgentVersionNotFoundError(version_id)
    return version


async def _record(
    audit: AuditWriter | None,
    *,
    actor: User,
    action: str,
    project_id: ProjectId,
    object_type: str,
    object_id: object,
    changes: Mapping[str, object] | None = None,
) -> None:
    if audit is not None:
        await audit.record(
            actor_user_id=actor.user_id,
            action=action,
            object_type=object_type,
            object_id=object_id,  # type: ignore[arg-type]
            project_id=project_id,
            changes=dict(changes) if changes else {},
            source_ip=None,
        )


# ── Errors ────────────────────────────────────────────────────────────────────


class AgentNotFoundError(Exception):
    def __init__(self, agent_id: AgentId) -> None:
        self.agent_id = agent_id
        super().__init__(f"Agent {agent_id.value} not found")


class AgentVersionNotFoundError(Exception):
    def __init__(self, version_id: AgentVersionId) -> None:
        self.version_id = version_id
        super().__init__(f"Agent version {version_id.value} not found")
