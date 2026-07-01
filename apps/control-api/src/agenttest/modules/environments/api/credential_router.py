from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agenttest.modules.environments.application.credentials import (
    CredentialBindingRecord,
    CredentialBindingService,
)
from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.shared.api.auth_guard import require_actor, require_writer


class CreateCredentialBindingRequest(BaseModel):
    alias: str = Field(min_length=1, max_length=200)
    kind: str = Field(pattern="^(api_key|bearer|basic|cookie|custom)$")
    injection_location: str = Field(pattern="^(header|query|cookie)$")
    injection_name: str = Field(min_length=1, max_length=200)
    value: str = Field(min_length=1, max_length=10000)


def create_credential_router(
    *,
    actor_for,
    check_project,
    settings,
    service: CredentialBindingService,
) -> APIRouter:
    router = APIRouter(prefix="/projects/{project_id}/credentials", tags=["credentials"])

    @router.get("")
    async def list_credentials(request: Request, project_id: UUID):
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})
        rows = await service.list(project_id)
        return {"items": [_response(item) for item in rows]}

    @router.post("", status_code=201)
    async def create_credential(
        request: Request,
        project_id: UUID,
        body: CreateCredentialBindingRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            row = await service.create(
                actor=actor,
                project_id=project_id,
                alias=body.alias,
                kind=body.kind,
                injection_location=body.injection_location,
                injection_name=body.injection_name,
                value=body.value,
                now=datetime.now(UTC),
            )
        except RuntimeError as error:
            return JSONResponse(
                status_code=503,
                content={"detail": str(error)},
            )
        return _response(row)

    @router.delete("/{credential_id}", status_code=204)
    async def delete_credential(
        request: Request,
        project_id: UUID,
        credential_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        if not await service.delete(project_id, credential_id):
            return JSONResponse(status_code=404, content={"detail": "凭证不存在"})
        return JSONResponse(status_code=204, content=None)

    return router


def _response(item: CredentialBindingRecord) -> dict[str, object]:
    return {
        "id": str(item.id),
        "project_id": str(item.project_id),
        "alias": item.alias,
        "kind": item.kind,
        "injection_location": item.injection_location,
        "injection_name": item.injection_name,
        "masked_hint": item.masked_hint,
        "updated_at": item.updated_at.isoformat(),
    }
