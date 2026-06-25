"""Agent domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from agenttest.modules.agents.domain.value_objects import (
    AgentConfig,
    AgentType,
    VersionStatus,
)
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId


@dataclass(frozen=True, slots=True)
class AgentId:
    value: UUID

    @classmethod
    def new(cls) -> AgentId:
        return cls(uuid4())


@dataclass(frozen=True, slots=True)
class AgentVersionId:
    value: UUID

    @classmethod
    def new(cls) -> AgentVersionId:
        return cls(uuid4())


@dataclass(slots=True)
class Agent:
    """Root entity representing an AI agent under a project."""

    agent_id: AgentId
    project_id: ProjectId
    name: str
    agent_type: AgentType
    created_by: UserId
    updated_by: UserId
    created_at: datetime
    updated_at: datetime
    description: str | None = None

    @classmethod
    def create(
        cls,
        *,
        agent_id: AgentId,
        project_id: ProjectId,
        name: str,
        agent_type: AgentType,
        created_by: UserId,
        description: str | None = None,
    ) -> Agent:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Agent name is required")
        now = datetime.now(UTC)
        return cls(
            agent_id=agent_id,
            project_id=project_id,
            name=normalized_name,
            agent_type=agent_type,
            created_by=created_by,
            updated_by=created_by,
            created_at=now,
            updated_at=now,
            description=description,
        )

    def rename(self, name: str) -> None:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Agent name is required")
        self.name = normalized_name
        self.updated_at = datetime.now(UTC)

    def update_description(self, description: str | None) -> None:
        self.description = description
        self.updated_at = datetime.now(UTC)


@dataclass(slots=True)
class AgentVersion:
    """An immutable-once-published version of an agent's configuration."""

    version_id: AgentVersionId
    agent_id: AgentId
    version_number: int
    status: VersionStatus
    config: AgentConfig
    created_by: UserId
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None

    @classmethod
    def create_draft(
        cls,
        *,
        version_id: AgentVersionId,
        agent_id: AgentId,
        version_number: int,
        config: AgentConfig,
        created_by: UserId,
    ) -> AgentVersion:
        if version_number < 1:
            raise ValueError("version_number must be >= 1")
        now = datetime.now(UTC)
        return cls(
            version_id=version_id,
            agent_id=agent_id,
            version_number=version_number,
            status=VersionStatus.DRAFT,
            config=config,
            published_at=None,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

    @property
    def is_editable(self) -> bool:
        """Only draft versions can be modified."""
        return self.status is VersionStatus.DRAFT

    @property
    def is_published(self) -> bool:
        return self.status is VersionStatus.PUBLISHED

    def publish(self) -> None:
        """Transition from draft to published.  Once published, immutable."""
        if self.status is VersionStatus.PUBLISHED:
            raise ValueError("Version is already published")
        self.status = VersionStatus.PUBLISHED
        self.published_at = datetime.now(UTC)
        self.updated_at = self.published_at

    def update_config(self, config: AgentConfig) -> None:
        """Update the config of a draft version."""
        if not self.is_editable:
            raise ValueError("Cannot modify a published version")
        self.config = config
        self.updated_at = datetime.now(UTC)

    @classmethod
    def create_new_version_from(
        cls,
        *,
        version_id: AgentVersionId,
        source: AgentVersion,
        new_version_number: int,
    ) -> AgentVersion:
        """Create a new draft version from a published version.

        The new draft inherits the config of the source version.
        """
        if not source.is_published:
            raise ValueError("Can only create a new version from a published version")
        now = datetime.now(UTC)
        return cls(
            version_id=version_id,
            agent_id=source.agent_id,
            version_number=new_version_number,
            status=VersionStatus.DRAFT,
            config=source.config,
            published_at=None,
            created_by=source.created_by,
            created_at=now,
            updated_at=now,
        )
