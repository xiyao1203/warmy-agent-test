from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.modules.runs.application.comparison import (
    RunComparisonNotFound,
    RunComparisonService,
)
from agenttest.shared.api.auth_guard import require_actor


class ActorResolver(Protocol):
    async def __call__(self, request: Request) -> User | None: ...


@dataclass(frozen=True, slots=True)
class TraceDiffApiDependencies:
    compare: RunComparisonService
    actor_for: ActorResolver
    settings: Settings


def create_trace_diff_router(dependencies: TraceDiffApiDependencies) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/runs/{run_a_id}/diff/{run_b_id}",
        tags=["trace-diff"],
    )

    @router.get("")
    async def diff_runs(
        request: Request,
        project_id: UUID,
        run_a_id: UUID,
        run_b_id: UUID,
    ):
        actor = await require_actor(request, dependencies.actor_for, dependencies.settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            result = await dependencies.compare.compare(
                actor,
                project_id,
                run_a_id,
                run_b_id,
            )
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        except RunComparisonNotFound as error:
            return JSONResponse(
                status_code=404,
                content={"detail": f"运行 {error.run_id} 不存在"},
            )
        return {
            "run_a": result.run_a,
            "run_b": result.run_b,
            "case_diffs": result.case_diffs,
            "summary": result.summary,
        }

    return router
