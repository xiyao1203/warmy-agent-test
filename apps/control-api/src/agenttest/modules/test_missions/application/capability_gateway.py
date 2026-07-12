from __future__ import annotations

from typing import Protocol
from uuid import UUID

from pydantic import BaseModel

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_missions.application.commands import (
    ConfirmMissionHandler,
    DiscoverMissionHandler,
    PreviewMissionHandler,
    UpsertMissionHandler,
)
from agenttest.modules.test_missions.application.queries import GetMissionHandler


class MissionCapabilityContext(Protocol):
    actor: User
    project_id: ProjectId
    session_id: UUID


class MissionCapabilityGateway:
    def __init__(
        self,
        *,
        upsert: UpsertMissionHandler,
        discover: DiscoverMissionHandler,
        preview: PreviewMissionHandler,
        confirm: ConfirmMissionHandler,
        get: GetMissionHandler,
    ) -> None:
        self._upsert = upsert
        self._discover = discover
        self._preview = preview
        self._confirm = confirm
        self._get = get

    async def execute(
        self, capability: str, context: MissionCapabilityContext, payload: BaseModel
    ) -> dict[str, object]:
        actor = context.actor
        project_id = context.project_id
        session_id = context.session_id
        values = payload.model_dump(exclude_none=True)
        if capability == "test_missions.create_or_update":
            mission = await self._upsert.execute(
                actor, project_id, session_id=session_id, values=values
            )
            return _mission_result(mission)
        mission_id = _uuid(values["mission_id"])
        discovery = None
        if capability == "test_missions.discover":
            discovery = await self._discover.execute(actor, project_id.value, mission_id)
        if capability in {"test_missions.discover", "test_missions.preview"}:
            preview = await self._preview.execute(actor, project_id.value, mission_id)
            return {
                "mission_id": str(mission_id),
                "ready": preview.preview.ready,
                "missing_inputs": [
                    {"key": item.key, "reason": item.reason}
                    for item in preview.preview.missing_inputs
                ],
                "execution_channels": list(preview.preview.execution_channels),
                "action_allowlist": list(preview.preview.action_allowlist),
                "revision_hash": preview.revision_hash,
                "discovery": (
                    {
                        "capabilities": list(discovery.capabilities),
                        "api_available": discovery.api_available,
                        "browser_available": discovery.browser_available,
                        "login_valid": discovery.login_valid,
                    }
                    if discovery is not None
                    else None
                ),
                "artifacts": [_artifact("test_mission", mission_id, "updated")],
            }
        if capability == "test_missions.get_status":
            mission, _, assets = await self._get.execute(actor, project_id.value, mission_id)
            return {**_mission_result(mission), "linked_assets": assets}
        if capability == "test_missions.confirm_and_start":
            result = await self._confirm.execute(
                actor,
                project_id.value,
                mission_id,
                revision_hash=str(values["revision_hash"]),
                idempotency_key=str(values["idempotency_key"]),
            )
            return {
                **_mission_result(result.mission),
                "revision_id": str(result.revision.revision_id),
                "workflow_id": result.workflow_id,
            }
        raise KeyError(f"Unsupported Mission capability: {capability}")


def _mission_result(mission) -> dict[str, object]:
    return {
        "mission_id": str(mission.mission_id),
        "status": mission.status.value,
        "missing_fields": [
            key
            for key in ("target", "access", "test_goal", "safety_scope")
            if key not in mission.facts or not mission.facts[key].verified
        ],
        "artifacts": [_artifact("test_mission", mission.mission_id, "updated")],
    }


def _artifact(kind, value, relation):
    return {"type": kind, "id": str(value), "relation": relation}


def _uuid(value):
    return UUID(str(value))
