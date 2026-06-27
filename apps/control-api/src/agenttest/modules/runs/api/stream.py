"""SSE 实时进度端点。"""

from __future__ import annotations

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import text

from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.shared.api.auth_guard import require_actor


def create_run_stream_router(
    *, session_factory, actor_for, check_project, settings,
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/runs/{run_id}",
        tags=["run-stream"],
    )

    @router.get("/stream")
    async def stream_run_progress(
        request: Request,
        project_id: UUID,
        run_id: UUID,
    ):
        """SSE 端点：实时推送运行进度。"""
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, dict):
            # JSONResponse error
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})

        async def event_generator():
            last_status = None
            last_cases = None
            while True:
                async with session_factory() as session:
                    result = await session.execute(
                        text(
                            "SELECT status, passed_cases, failed_cases, "
                            "error_cases, cancelled_cases, total_cases "
                            "FROM runs WHERE id = :rid AND project_id = :pid"
                        ),
                        {"rid": run_id, "pid": project_id},
                    )
                    row = result.mappings().first()

                if row is None:
                    yield f"data: {json.dumps({'error': 'Run not found'})}\n\n"
                    break

                status = row["status"]
                cases = {
                    "passed": row["passed_cases"],
                    "failed": row["failed_cases"],
                    "error": row["error_cases"],
                    "cancelled": row["cancelled_cases"],
                    "total": row["total_cases"],
                }

                if status != last_status or cases != last_cases:
                    yield f"data: {json.dumps({'status': status, 'cases': cases})}\n\n"
                    last_status = status
                    last_cases = cases

                if status in ("passed", "failed", "error", "cancelled"):
                    yield f"data: {json.dumps({'event': 'completed', 'status': status})}\n\n"
                    break

                await asyncio.sleep(2)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    return router
