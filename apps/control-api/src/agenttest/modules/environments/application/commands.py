"""Environment template application command handlers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from agenttest.modules.audit.public import AuditWriter
from agenttest.modules.environments.application.ports import ProjectAccessPort
from agenttest.modules.environments.domain.entities import (
    EnvironmentTemplate,
    EnvironmentTemplateId,
)
from agenttest.modules.environments.domain.repositories import (
    EnvironmentTemplateRepository,
)
from agenttest.modules.environments.domain.value_objects import TemplateType
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId

# ── Commands ────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class CreateEnvironmentTemplateCommand:
    project_id: ProjectId
    name: str
    template_type: TemplateType
    config: dict[str, object] | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateEnvironmentTemplateCommand:
    template_id: EnvironmentTemplateId
    name: str | None = None
    description: str | None = None
    config: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class DeleteEnvironmentTemplateCommand:
    template_id: EnvironmentTemplateId


# ── Handlers ────────────────────────────────────────────────────────────────


class CreateEnvironmentTemplateHandler:
    def __init__(
        self,
        *,
        templates: EnvironmentTemplateRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._templates = templates
        self._project_access = project_access
        self._audit = audit

    async def execute(
        self, actor: User, command: CreateEnvironmentTemplateCommand
    ) -> EnvironmentTemplate:
        await self._project_access.ensure_editor(actor, command.project_id)
        template = EnvironmentTemplate.create(
            template_id=EnvironmentTemplateId.new(),
            project_id=command.project_id,
            name=command.name,
            template_type=command.template_type,
            created_by=actor.user_id,
            config=command.config,
            description=command.description,
        )
        await self._templates.add(template)
        await _record(
            self._audit,
            actor=actor,
            action="environments.created",
            project_id=command.project_id,
            object_type="environment_template",
            object_id=template.template_id.value,
            changes={"name": {"after": template.name}},
        )
        return template


class UpdateEnvironmentTemplateHandler:
    def __init__(
        self,
        *,
        templates: EnvironmentTemplateRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._templates = templates
        self._project_access = project_access
        self._audit = audit

    async def execute(
        self, actor: User, command: UpdateEnvironmentTemplateCommand
    ) -> EnvironmentTemplate:
        template = await _required(self._templates, command.template_id)
        await self._project_access.ensure_editor(actor, template.project_id)
        changes: dict[str, dict[str, str]] = {}
        if command.name is not None:
            before = template.name
            template.rename(command.name)
            changes["name"] = {"before": before, "after": template.name}
        if command.description is not None:
            before = template.description or ""
            template.update_description(command.description)
            changes["description"] = {"before": before, "after": template.description or ""}
        if command.config is not None:
            template.update_config(command.config)
        await self._templates.save(template)
        await _record(
            self._audit,
            actor=actor,
            action="environments.updated",
            project_id=template.project_id,
            object_type="environment_template",
            object_id=template.template_id.value,
            changes=changes,
        )
        return template


class DeleteEnvironmentTemplateHandler:
    def __init__(
        self,
        *,
        templates: EnvironmentTemplateRepository,
        project_access: ProjectAccessPort,
        audit: AuditWriter | None = None,
    ) -> None:
        self._templates = templates
        self._project_access = project_access
        self._audit = audit

    async def execute(self, actor: User, command: DeleteEnvironmentTemplateCommand) -> None:
        template = await _required(self._templates, command.template_id)
        await self._project_access.ensure_editor(actor, template.project_id)
        await self._templates.delete(template.template_id)
        await _record(
            self._audit,
            actor=actor,
            action="environments.deleted",
            project_id=template.project_id,
            object_type="environment_template",
            object_id=template.template_id.value,
            changes={},
        )


# ── Helpers ─────────────────────────────────────────────────────────────────


async def _required(
    repo: EnvironmentTemplateRepository, template_id: EnvironmentTemplateId
) -> EnvironmentTemplate:
    template = await repo.get_by_id(template_id)
    if template is None:
        raise EnvironmentTemplateNotFoundError(template_id)
    return template


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


class EnvironmentTemplateNotFoundError(Exception):
    def __init__(self, template_id: EnvironmentTemplateId) -> None:
        self.template_id = template_id
        super().__init__(f"Environment template {template_id.value} not found")
