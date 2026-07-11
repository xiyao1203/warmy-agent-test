from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agenttest.modules.test_missions.application.stage_controller import (
    MissionStageController,
)


class ExecuteStageRequest(BaseModel):
    revision_hash: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")
    idempotency_key: str = Field(min_length=1, max_length=300)


def create_internal_mission_stage_router(
    *, internal_token: str, controller: MissionStageController
) -> APIRouter:
    router = APIRouter(tags=["internal-test-missions"])

    @router.post(
        "/internal/projects/{project_id}/test-missions/{mission_id}/"
        "revisions/{revision_id}/stages/{stage}"
    )
    async def execute_stage(
        project_id: UUID,
        mission_id: UUID,
        revision_id: UUID,
        stage: str,
        body: ExecuteStageRequest,
        x_internal_token: str | None = Header(default=None),
    ):
        del body.idempotency_key
        if x_internal_token != internal_token:
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        try:
            result = await controller.execute(
                project_id=project_id,
                mission_id=mission_id,
                revision_id=revision_id,
                revision_hash=body.revision_hash,
                stage=stage,
            )
        except LookupError as error:
            return JSONResponse(status_code=404, content={"detail": str(error)})
        except ValueError as error:
            return JSONResponse(status_code=409, content={"detail": str(error)})
        return {
            "status": result.status,
            "output": result.output,
            "error_type": result.error_type,
            "error_message": result.error_message,
        }

    return router
