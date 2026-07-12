from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from agenttest.modules.identity.public import User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_missions.application.ports import MissionRepository
from agenttest.modules.test_missions.application.stages import (
    MissionNeedsAttention,
    MissionStageService,
)
from agenttest.modules.test_missions.domain.value_objects import MissionRevision


class MissionActorSource(Protocol):
    async def get_by_id(self, user_id: UserId) -> User | None: ...


@dataclass(frozen=True, slots=True)
class StageExecutionResult:
    status: str
    output: dict[str, object]
    error_type: str | None = None
    error_message: str | None = None


class MissionStageController:
    def __init__(
        self,
        repository: MissionRepository,
        stages: MissionStageService,
        users: MissionActorSource,
    ) -> None:
        self._repository = repository
        self._stages = stages
        self._users = users

    async def execute(
        self,
        *,
        project_id: UUID,
        mission_id: UUID,
        revision_id: UUID,
        revision_hash: str,
        stage: str,
        resume_attempt: int = 0,
    ) -> StageExecutionResult:
        mission = await self._repository.get(project_id, mission_id)
        if mission is None:
            raise LookupError("Mission does not exist in project")
        revision = _revision(mission.revisions, revision_id, revision_hash)
        actor = await self._users.get_by_id(UserId(revision.confirmed_by))
        if actor is None:
            raise LookupError("Mission confirming user no longer exists")
        expected_lock = mission.lock_version
        project = ProjectId(project_id)
        if stage not in {"provision", "start_run", "await_run", "close_loop", "cancel"}:
            raise ValueError("Unknown Mission stage")
        try:
            result = await self._execute_stage(
                stage=stage,
                actor=actor,
                project_id=project,
                session_id=mission.session_id,
                revision=revision,
                resume_attempt=resume_attempt,
            )
        except MissionNeedsAttention as error:
            mission.mark_needs_attention(error.error_type)
            result = StageExecutionResult(
                "needs_attention",
                {},
                error_type=error.error_type,
                error_message=str(error),
            )
        except Exception as error:
            mission.fail()
            result = StageExecutionResult(
                "failed",
                {},
                error_type=type(error).__name__,
                error_message=str(error),
            )
        if result.status == "completed" and stage == "start_run":
            mission.mark_running()
        elif result.status == "completed" and stage == "close_loop":
            mission.complete()
        elif result.status == "completed" and stage == "cancel":
            mission.cancel()
        if mission.lock_version != expected_lock:
            await self._repository.save(mission, expected_lock_version=expected_lock)
        await self._repository.append_event(
            project_id,
            mission_id,
            f"mission.stage.{stage}",
            {
                "status": result.status,
                "output": result.output,
                "error_type": result.error_type,
                "error_message": result.error_message,
            },
        )
        return result

    async def _execute_stage(
        self,
        *,
        stage: str,
        actor: User,
        project_id: ProjectId,
        session_id: UUID,
        revision: MissionRevision,
        resume_attempt: int,
    ) -> StageExecutionResult:
        if stage == "provision":
            receipt = await self._stages.provision(
                actor=actor,
                project_id=project_id,
                session_id=session_id,
                revision=revision,
            )
            return StageExecutionResult("completed", receipt.output)
        if stage == "start_run":
            receipt = await self._stages.start_run(
                actor=actor,
                project_id=project_id,
                session_id=session_id,
                revision=revision,
            )
            return StageExecutionResult("completed", receipt.output)
        if stage == "await_run":
            await_receipt = await self._stages.await_run(
                actor=actor,
                project_id=project_id,
                session_id=session_id,
                revision=revision,
                resume_attempt=resume_attempt,
            )
            return (
                StageExecutionResult("running", {})
                if await_receipt is None
                else StageExecutionResult("completed", await_receipt.output)
            )
        if stage == "close_loop":
            receipt = await self._stages.close_loop(
                actor=actor,
                project_id=project_id,
                session_id=session_id,
                revision=revision,
            )
            return StageExecutionResult("completed", receipt.output)
        if stage == "cancel":
            output = await self._stages.cancel_run(
                actor=actor,
                project_id=project_id,
                session_id=session_id,
                revision=revision,
            )
            return StageExecutionResult("completed", output)
        raise ValueError("Unknown Mission stage")


def _revision(
    revisions: list[MissionRevision], revision_id: UUID, revision_hash: str
) -> MissionRevision:
    revision = next((item for item in revisions if item.revision_id == revision_id), None)
    if revision is None or revision.content_hash != revision_hash:
        raise ValueError("Mission revision scope does not match")
    return revision
