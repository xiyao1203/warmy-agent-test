"""TestAccount CRUD API 路由。"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agenttest.modules.identity.public import InvalidSessionError
from agenttest.modules.projects.public import ProjectNotFoundError
from agenttest.modules.test_accounts.domain.entities import (
    TestAccount,
    TestAccountId,
)
from agenttest.modules.test_accounts.infrastructure.persistence.repositories import (
    SqlAlchemyTestAccountRepository,
)
from agenttest.shared.api.auth_guard import require_actor, require_writer


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


def create_test_account_router(
    *,
    session_factory,
    actor_for,
    check_project,
    settings,
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/test-accounts",
        tags=["test-accounts"],
    )

    repo = SqlAlchemyTestAccountRepository(session_factory)

    @router.get("")
    async def list_accounts(request: Request, project_id: UUID):
        actor = await require_actor(request, actor_for, settings)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})
        accounts = await repo.list_by_project(project_id)
        return {"items": [_to_dict(a) for a in accounts]}

    @router.post("")
    async def create_account(
        request: Request,
        project_id: UUID,
        body: CreateAccountRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await check_project(project_id)
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "项目不存在"})
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "认证失败"})
        try:
            account = TestAccount.create(
                project_id=project_id,
                name=body.name,
                username=body.username,
                credential_encrypted=body.credential_encrypted,
                account_type=body.account_type,
                description=body.description,
            )
        except ValueError as e:
            return JSONResponse(status_code=422, content={"detail": str(e)})
        await repo.add(account)
        return _to_dict(account)

    @router.patch("/{account_id}")
    async def update_account(
        request: Request,
        project_id: UUID,
        account_id: UUID,
        body: UpdateAccountRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        account = await repo.get_by_id_and_project(
            TestAccountId(account_id),
            project_id,
        )
        if account is None:
            return JSONResponse(status_code=404, content={"detail": "账号不存在"})
        if body.credential_encrypted is not None:
            account.update_credential(body.credential_encrypted)
        if body.enabled is not None and body.enabled != account.enabled:
            account.toggle()
        await repo.save(account)
        return _to_dict(account)

    @router.delete("/{account_id}")
    async def delete_account(
        request: Request,
        project_id: UUID,
        account_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        actor = await require_writer(request, actor_for, settings, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        account = await repo.get_by_id_and_project(
            TestAccountId(account_id),
            project_id,
        )
        if account is None:
            return JSONResponse(status_code=404, content={"detail": "账号不存在"})
        await repo.delete(TestAccountId(account_id))
        return {"status": "deleted", "account_id": str(account_id)}

    return router


def _to_dict(a: TestAccount) -> dict[str, object]:
    return {
        "id": str(a.account_id.value),
        "project_id": str(a.project_id),
        "name": a.name,
        "username": a.username,
        "credential_encrypted": "••••••••",
        "account_type": a.account_type,
        "enabled": a.enabled,
        "description": a.description,
        "created_at": a.created_at.isoformat(),
        "updated_at": a.updated_at.isoformat(),
    }
