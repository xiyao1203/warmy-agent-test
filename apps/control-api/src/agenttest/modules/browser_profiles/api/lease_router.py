"""Internal browser auth-state lease endpoint scoped to a RunCase."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agenttest.modules.browser_profiles.application.leases import BrowserSessionLeaseService


class RedeemBrowserSessionRequest(BaseModel):
    run_id: UUID
    run_case_id: UUID
    browser_profile_id: UUID


def create_browser_session_lease_router(
    *, internal_token: str, service: BrowserSessionLeaseService
) -> APIRouter:
    router = APIRouter(prefix="/internal/projects/{project_id}", tags=["internal"])

    @router.post("/browser-session-leases:redeem")
    async def redeem(
        project_id: UUID,
        body: RedeemBrowserSessionRequest,
        x_internal_token: str | None = Header(default=None),
    ):
        if x_internal_token != internal_token:
            return JSONResponse(status_code=403, content={"detail": "Permission denied"})
        try:
            lease = await service.redeem(
                project_id=project_id,
                run_id=body.run_id,
                run_case_id=body.run_case_id,
                browser_profile_id=body.browser_profile_id,
            )
        except PermissionError:
            return JSONResponse(status_code=404, content={"detail": "Run case not found"})
        except RuntimeError as error:
            return JSONResponse(status_code=409, content={"detail": str(error)})
        return {
            "storage_state": lease.storage_state,
            "auth_state_version": lease.auth_state_version,
        }

    return router
