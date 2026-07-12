from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from agenttest.modules.run_postprocessing.api.schemas import (
    ExecutePostprocessStageRequest,
    PostprocessStageResponse,
)
from agenttest.modules.run_postprocessing.application import PostprocessStageController
from agenttest.modules.run_postprocessing.domain import PostprocessStage
from agenttest.shared.application.uow import UnitOfWorkFactory


def create_internal_postprocess_router(
    *,
    internal_token: str,
    controller: PostprocessStageController,
    uow_factory: UnitOfWorkFactory,
) -> APIRouter:
    router = APIRouter(tags=["internal-run-trust-loop"])

    async def execute(
        project_id: UUID,
        run_id: UUID,
        pipeline_version: str,
        stage: PostprocessStage,
        body: ExecutePostprocessStageRequest,
        token: str | None,
    ) -> PostprocessStageResponse | JSONResponse:
        del body.idempotency_key
        if token != internal_token:
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        try:
            async with uow_factory():
                result = await controller.execute(
                    project_id=project_id,
                    run_id=run_id,
                    pipeline_version=pipeline_version,
                    stage=stage,
                    workflow_id=body.workflow_id,
                    attempt=body.attempt,
                )
        except LookupError:
            return JSONResponse(status_code=404, content={"detail": "Run trust loop not found"})
        except ValueError:
            return JSONResponse(status_code=409, content={"detail": "Invalid stage transition"})
        return PostprocessStageResponse(
            status=result.status,
            output=result.output,
            warning_code=result.warning_code,
        )

    @router.post(
        "/internal/projects/{project_id}/runs/{run_id}/trust-loop/"
        "{pipeline_version}/stages/{stage}",
        response_model=PostprocessStageResponse,
    )
    async def execute_stage(
        project_id: UUID,
        run_id: UUID,
        pipeline_version: str,
        stage: PostprocessStage,
        body: ExecutePostprocessStageRequest,
        x_internal_token: str | None = Header(default=None),
    ) -> PostprocessStageResponse | JSONResponse:
        return await execute(
            project_id,
            run_id,
            pipeline_version,
            stage,
            body,
            x_internal_token,
        )

    @router.post(
        "/internal/projects/{project_id}/runs/{run_id}/trust-loop/{pipeline_version}/finalize",
        response_model=PostprocessStageResponse,
    )
    async def finalize(
        project_id: UUID,
        run_id: UUID,
        pipeline_version: str,
        body: ExecutePostprocessStageRequest,
        x_internal_token: str | None = Header(default=None),
    ) -> PostprocessStageResponse | JSONResponse:
        return await execute(
            project_id,
            run_id,
            pipeline_version,
            PostprocessStage.FINALIZE,
            body,
            x_internal_token,
        )

    return router
