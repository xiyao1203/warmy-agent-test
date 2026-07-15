from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.modules.runs.application.event_stream import RunProgressService
from agenttest.shared.api.auth_guard import require_actor


class ActorResolver(Protocol):
    async def __call__(self, request: Request) -> User | None: ...


@dataclass(frozen=True, slots=True)
class RunStreamApiDependencies:
    progress: RunProgressService
    actor_for: ActorResolver
    settings: Settings


def create_run_stream_router(dependencies: RunStreamApiDependencies) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/runs/{run_id}",
        tags=["run-stream"],
    )

    @router.get("/stream")
    async def stream_run_progress(request: Request, project_id: UUID, run_id: UUID):
        actor = await require_actor(request, dependencies.actor_for, dependencies.settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            initial = await dependencies.progress.get(actor, project_id, run_id)
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})

        async def event_generator():
            current = initial
            last_status: str | None = None
            last_cases: dict[str, int] | None = None
            while True:
                if current is None:
                    yield f"data: {json.dumps({'error': 'Run not found'})}\n\n"
                    break
                cases = current.cases()
                if current.status != last_status or cases != last_cases:
                    yield f"data: {json.dumps({'status': current.status, 'cases': cases})}\n\n"
                    last_status = current.status
                    last_cases = cases
                if current.status in {"passed", "failed", "error", "cancelled"}:
                    completed = {"event": "completed", "status": current.status}
                    yield f"data: {json.dumps(completed)}\n\n"
                    break
                await asyncio.sleep(getattr(dependencies.settings, "run_stream_poll_seconds", 1))
                current = await dependencies.progress.get(actor, project_id, run_id)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    return router
