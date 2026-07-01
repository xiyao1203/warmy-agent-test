"""Environment version application services.

CRUD and lifecycle management for immutable, publishable environment versions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from agenttest.modules.audit.public import AuditWriter
from agenttest.modules.environments.application.ports import ProjectAccessPort
from agenttest.modules.environments.domain.entities import (
    EnvironmentTemplateId,
)
from agenttest.modules.environments.domain.repositories import (
    EnvironmentTemplateRepository,
)
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId

# ── Domain record for a version ────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class EnvironmentVersionRecord:
    """Read-only projection of an environment version row."""

    id: UUID
    project_id: UUID
    environment_template_id: UUID
    version_number: int
    status: str  # "draft" | "published"
    config: dict[str, object]
    published_at: datetime | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime


# ── Repository protocol ────────────────────────────────────────────────────


class EnvironmentVersionRepository(Protocol):
    """Persistence contract for environment versions."""

    async def get_by_id(
        self, version_id: UUID, project_id: ProjectId
    ) -> EnvironmentVersionRecord | None: ...

    async def list_by_template(
        self, template_id: EnvironmentTemplateId, project_id: ProjectId
    ) -> list[EnvironmentVersionRecord]: ...

    async def get_next_version_number(
        self, template_id: EnvironmentTemplateId, project_id: ProjectId
    ) -> int: ...

    async def add(self, version: EnvironmentVersionRecord) -> None: ...

    async def save(self, version: EnvironmentVersionRecord) -> None: ...


# ── Errors ─────────────────────────────────────────────────────────────────


class EnvironmentVersionNotFoundError(RuntimeError):
    """Raised when a version cannot be found within the owning project."""


# ── Commands ───────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class CreateEnvironmentVersionCommand:
    template_id: EnvironmentTemplateId
    project_id: ProjectId
    config: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class UpdateEnvironmentVersionCommand:
    version_id: UUID
    template_id: EnvironmentTemplateId
    project_id: ProjectId
    config: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class PublishEnvironmentVersionCommand:
    version_id: UUID
    template_id: EnvironmentTemplateId
    project_id: ProjectId


# ── Handlers ───────────────────────────────────────────────────────────────


class ListEnvironmentVersionsHandler:
    """Query versions of an environment template."""

    def __init__(
        self,
        *,
        versions: EnvironmentVersionRepository,
        templates: EnvironmentTemplateRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._versions = versions
        self._templates = templates
        self._project_access = project_access

    async def execute(
        self,
        actor: User,
        template_id: EnvironmentTemplateId,
        project_id: ProjectId,
    ) -> list[EnvironmentVersionRecord]:
        await self._project_access.ensure_member(actor, project_id)
        template = await self._templates.get_by_id_and_project(template_id, project_id)
        if template is None:
            raise EnvironmentVersionNotFoundError("Environment template not found")
        return await self._versions.list_by_template(template_id, project_id)


class GetEnvironmentVersionHandler:
    """Query a single environment version."""

    def __init__(
        self,
        *,
        versions: EnvironmentVersionRepository,
        templates: EnvironmentTemplateRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._versions = versions
        self._templates = templates
        self._project_access = project_access

    async def execute(
        self,
        actor: User,
        version_id: UUID,
        template_id: EnvironmentTemplateId,
        project_id: ProjectId,
    ) -> EnvironmentVersionRecord:
        await self._project_access.ensure_member(actor, project_id)
        template = await self._templates.get_by_id_and_project(template_id, project_id)
        if template is None:
            raise EnvironmentVersionNotFoundError("Environment template not found")
        record = await self._versions.get_by_id(version_id, project_id)
        if record is None or record.environment_template_id != template_id.value:
            raise EnvironmentVersionNotFoundError("Version not found")
        return record


class CreateEnvironmentVersionHandler:
    """Create a new draft version of an environment template."""

    def __init__(
        self,
        *,
        versions: EnvironmentVersionRepository,
        templates: EnvironmentTemplateRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._versions = versions
        self._templates = templates
        self._project_access = project_access
        self._audit = audit

    async def execute(
        self,
        actor: User,
        command: CreateEnvironmentVersionCommand,
    ) -> EnvironmentVersionRecord:
        await self._project_access.ensure_editor(actor, command.project_id)
        template = await self._templates.get_by_id_and_project(
            command.template_id, command.project_id
        )
        if template is None:
            raise EnvironmentVersionNotFoundError("Environment template not found")

        next_number = await self._versions.get_next_version_number(
            command.template_id, command.project_id
        )
        now = datetime.now(UTC)
        record = EnvironmentVersionRecord(
            id=uuid4(),
            project_id=command.project_id.value,
            environment_template_id=command.template_id.value,
            version_number=next_number,
            status="draft",
            config=command.config or {},
            published_at=None,
            created_by=actor.user_id.value,
            created_at=now,
            updated_at=now,
        )
        await self._versions.add(record)

        if self._audit:
            await self._audit.record(
                actor_user_id=actor.user_id,
                action="environment_version.created",
                object_type="environment_version",
                object_id=record.id,  # type: ignore[arg-type]
                project_id=command.project_id,
                changes={},
                source_ip=None,
            )

        return record


class UpdateEnvironmentVersionHandler:
    """Update a draft version's config."""

    def __init__(
        self,
        *,
        versions: EnvironmentVersionRepository,
        templates: EnvironmentTemplateRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._versions = versions
        self._templates = templates
        self._project_access = project_access
        self._audit = audit

    async def execute(
        self,
        actor: User,
        command: UpdateEnvironmentVersionCommand,
    ) -> EnvironmentVersionRecord:
        await self._project_access.ensure_editor(actor, command.project_id)
        template = await self._templates.get_by_id_and_project(
            command.template_id, command.project_id
        )
        if template is None:
            raise EnvironmentVersionNotFoundError("Environment template not found")

        record = await self._versions.get_by_id(command.version_id, command.project_id)
        if record is None or record.environment_template_id != command.template_id.value:
            raise EnvironmentVersionNotFoundError("Version not found")

        if record.status != "draft":
            raise ValueError("Only draft versions can be updated")

        # Create a new record with updated fields (dataclass is frozen)
        updated = EnvironmentVersionRecord(
            id=record.id,
            project_id=record.project_id,
            environment_template_id=record.environment_template_id,
            version_number=record.version_number,
            status=record.status,
            config=command.config if command.config is not None else record.config,
            published_at=record.published_at,
            created_by=record.created_by,
            created_at=record.created_at,
            updated_at=datetime.now(UTC),
        )
        await self._versions.save(updated)

        if self._audit:
            await self._audit.record(
                actor_user_id=actor.user_id,
                action="environment_version.updated",
                object_type="environment_version",
                object_id=updated.id,  # type: ignore[arg-type]
                project_id=command.project_id,
                changes={},
                source_ip=None,
            )

        return updated


class PublishEnvironmentVersionHandler:
    """Publish a draft version, making it immutable."""

    def __init__(
        self,
        *,
        versions: EnvironmentVersionRepository,
        templates: EnvironmentTemplateRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._versions = versions
        self._templates = templates
        self._project_access = project_access
        self._audit = audit

    async def execute(
        self,
        actor: User,
        command: PublishEnvironmentVersionCommand,
    ) -> EnvironmentVersionRecord:
        await self._project_access.ensure_editor(actor, command.project_id)
        template = await self._templates.get_by_id_and_project(
            command.template_id, command.project_id
        )
        if template is None:
            raise EnvironmentVersionNotFoundError("Environment template not found")

        record = await self._versions.get_by_id(command.version_id, command.project_id)
        if record is None or record.environment_template_id != command.template_id.value:
            raise EnvironmentVersionNotFoundError("Version not found")

        if record.status != "draft":
            raise ValueError("Only draft versions can be published")

        published = EnvironmentVersionRecord(
            id=record.id,
            project_id=record.project_id,
            environment_template_id=record.environment_template_id,
            version_number=record.version_number,
            status="published",
            config=record.config,
            published_at=datetime.now(UTC),
            created_by=record.created_by,
            created_at=record.created_at,
            updated_at=datetime.now(UTC),
        )
        await self._versions.save(published)

        if self._audit:
            await self._audit.record(
                actor_user_id=actor.user_id,
                action="environment_version.published",
                object_type="environment_version",
                object_id=published.id,  # type: ignore[arg-type]
                project_id=command.project_id,
                changes={},
                source_ip=None,
            )

        return published
