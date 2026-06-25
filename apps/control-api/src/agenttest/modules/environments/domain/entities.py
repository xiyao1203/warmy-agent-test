"""Environment template domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from agenttest.modules.environments.domain.value_objects import TemplateType
from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId


@dataclass(frozen=True, slots=True)
class EnvironmentTemplateId:
    value: UUID

    @classmethod
    def new(cls) -> EnvironmentTemplateId:
        return cls(uuid4())


@dataclass(slots=True)
class EnvironmentTemplate:
    template_id: EnvironmentTemplateId
    project_id: ProjectId
    name: str
    template_type: TemplateType
    config: dict[str, object]
    created_by: UserId
    created_at: datetime
    updated_at: datetime
    description: str | None = None

    @classmethod
    def create(
        cls,
        *,
        template_id: EnvironmentTemplateId,
        project_id: ProjectId,
        name: str,
        template_type: TemplateType,
        created_by: UserId,
        config: dict[str, object] | None = None,
        description: str | None = None,
    ) -> EnvironmentTemplate:
        normalized = name.strip()
        if not normalized:
            raise ValueError("Environment template name is required")
        now = datetime.now(UTC)
        return cls(
            template_id=template_id,
            project_id=project_id,
            name=normalized,
            template_type=template_type,
            config=config or {},
            created_by=created_by,
            created_at=now,
            updated_at=now,
            description=description,
        )

    def rename(self, name: str) -> None:
        normalized = name.strip()
        if not normalized:
            raise ValueError("Environment template name is required")
        self.name = normalized
        self.updated_at = datetime.now(UTC)

    def update_description(self, description: str | None) -> None:
        self.description = description
        self.updated_at = datetime.now(UTC)

    def update_config(self, config: dict[str, object]) -> None:
        self.config = config
        self.updated_at = datetime.now(UTC)
