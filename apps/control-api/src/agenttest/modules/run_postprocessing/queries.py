from __future__ import annotations

from typing import Protocol
from uuid import UUID

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.run_postprocessing.application import PIPELINE_VERSION
from agenttest.modules.run_postprocessing.domain import RunPostprocessJob
from agenttest.modules.run_postprocessing.projection import TrustLoopProjection
from agenttest.modules.runs.public import RunId


class RunAccessQuery(Protocol):
    async def execute(self, actor: User, project_id: ProjectId, run_id: RunId) -> object: ...


class TrustLoopQueryRepository(Protocol):
    async def get(
        self, project_id: UUID, run_id: UUID, pipeline_version: str
    ) -> RunPostprocessJob | None: ...

    async def list_diagnostics(
        self,
        project_id: UUID,
        run_id: UUID,
        pipeline_version: str,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, object]], int]: ...

    async def list_regressions(
        self,
        project_id: UUID,
        run_id: UUID,
        pipeline_version: str,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, object]], int]: ...

    async def get_calibration(
        self, project_id: UUID, run_id: UUID, pipeline_version: str
    ) -> dict[str, object] | None: ...

    async def get_joint_gate(
        self, project_id: UUID, run_id: UUID, pipeline_version: str
    ) -> dict[str, object] | None: ...


class RunTrustLoopQueryService:
    def __init__(self, repository: TrustLoopQueryRepository, run_access: RunAccessQuery) -> None:
        self._repository = repository
        self._run_access = run_access

    async def get_summary(self, actor: User, project_id: UUID, run_id: UUID) -> dict[str, object]:
        await self._authorize(actor, project_id, run_id)
        job = await self._repository.get(project_id, run_id, PIPELINE_VERSION)
        if job is not None:
            return TrustLoopProjection.build(job)
        return {
            "job_id": None,
            "project_id": str(project_id),
            "run_id": str(run_id),
            "pipeline_version": PIPELINE_VERSION,
            "status": "pending",
            "current_stage": None,
            "classifications": [],
            "diagnostics": {"status": "inconclusive", "items": []},
            "regressions": [],
            "calibration": {"status": "pending", "metrics": {}},
            "joint_gate": None,
            "warning_codes": [],
            "error_type": None,
            "created_at": None,
            "updated_at": None,
            "completed_at": None,
        }

    async def list_diagnostics(
        self,
        actor: User,
        project_id: UUID,
        run_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, object]], int]:
        await self._authorize(actor, project_id, run_id)
        return await self._repository.list_diagnostics(
            project_id, run_id, PIPELINE_VERSION, limit=limit, offset=offset
        )

    async def list_regressions(
        self,
        actor: User,
        project_id: UUID,
        run_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[dict[str, object]], int]:
        await self._authorize(actor, project_id, run_id)
        return await self._repository.list_regressions(
            project_id, run_id, PIPELINE_VERSION, limit=limit, offset=offset
        )

    async def get_calibration(
        self, actor: User, project_id: UUID, run_id: UUID
    ) -> dict[str, object]:
        await self._authorize(actor, project_id, run_id)
        value = await self._repository.get_calibration(project_id, run_id, PIPELINE_VERSION)
        return value or {
            "id": None,
            "pipeline_version": PIPELINE_VERSION,
            "status": "pending",
            "sample_set_version": None,
            "metrics": {},
            "arbitration": {},
            "evaluator_version": None,
            "created_at": None,
            "updated_at": None,
        }

    async def get_joint_gate(
        self, actor: User, project_id: UUID, run_id: UUID
    ) -> dict[str, object]:
        await self._authorize(actor, project_id, run_id)
        value = await self._repository.get_joint_gate(project_id, run_id, PIPELINE_VERSION)
        if value is not None:
            return {"status": "completed", **value}
        return {
            "id": None,
            "pipeline_version": PIPELINE_VERSION,
            "status": "pending",
            "baseline_run_id": None,
            "decision": None,
            "rules": [],
            "input_facts": {},
            "explanation": None,
            "created_at": None,
        }

    async def _authorize(self, actor: User, project_id: UUID, run_id: UUID) -> None:
        await self._run_access.execute(actor, ProjectId(project_id), RunId(run_id))
