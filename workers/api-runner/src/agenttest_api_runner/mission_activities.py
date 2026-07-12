from __future__ import annotations

import os

import httpx
from temporalio import activity

from .mission_contracts import MissionStageResponse, MissionStageTask


@activity.defn
async def execute_mission_stage(task: MissionStageTask) -> MissionStageResponse:
    token = os.environ.get("AGENTTEST_INTERNAL_API_TOKEN")
    if not token:
        raise RuntimeError("Mission Activity requires AGENTTEST_INTERNAL_API_TOKEN")
    mission = task.mission
    url = (
        f"{mission.callback_base_url.rstrip('/')}/api/v1/internal/projects/"
        f"{mission.project_id}/test-missions/{mission.mission_id}/revisions/"
        f"{mission.revision_id}/stages/{task.stage}"
    )
    async with httpx.AsyncClient(timeout=90.0, trust_env=False) as client:
        response = await client.post(
            url,
            headers={"X-Internal-Token": token},
            json={
                "revision_hash": mission.revision_hash,
                "idempotency_key": f"{mission.idempotency_key}:{task.stage}",
                "resume_attempt": task.resume_attempt,
            },
        )
    if response.status_code >= 500:
        raise RuntimeError(f"Mission stage service unavailable ({response.status_code})")
    if response.status_code >= 400:
        return MissionStageResponse(
            status="failed",
            error_type="platform_error",
            error_message=f"Mission stage rejected ({response.status_code})",
        )
    payload = response.json()
    return MissionStageResponse(
        status=str(payload.get("status") or "failed"),
        output=dict(payload.get("output") or {}),
        error_type=str(payload["error_type"]) if payload.get("error_type") else None,
        error_message=(str(payload["error_message"]) if payload.get("error_message") else None),
    )
