from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_missions.application.intake import MissionIntake
from agenttest.modules.test_missions.application.ports import MissionRepository
from agenttest.modules.test_missions.application.preflight import (
    MissionPreflight,
    MissionPreview,
)
from agenttest.modules.test_missions.domain.entities import TestMission
from agenttest.modules.test_missions.domain.value_objects import (
    MissionRevision,
    MissionStatus,
    canonical_snapshot_hash,
)


class MissionPreviewChangedError(ValueError):
    pass


class MissionRuntime(Protocol):
    async def start(
        self, mission: TestMission, revision: MissionRevision, idempotency_key: str
    ) -> str: ...


@dataclass(frozen=True, slots=True)
class MissionPreviewResult:
    mission_id: UUID
    preview: MissionPreview
    revision_hash: str | None
    snapshot: dict[str, object] | None


@dataclass(frozen=True, slots=True)
class ConfirmMissionResult:
    mission: TestMission
    revision: MissionRevision
    workflow_id: str


class UpsertMissionHandler:
    def __init__(self, repository: MissionRepository, intake: MissionIntake) -> None:
        self._repository = repository
        self._intake = intake

    async def execute(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        session_id: UUID,
        values: dict[str, object],
    ) -> TestMission:
        mission = await self._repository.get_for_session(project_id.value, session_id)
        created = mission is None
        if mission is None:
            mission = TestMission.create(
                project_id=project_id.value,
                session_id=session_id,
                created_by=actor.user_id.value,
            )
        elif mission.status not in {
            MissionStatus.COLLECTING,
            MissionStatus.NEEDS_INPUT,
            MissionStatus.DISCOVERING,
            MissionStatus.READY_FOR_CONFIRMATION,
        }:
            mission.reopen_for_revision()
        expected_lock = mission.lock_version
        changed = self._intake.merge_raw(mission, values)
        if created:
            await self._repository.add(mission)
        elif mission.lock_version != expected_lock:
            await self._repository.save(mission, expected_lock_version=expected_lock)
        if created or changed:
            await self._repository.append_event(
                project_id.value,
                mission.mission_id,
                "mission.created" if created else "mission.updated",
                {"changed_fields": list(changed), "status": mission.status.value},
            )
        return mission


class PreviewMissionHandler:
    def __init__(self, repository: MissionRepository, preflight: MissionPreflight) -> None:
        self._repository = repository
        self._preflight = preflight

    async def execute(
        self, actor: User, project_id: UUID, mission_id: UUID
    ) -> MissionPreviewResult:
        del actor
        mission = await _required_mission(self._repository, project_id, mission_id)
        preview = self._preflight.evaluate(mission)
        if not preview.ready:
            return MissionPreviewResult(mission_id, preview, None, None)
        snapshot = _snapshot_for(mission, preview)
        return MissionPreviewResult(
            mission_id=mission_id,
            preview=preview,
            revision_hash=canonical_snapshot_hash(snapshot),
            snapshot=snapshot,
        )


class ConfirmMissionHandler:
    def __init__(
        self,
        repository: MissionRepository,
        preflight: MissionPreflight,
        runtime: MissionRuntime,
    ) -> None:
        self._repository = repository
        self._preflight = preflight
        self._runtime = runtime

    async def execute(
        self,
        actor: User,
        project_id: UUID,
        mission_id: UUID,
        *,
        revision_hash: str,
        idempotency_key: str,
    ) -> ConfirmMissionResult:
        mission = await _required_mission(self._repository, project_id, mission_id)
        current = _active_revision(mission)
        if current is not None:
            if current.content_hash != revision_hash:
                raise MissionPreviewChangedError("Mission preview has changed")
            if mission.workflow_id:
                return ConfirmMissionResult(mission, current, mission.workflow_id)
            return await self._start_existing(mission, current, idempotency_key)

        preview = self._preflight.evaluate(mission)
        if not preview.ready:
            raise ValueError("Mission still requires input")
        snapshot = _snapshot_for(mission, preview)
        if canonical_snapshot_hash(snapshot) != revision_hash:
            raise MissionPreviewChangedError("Mission preview has changed")
        expected_lock = mission.lock_version
        revision = mission.confirm(
            confirmed_by=actor.user_id.value,
            execution=dict(snapshot["execution"]),
            budget=dict(snapshot["budget"]),
            action_allowlist=list(snapshot["action_allowlist"]),
        )
        await self._repository.save(mission, expected_lock_version=expected_lock)
        await self._repository.append_event(
            project_id,
            mission_id,
            "mission.confirmed",
            {
                "revision_id": str(revision.revision_id),
                "revision_hash": revision.content_hash,
                "confirmed_by": str(actor.user_id.value),
            },
        )
        return await self._start_existing(mission, revision, idempotency_key)

    async def _start_existing(
        self,
        mission: TestMission,
        revision: MissionRevision,
        idempotency_key: str,
    ) -> ConfirmMissionResult:
        workflow_id = await self._runtime.start(mission, revision, idempotency_key)
        expected_lock = mission.lock_version
        mission.mark_provisioning(workflow_id)
        await self._repository.save(mission, expected_lock_version=expected_lock)
        await self._repository.append_event(
            mission.project_id,
            mission.mission_id,
            "mission.started",
            {"revision_id": str(revision.revision_id), "workflow_id": workflow_id},
        )
        return ConfirmMissionResult(mission, revision, workflow_id)


async def _required_mission(
    repository: MissionRepository, project_id: UUID, mission_id: UUID
) -> TestMission:
    mission = await repository.get(project_id, mission_id)
    if mission is None:
        raise LookupError("Mission does not exist in project")
    return mission


def _active_revision(mission: TestMission) -> MissionRevision | None:
    if mission.active_revision_id is None:
        return None
    return next(
        (
            revision
            for revision in mission.revisions
            if revision.revision_id == mission.active_revision_id
        ),
        None,
    )


def _snapshot_for(mission: TestMission, preview: MissionPreview) -> dict[str, Any]:
    return mission.preview_snapshot(
        execution={
            "channels": list(preview.execution_channels),
            "scenarios": list(preview.inferred_scenarios),
        },
        budget={"max_cases": 50, "soft_cost": 15, "hard_cost": 20},
        action_allowlist=list(preview.action_allowlist),
    )
