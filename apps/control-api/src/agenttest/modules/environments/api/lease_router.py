"""Internal credential redemption scoped to an active run case."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class LeaseService(Protocol):
    async def redeem(
        self, project_id: UUID, credential_ids: list[UUID]
    ) -> dict[str, str]: ...


class RedeemCredentialLeaseRequest(BaseModel):
    run_id: UUID
    run_case_id: UUID
    binding_ids: list[UUID] = Field(min_length=1, max_length=20)


def create_credential_lease_router(
    *,
    internal_token: str,
    service: LeaseService,
    scope_check: Callable[[UUID, UUID, UUID], Awaitable[bool]],
) -> APIRouter:
    router = APIRouter(prefix="/internal/projects/{project_id}", tags=["internal"])

    @router.post("/credential-leases:redeem")
    async def redeem(
        project_id: UUID,
        body: RedeemCredentialLeaseRequest,
        x_internal_token: str | None = Header(default=None),
    ):
        if x_internal_token != internal_token:
            return JSONResponse(status_code=403, content={"detail": "Permission denied"})
        if not await scope_check(project_id, body.run_id, body.run_case_id):
            return JSONResponse(status_code=404, content={"detail": "Run case not found"})
        try:
            values = await service.redeem(project_id, body.binding_ids)
        except PermissionError:
            return JSONResponse(status_code=404, content={"detail": "Credential not found"})
        except RuntimeError as error:
            return JSONResponse(status_code=503, content={"detail": str(error)})
        return {"values": values}

    return router
