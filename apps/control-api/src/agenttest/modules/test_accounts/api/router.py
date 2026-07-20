"""Test-account HTTP adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.modules.test_accounts.application.service import (
    TestAccountNotFound,
    TestAccountService,
    TestAccountValidationError,
)
from agenttest.modules.test_accounts.domain.entities import TestAccount
from agenttest.shared.api.auth_guard import require_actor, require_writer
from agenttest.shared.api.pagination import resolve_page_request
from agenttest.shared.application.pagination import paginate_items


class CreateAccountRequest(BaseModel):
    name: str
    username: str
    credential_encrypted: str
    account_type: str = "user"
    description: str | None = None


class UpdateAccountRequest(BaseModel):
    name: str | None = None
    username: str | None = None
    credential_encrypted: str | None = None
    description: str | None = None
    enabled: bool | None = None


class ActorResolver(Protocol):
    async def __call__(self, request: Request) -> User | None: ...


@dataclass(frozen=True, slots=True)
class TestAccountApiDependencies:
    service: TestAccountService
    actor_for: ActorResolver
    settings: Settings


def create_test_account_router(dependencies: TestAccountApiDependencies) -> APIRouter:
    router = APIRouter(prefix="/projects/{project_id}/test-accounts", tags=["test-accounts"])

    @router.get("")
    async def list_accounts(
        request: Request,
        project_id: UUID,
        page: int | None = Query(default=None),
        page_size: int | None = Query(default=None),
    ):
        actor = await require_actor(request, dependencies.actor_for, dependencies.settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            accounts = await dependencies.service.list(actor, project_id)
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        page_request = resolve_page_request(page=page, page_size=page_size)
        if page_request:
            result = paginate_items(accounts, page_request)
            accounts = result.items
            metadata: dict[str, int | None] = {
                "total": result.total,
                "page": result.page,
                "page_size": result.page_size,
                "total_pages": result.total_pages,
            }
        else:
            metadata = {
                "total": len(accounts),
                "page": None,
                "page_size": 50,
                "total_pages": 1 if accounts else 0,
            }
        return {"items": [_to_dict(account) for account in accounts], **metadata}

    @router.post("")
    async def create_account(
        request: Request,
        project_id: UUID,
        body: CreateAccountRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            account = await dependencies.service.create(
                actor,
                project_id,
                name=body.name,
                username=body.username,
                credential_encrypted=body.credential_encrypted,
                account_type=body.account_type,
                description=body.description,
            )
        except TestAccountValidationError as error:
            return JSONResponse(status_code=422, content={"detail": str(error)})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        return _to_dict(account)

    @router.patch("/{account_id}")
    async def update_account(
        request: Request,
        project_id: UUID,
        account_id: UUID,
        body: UpdateAccountRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            account = await dependencies.service.update(
                actor,
                project_id,
                account_id,
                credential_encrypted=body.credential_encrypted,
                enabled=body.enabled,
            )
        except TestAccountNotFound:
            return JSONResponse(status_code=404, content={"detail": "账号不存在"})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        return _to_dict(account)

    @router.delete("/{account_id}")
    async def delete_account(
        request: Request,
        project_id: UUID,
        account_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(
            request, dependencies.actor_for, dependencies.settings, x_csrf_token
        )
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await dependencies.service.delete(actor, project_id, account_id)
        except TestAccountNotFound:
            return JSONResponse(status_code=404, content={"detail": "账号不存在"})
        except Exception as error:
            response = _access_error(error)
            if response is not None:
                return response
            raise
        return {"status": "deleted", "account_id": str(account_id)}

    return router


def _access_error(error: Exception) -> JSONResponse | None:
    if isinstance(error, InvalidSessionError):
        return JSONResponse(status_code=401, content={"detail": "认证失败"})
    if isinstance(error, PermissionError):
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})
    if isinstance(error, ProjectNotFoundError):
        return JSONResponse(status_code=404, content={"detail": "项目不存在"})
    return None


def _to_dict(account: TestAccount) -> dict[str, object]:
    return {
        "id": str(account.account_id.value),
        "project_id": str(account.project_id),
        "name": account.name,
        "username": account.username,
        "credential_encrypted": "••••••••",
        "account_type": account.account_type,
        "enabled": account.enabled,
        "description": account.description,
        "created_at": account.created_at.isoformat(),
        "updated_at": account.updated_at.isoformat(),
    }
