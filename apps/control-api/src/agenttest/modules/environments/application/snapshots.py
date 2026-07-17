from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4

from agenttest.modules.environments.domain.entities import (
    EnvironmentTemplate,
    EnvironmentTemplateId,
)
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.shared.domain.clock import Clock


class EnvironmentTemplateStore(Protocol):
    async def get_by_id_and_project(
        self,
        template_id: EnvironmentTemplateId,
        project_id: ProjectId,
    ) -> EnvironmentTemplate | None: ...

    async def save(self, template: EnvironmentTemplate) -> None: ...


class ProjectAccess(Protocol):
    async def ensure_member(self, actor: User, project_id: ProjectId) -> None: ...

    async def ensure_editor(self, actor: User, project_id: ProjectId) -> None: ...


class EnvironmentTemplateNotFound(Exception):
    pass


class EnvironmentSnapshotNotFound(Exception):
    pass


@dataclass(frozen=True, slots=True)
class EnvironmentSnapshotDto:
    snapshot_id: str
    name: str
    created_at: str


class EnvironmentSnapshotService:
    def __init__(
        self,
        *,
        templates: EnvironmentTemplateStore,
        project_access: ProjectAccess,
        clock: Clock,
    ) -> None:
        self._templates = templates
        self._project_access = project_access
        self._clock = clock

    async def create(
        self,
        actor: User,
        project_id: UUID,
        template_id: UUID,
    ) -> EnvironmentSnapshotDto:
        project = ProjectId(project_id)
        await self._project_access.ensure_editor(actor, project)
        template = await self._template(project, template_id)
        now = self._clock.now()
        snapshot: dict[str, object] = {
            "id": str(uuid4()),
            "name": f"snapshot-{now.strftime('%Y%m%d-%H%M%S')}",
            "config": dict(template.config),
            "created_at": now.isoformat(),
        }
        snapshots = _snapshots(template)
        snapshots.append(snapshot)
        template.config["snapshots"] = snapshots
        await self._templates.save(template)
        return _to_dto(snapshot)

    async def list(
        self,
        actor: User,
        project_id: UUID,
        template_id: UUID,
    ) -> list[EnvironmentSnapshotDto]:
        project = ProjectId(project_id)
        await self._project_access.ensure_member(actor, project)
        return [_to_dto(item) for item in _snapshots(await self._template(project, template_id))]

    async def restore(
        self,
        actor: User,
        project_id: UUID,
        template_id: UUID,
        snapshot_id: str,
    ) -> None:
        project = ProjectId(project_id)
        await self._project_access.ensure_editor(actor, project)
        template = await self._template(project, template_id)
        snapshots = _snapshots(template)
        snapshot = next((item for item in snapshots if item.get("id") == snapshot_id), None)
        if snapshot is None:
            raise EnvironmentSnapshotNotFound
        config = snapshot.get("config")
        template.config = dict(config) if isinstance(config, dict) else {}
        template.config["snapshots"] = snapshots
        await self._templates.save(template)

    async def delete(
        self,
        actor: User,
        project_id: UUID,
        template_id: UUID,
        snapshot_id: str,
    ) -> None:
        project = ProjectId(project_id)
        await self._project_access.ensure_editor(actor, project)
        template = await self._template(project, template_id)
        template.config["snapshots"] = [
            item for item in _snapshots(template) if item.get("id") != snapshot_id
        ]
        await self._templates.save(template)

    async def _template(
        self,
        project_id: ProjectId,
        template_id: UUID,
    ) -> EnvironmentTemplate:
        template = await self._templates.get_by_id_and_project(
            EnvironmentTemplateId(template_id),
            project_id,
        )
        if template is None:
            raise EnvironmentTemplateNotFound
        return template


def _snapshots(template: EnvironmentTemplate) -> list[dict[str, object]]:
    value = template.config.get("snapshots", [])
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _to_dto(snapshot: dict[str, object]) -> EnvironmentSnapshotDto:
    return EnvironmentSnapshotDto(
        snapshot_id=str(snapshot.get("id") or ""),
        name=str(snapshot.get("name") or ""),
        created_at=str(snapshot.get("created_at") or ""),
    )
