from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.modules.test_plans.application.dry_run import (
    DryRunService,
    DryRunVersionNotFound,
)
from agenttest.shared.api.auth_guard import require_writer


class ActorResolver(Protocol):
    async def __call__(self, request: Request) -> User | None: ...


@dataclass(frozen=True, slots=True)
class DryRunApiDependencies:
    service: DryRunService
    actor_for: ActorResolver
    settings: Settings


def create_dry_run_router(dependencies: DryRunApiDependencies) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/test-plans/{plan_id}/versions/{version_id}/dry-run",
        tags=["test-plan-dry-run"],
    )

    @router.post("")
    async def dry_run(
        request: Request,
        project_id: UUID,
        plan_id: UUID,
        version_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            result = await dependencies.service.execute(
                actor,
                project_id,
                plan_id,
                version_id,
            )
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})
        except PermissionError:
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        except DryRunVersionNotFound:
            return JSONResponse(status_code=404, content={"detail": "测试计划版本不存在"})
        return {
            "version_id": str(result.version_id),
            "status": result.status,
            "preview": result.preview,
            "validation": {
                "valid": not result.errors,
                "errors": list(result.errors),
            },
        }

    return router
