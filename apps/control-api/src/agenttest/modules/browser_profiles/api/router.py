"""Project-scoped browser-profile HTTP adapter."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from uuid import UUID

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from agenttest.bootstrap.settings import Settings
from agenttest.modules.browser_profiles.application.service import (
    BrowserProfileAuthStateMissing,
    BrowserProfileNotFound,
    BrowserProfileOperationError,
    BrowserProfileService,
    DuplicateBrowserProfile,
)
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectNotFoundError


@dataclass(frozen=True, slots=True)
class BrowserProfileApiDependencies:
    service: BrowserProfileService
    actor_for: Callable[[Request], Awaitable[User | None]]
    settings: Settings


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
    dependencies: BrowserProfileApiDependencies,
) -> APIRouter:
    router = APIRouter(tags=["browser-profiles"])

    async def actor(
        request: Request, *, write: bool, csrf_header: str | None = None
    ) -> User | JSONResponse:
        if not request.cookies.get(dependencies.settings.session_cookie_name):
            return _error(401, "Unauthorized")
        resolved = await dependencies.actor_for(request)
        if resolved is None:
            return _error(401, "Unauthorized")
        if write:
            csrf_cookie = request.cookies.get("agenttest_csrf")
            if not csrf_header or not csrf_cookie or csrf_header != csrf_cookie:
                return _error(403, "Forbidden")
        return resolved

    @router.get("/api/v1/projects/{project_id}/browser-profiles")
    async def list_profiles(request: Request, project_id: UUID):
        resolved = await actor(request, write=False)
        if isinstance(resolved, JSONResponse):
            return resolved
        try:
            items = await dependencies.service.list(resolved, project_id)
        except Exception as error:
            response = _service_error(error)
            if response is not None:
                return response
            raise
        return {"items": [item.to_public_dict() for item in items]}

    @router.post("/api/v1/projects/{project_id}/browser-profiles", status_code=201)
    async def create_profile(
        request: Request,
        project_id: UUID,
        body: CreateBrowserProfileRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        resolved = await actor(request, write=True, csrf_header=x_csrf_token)
        if isinstance(resolved, JSONResponse):
            return resolved
        try:
            item = await dependencies.service.create(
                resolved,
                project_id,
                name=body.name,
                target_domain=body.target_domain,
            )
        except Exception as error:
            response = _service_error(error)
            if response is not None:
                return response
            raise
        return item.to_public_dict()

    @router.get("/api/v1/projects/{project_id}/browser-profiles/{profile_id}")
    async def get_profile(request: Request, project_id: UUID, profile_id: UUID):
        resolved = await actor(request, write=False)
        if isinstance(resolved, JSONResponse):
            return resolved
        try:
            item = await dependencies.service.get(resolved, project_id, profile_id)
        except Exception as error:
            response = _service_error(error)
            if response is not None:
                return response
            raise
        return item.to_public_dict()

    @router.patch("/api/v1/projects/{project_id}/browser-profiles/{profile_id}")
    async def update_profile(
        request: Request,
        project_id: UUID,
        profile_id: UUID,
        body: UpdateBrowserProfileRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        resolved = await actor(request, write=True, csrf_header=x_csrf_token)
        if isinstance(resolved, JSONResponse):
            return resolved
        try:
            item = await dependencies.service.update(
                resolved,
                project_id,
                profile_id,
                name=body.name,
                target_domain=body.target_domain,
            )
        except Exception as error:
            response = _service_error(error)
            if response is not None:
                return response
            raise
        return item.to_public_dict()

    @router.post("/api/v1/projects/{project_id}/browser-profiles/{profile_id}/start")
    async def start_profile(
        request: Request,
        project_id: UUID,
        profile_id: UUID,
        body: StartBrowserProfileRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        resolved = await actor(request, write=True, csrf_header=x_csrf_token)
        if isinstance(resolved, JSONResponse):
            return resolved
        try:
            item = await dependencies.service.start(
                resolved, project_id, profile_id, login_url=body.login_url
            )
        except BrowserProfileOperationError as error:
            return _error(503, str(error))
        except Exception as error:
            response = _service_error(error)
            if response is not None:
                return response
            raise
        return item.to_public_dict()

    @router.post("/api/v1/projects/{project_id}/browser-profiles/{profile_id}/login-complete")
    async def complete_login(
        request: Request,
        project_id: UUID,
        profile_id: UUID,
        body: CompleteBrowserProfileLoginRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        resolved = await actor(request, write=True, csrf_header=x_csrf_token)
        if isinstance(resolved, JSONResponse):
            return resolved
        try:
            item = await dependencies.service.complete_login(
                resolved,
                project_id,
                profile_id,
                stop_after_save=body.stop_after_save,
            )
        except BrowserProfileOperationError as error:
            return _error(422, str(error))
        except Exception as error:
            response = _service_error(error)
            if response is not None:
                return response
            raise
        return item.to_public_dict()

    @router.post("/api/v1/projects/{project_id}/browser-profiles/{profile_id}/verify")
    async def verify_profile(
        request: Request,
        project_id: UUID,
        profile_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        resolved = await actor(request, write=True, csrf_header=x_csrf_token)
        if isinstance(resolved, JSONResponse):
            return resolved
        try:
            item = await dependencies.service.verify(resolved, project_id, profile_id)
        except BrowserProfileAuthStateMissing:
            return _error(409, "Browser profile has no saved auth state")
        except BrowserProfileOperationError as error:
            return _error(422, str(error))
        except Exception as error:
            response = _service_error(error)
            if response is not None:
                return response
            raise
        return item.to_public_dict()

    @router.post("/api/v1/projects/{project_id}/browser-profiles/{profile_id}/stop")
    async def stop_profile(
        request: Request,
        project_id: UUID,
        profile_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        resolved = await actor(request, write=True, csrf_header=x_csrf_token)
        if isinstance(resolved, JSONResponse):
            return resolved
        try:
            item = await dependencies.service.stop(resolved, project_id, profile_id)
        except Exception as error:
            response = _service_error(error)
            if response is not None:
                return response
            raise
        return item.to_public_dict()

    @router.delete("/api/v1/projects/{project_id}/browser-profiles/{profile_id}", status_code=204)
    async def delete_profile(
        request: Request,
        project_id: UUID,
        profile_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ):
        resolved = await actor(request, write=True, csrf_header=x_csrf_token)
        if isinstance(resolved, JSONResponse):
            return resolved
        try:
            await dependencies.service.delete(resolved, project_id, profile_id)
        except Exception as error:
            response = _service_error(error)
            if response is not None:
                return response
            raise
        return Response(status_code=204)

    return router


def _service_error(error: Exception) -> JSONResponse | None:
    if isinstance(error, BrowserProfileNotFound):
        return _error(404, "Profile not found")
    if isinstance(error, DuplicateBrowserProfile):
        return _error(409, "Browser profile name already exists")
    if isinstance(error, (ProjectNotFoundError, PermissionError)):
        return _error(404, "Project not found")
    return None


def _error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})
