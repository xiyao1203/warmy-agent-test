"""Project-scoped browser profile API without auth-state disclosure."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from agenttest.modules.browser_profiles.application.auth_state import BrowserAuthStateService
from agenttest.modules.browser_profiles.domain.entities import BrowserProfile


class BrowserProfileRepository(Protocol):
    async def list(self, project_id: UUID) -> list[BrowserProfile]: ...

    async def get(self, project_id: UUID, profile_id: UUID) -> BrowserProfile | None: ...

    async def add(self, item: BrowserProfile) -> None: ...

    async def save(self, item: BrowserProfile) -> None: ...

    async def delete(self, project_id: UUID, profile_id: UUID) -> bool: ...


class BrowserProfileRuntime(Protocol):
    def profile_dir(self, profile_id: UUID) -> str: ...

    async def start(self, profile: BrowserProfile, login_url: str) -> None: ...

    async def stop(self, profile_id: UUID) -> None: ...

    async def export_storage_state(self, profile: BrowserProfile) -> dict: ...

    async def verify(self, profile: BrowserProfile, storage_state: dict) -> bool: ...


@dataclass(frozen=True, slots=True)
class BrowserProfileApiDependencies:
    repository: BrowserProfileRepository
    runtime: BrowserProfileRuntime
    auth_state: BrowserAuthStateService


class CreateBrowserProfileRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    target_domain: str = Field(default="", max_length=500)


class UpdateBrowserProfileRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    target_domain: str | None = Field(default=None, max_length=500)


class StartBrowserProfileRequest(BaseModel):
    login_url: str = Field(default="", max_length=2000)


class CompleteBrowserProfileLoginRequest(BaseModel):
    stop_after_save: bool = False


def create_browser_profile_router(
    *,
    settings,
    actor_for: Callable[[Request], Awaitable[object | None]],
    check_project: Callable[[object, UUID, bool], Awaitable[None]],
    dependencies: BrowserProfileApiDependencies,
) -> APIRouter:
    router = APIRouter(tags=["browser-profiles"])

    async def actor(request: Request) -> object | JSONResponse:
        if not request.cookies.get(settings.session_cookie_name):
            return _error(401, "Unauthorized")
        resolved = await actor_for(request)
        return resolved if resolved is not None else _error(401, "Unauthorized")

    async def authorized(
        request: Request,
        project_id: UUID,
        *,
        write: bool,
        csrf_header: str | None = None,
    ) -> object | JSONResponse:
        resolved = await actor(request)
        if isinstance(resolved, JSONResponse):
            return resolved
        if write:
            csrf_cookie = request.cookies.get("agenttest_csrf")
            if not csrf_header or not csrf_cookie or csrf_header != csrf_cookie:
                return _error(403, "Forbidden")
        try:
            await check_project(resolved, project_id, write)
        except Exception:
            return _error(404, "Project not found")
        return resolved

    @router.get("/api/v1/projects/{project_id}/browser-profiles")
    async def list_profiles(request: Request, project_id: UUID):
        access = await authorized(request, project_id, write=False)
        if isinstance(access, JSONResponse):
            return access
        items = await dependencies.repository.list(project_id)
        return {"items": [item.to_public_dict() for item in items]}

    @router.post("/api/v1/projects/{project_id}/browser-profiles", status_code=201)
    async def create_profile(
        request: Request,
        project_id: UUID,
        body: CreateBrowserProfileRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        access = await authorized(request, project_id, write=True, csrf_header=x_csrf_token)
        if isinstance(access, JSONResponse):
            return access
        item = BrowserProfile.create(
            project_id=project_id,
            name=body.name,
            target_domain=body.target_domain,
            created_by=_actor_id(access),
            now=datetime.now(UTC),
        )
        item.user_data_dir = dependencies.runtime.profile_dir(item.id)
        try:
            await dependencies.repository.add(item)
        except IntegrityError:
            return _error(409, "Browser profile name already exists")
        return item.to_public_dict()

    @router.get("/api/v1/projects/{project_id}/browser-profiles/{profile_id}")
    async def get_profile(request: Request, project_id: UUID, profile_id: UUID):
        access = await authorized(request, project_id, write=False)
        if isinstance(access, JSONResponse):
            return access
        item = await dependencies.repository.get(project_id, profile_id)
        return item.to_public_dict() if item else _error(404, "Profile not found")

    @router.patch("/api/v1/projects/{project_id}/browser-profiles/{profile_id}")
    async def update_profile(
        request: Request,
        project_id: UUID,
        profile_id: UUID,
        body: UpdateBrowserProfileRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        access = await authorized(request, project_id, write=True, csrf_header=x_csrf_token)
        if isinstance(access, JSONResponse):
            return access
        item = await dependencies.repository.get(project_id, profile_id)
        if item is None:
            return _error(404, "Profile not found")
        if body.name is not None:
            item.name = body.name.strip()
        if body.target_domain is not None:
            item.target_domain = body.target_domain.strip()
        item.updated_at = datetime.now(UTC)
        try:
            await dependencies.repository.save(item)
        except IntegrityError:
            return _error(409, "Browser profile name already exists")
        return item.to_public_dict()

    @router.post("/api/v1/projects/{project_id}/browser-profiles/{profile_id}/start")
    async def start_profile(
        request: Request,
        project_id: UUID,
        profile_id: UUID,
        body: StartBrowserProfileRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        access = await authorized(request, project_id, write=True, csrf_header=x_csrf_token)
        if isinstance(access, JSONResponse):
            return access
        item = await dependencies.repository.get(project_id, profile_id)
        if item is None:
            return _error(404, "Profile not found")
        try:
            await dependencies.runtime.start(item, body.login_url)
            item.status = "running"
            item.updated_at = datetime.now(UTC)
            await dependencies.repository.save(item)
        except Exception as error:
            item.status = "error"
            item.cdp_endpoint = ""
            item.updated_at = datetime.now(UTC)
            await dependencies.repository.save(item)
            return _error(503, str(error))
        return item.to_public_dict()

    @router.post("/api/v1/projects/{project_id}/browser-profiles/{profile_id}/login-complete")
    async def complete_login(
        request: Request,
        project_id: UUID,
        profile_id: UUID,
        body: CompleteBrowserProfileLoginRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        access = await authorized(request, project_id, write=True, csrf_header=x_csrf_token)
        if isinstance(access, JSONResponse):
            return access
        item = await dependencies.repository.get(project_id, profile_id)
        if item is None:
            return _error(404, "Profile not found")
        try:
            storage_state = await dependencies.runtime.export_storage_state(item)
            snapshot = dependencies.auth_state.seal(
                project_id=project_id,
                profile_id=profile_id,
                target_domain=item.target_domain,
                storage_state=storage_state,
            )
            item.store_auth_state(
                envelope=snapshot.envelope,
                sha256=snapshot.sha256,
                saved_at=datetime.now(UTC),
            )
            await dependencies.repository.save(item)
            if body.stop_after_save:
                await dependencies.runtime.stop(profile_id)
                item.status = "stopped"
                item.cdp_endpoint = ""
                item.updated_at = datetime.now(UTC)
                await dependencies.repository.save(item)
        except Exception as error:
            item.auth_state_status = "error"
            item.updated_at = datetime.now(UTC)
            await dependencies.repository.save(item)
            return _error(422, str(error))
        return item.to_public_dict()

    @router.post("/api/v1/projects/{project_id}/browser-profiles/{profile_id}/verify")
    async def verify_profile(
        request: Request,
        project_id: UUID,
        profile_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        access = await authorized(request, project_id, write=True, csrf_header=x_csrf_token)
        if isinstance(access, JSONResponse):
            return access
        item = await dependencies.repository.get(project_id, profile_id)
        if item is None:
            return _error(404, "Profile not found")
        if not item.auth_state_envelope:
            return _error(409, "Browser profile has no saved auth state")
        try:
            storage_state = dependencies.auth_state.open(
                project_id, profile_id, item.auth_state_envelope
            )
            verified_at = datetime.now(UTC)
            if await dependencies.runtime.verify(item, storage_state):
                item.mark_auth_ready(verified_at)
            else:
                item.auth_state_status = "expired"
                item.last_verified_at = verified_at
                item.updated_at = verified_at
            await dependencies.repository.save(item)
        except Exception as error:
            item.auth_state_status = "error"
            item.updated_at = datetime.now(UTC)
            await dependencies.repository.save(item)
            return _error(422, str(error))
        return item.to_public_dict()

    @router.post("/api/v1/projects/{project_id}/browser-profiles/{profile_id}/stop")
    async def stop_profile(
        request: Request,
        project_id: UUID,
        profile_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        access = await authorized(request, project_id, write=True, csrf_header=x_csrf_token)
        if isinstance(access, JSONResponse):
            return access
        item = await dependencies.repository.get(project_id, profile_id)
        if item is None:
            return _error(404, "Profile not found")
        await dependencies.runtime.stop(profile_id)
        item.status = "stopped"
        item.cdp_endpoint = ""
        item.updated_at = datetime.now(UTC)
        await dependencies.repository.save(item)
        return item.to_public_dict()

    @router.delete("/api/v1/projects/{project_id}/browser-profiles/{profile_id}", status_code=204)
    async def delete_profile(
        request: Request,
        project_id: UUID,
        profile_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        access = await authorized(request, project_id, write=True, csrf_header=x_csrf_token)
        if isinstance(access, JSONResponse):
            return access
        item = await dependencies.repository.get(project_id, profile_id)
        if item is None:
            return _error(404, "Profile not found")
        await dependencies.runtime.stop(profile_id)
        if not await dependencies.repository.delete(project_id, profile_id):
            return _error(404, "Profile not found")
        return Response(status_code=204)

    return router


def _actor_id(actor: object) -> UUID:
    user_id = getattr(actor, "user_id", None)
    value = getattr(user_id, "value", user_id)
    if not isinstance(value, UUID):
        raise ValueError("Invalid actor id")
    return value


def _error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})
