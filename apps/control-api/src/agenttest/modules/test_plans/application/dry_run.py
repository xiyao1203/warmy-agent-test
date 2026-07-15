from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.public import ProjectAccessPort
from agenttest.modules.test_plans.domain.entities import TestPlanVersion


@dataclass(frozen=True, slots=True)
class DryRunReadModel:
    version: TestPlanVersion
    agent_ready: bool
    dataset_ready: bool
    environment_ready: bool
    num_cases: int


class DryRunReader(Protocol):
    async def get_dry_run_model(
        self,
        project_id: UUID,
        plan_id: UUID,
        version_id: UUID,
    ) -> DryRunReadModel | None: ...


class DryRunVersionNotFound(Exception):
    pass


@dataclass(frozen=True, slots=True)
class DryRunDto:
    version_id: UUID
    status: str
    preview: dict[str, object]
    errors: tuple[str, ...]


class DryRunService:
    def __init__(self, *, reader: DryRunReader, project_access: ProjectAccessPort) -> None:
        self._reader = reader
        self._project_access = project_access

    async def execute(
        self,
        actor: User,
        project_id: UUID,
        plan_id: UUID,
        version_id: UUID,
    ) -> DryRunDto:
        await self._project_access.ensure_editor(actor, ProjectId(project_id))
        model = await self._reader.get_dry_run_model(project_id, plan_id, version_id)
        if model is None:
            raise DryRunVersionNotFound
        errors: list[str] = []
        version = model.version
        if version.agent_version_id is not None and not model.agent_ready:
            errors.append("关联的 Agent 版本不存在或未发布")
        if version.dataset_version_id is not None and not model.dataset_ready:
            errors.append("关联的数据集版本不存在或未发布")
        if version.environment_template_id is not None and not model.environment_ready:
            errors.append("关联的环境模板不存在")
        return DryRunDto(
            version_id=version_id,
            status=version.status.value,
            preview=version.config.dry_run_preview(num_cases=model.num_cases),
            errors=tuple(errors),
        )
