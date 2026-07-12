from __future__ import annotations

import os

import httpx
from temporalio import activity

from .postprocess_contracts import PostprocessStageResponse, PostprocessStageTask


@activity.defn
async def execute_postprocess_stage(task: PostprocessStageTask) -> PostprocessStageResponse:
    token = os.environ.get("AGENTTEST_INTERNAL_API_TOKEN")
    if not token:
        raise RuntimeError("Postprocess Activity requires AGENTTEST_INTERNAL_API_TOKEN")
    workflow = task.workflow
    suffix = "finalize" if task.stage == "finalize" else f"stages/{task.stage}"
    url = (
        f"{workflow.callback_base_url.rstrip('/')}/api/v1/internal/projects/"
        f"{workflow.project_id}/runs/{workflow.run_id}/trust-loop/"
        f"{workflow.pipeline_version}/{suffix}"
    )
    async with httpx.AsyncClient(timeout=90.0, trust_env=False) as client:
        response = await client.post(
            url,
            headers={"X-Internal-Token": token},
            json={
                "idempotency_key": (
                    f"{workflow.run_id}:{workflow.pipeline_version}:{task.stage}:{task.attempt}"
                ),
                "workflow_id": f"run-trust-loop-{workflow.run_id}-{workflow.pipeline_version}",
                "attempt": task.attempt,
            },
        )
    if response.status_code >= 500:
        raise RuntimeError(f"Postprocess stage service unavailable ({response.status_code})")
    if response.status_code >= 400:
        return PostprocessStageResponse("failed")
    payload = response.json()
    raw_output = payload.get("output")
    return PostprocessStageResponse(
        status=str(payload.get("status") or "failed"),
        output=dict(raw_output) if isinstance(raw_output, dict) else {},
        warning_code=(str(payload["warning_code"]) if payload.get("warning_code") else None),
    )
