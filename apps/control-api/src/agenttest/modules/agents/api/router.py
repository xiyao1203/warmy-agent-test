"""HTTP routes for project-scoped Agent assets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse

from agenttest.bootstrap.settings import Settings
from agenttest.modules.agents.api.schemas import (
    AgentListResponse,
    AgentResponse,
    AgentVersionListResponse,
    AgentVersionResponse,
    CreateAgentRequest,
    CreateAgentVersionRequest,
    UpdateAgentRequest,
    UpdateAgentVersionRequest,
)
from agenttest.modules.agents.application.commands import (
    AgentNotFoundError,
    AgentVersionNotFoundError,
    CreateAgentCommand,
    CreateAgentVersionCommand,
    PublishAgentVersionCommand,
    UpdateAgentCommand,
    UpdateAgentVersionCommand,
)
from agenttest.modules.agents.domain.entities import (
    Agent,
    AgentId,
    AgentVersion,
    AgentVersionId,
)
from agenttest.modules.identity.public import InvalidSessionError, User
from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
from agenttest.shared.api.problem_details import ProblemDetails
from agenttest.shared.application.uow import UnitOfWorkFactory, null_uow_factory

CSRF_COOKIE_NAME = "agenttest_csrf"


class CurrentUserExecutor(Protocol):
    async def execute(self, session_token: str) -> User: ...


class CsrfExecutor(Protocol):
    async def execute(self, session_token: str, csrf_token: str) -> None: ...


class ListAgentsExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> tuple[list[Agent], str | None]: ...


class GetAgentExecutor(Protocol):
    async def execute(self, actor: User, agent_id: AgentId) -> Agent: ...


class CreateAgentExecutor(Protocol):
    async def execute(self, actor: User, command: CreateAgentCommand) -> Agent: ...


class UpdateAgentExecutor(Protocol):
    async def execute(self, actor: User, command: UpdateAgentCommand) -> Agent: ...


class ListVersionsExecutor(Protocol):
    async def execute(self, actor: User, agent_id: AgentId) -> list[AgentVersion]: ...


class GetVersionExecutor(Protocol):
    async def execute(self, actor: User, version_id: AgentVersionId) -> AgentVersion: ...


class CreateVersionExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        command: CreateAgentVersionCommand,
    ) -> AgentVersion: ...


class UpdateVersionExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        command: UpdateAgentVersionCommand,
    ) -> AgentVersion: ...


class PublishVersionExecutor(Protocol):
    async def execute(
        self,
        actor: User,
        command: PublishAgentVersionCommand,
    ) -> AgentVersion: ...


@dataclass(frozen=True, slots=True)
class AgentApiDependencies:
    list_agents: ListAgentsExecutor
    get_agent: GetAgentExecutor
    create_agent: CreateAgentExecutor
    update_agent: UpdateAgentExecutor
    list_versions: ListVersionsExecutor
    get_version: GetVersionExecutor
    create_version: CreateVersionExecutor
    update_version: UpdateVersionExecutor
    publish_version: PublishVersionExecutor
    uow_factory: UnitOfWorkFactory = null_uow_factory


def create_agent_router(
    dependencies: AgentApiDependencies,
    *,
    current_user: CurrentUserExecutor,
    csrf: CsrfExecutor,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(
        prefix="/projects/{project_id}/agents",
        tags=["agents"],
    )

    async def actor_for(request: Request) -> User | JSONResponse:
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return authentication_required()
        try:
            return await current_user.execute(token)
        except InvalidSessionError:
            return authentication_required()

    async def writer(
        request: Request,
        csrf_header: str | None,
    ) -> User | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        token = request.cookies.get(settings.session_cookie_name)
        cookie = request.cookies.get(CSRF_COOKIE_NAME)
        if not token or not csrf_header or not cookie or csrf_header != cookie:
            return csrf_failed()
        try:
            await csrf.execute(token, csrf_header)
        except InvalidSessionError:
            return csrf_failed()
        return actor

    async def project_agent(
        actor: User,
        project_id: UUID,
        agent_id: UUID,
    ) -> Agent:
        agent = await dependencies.get_agent.execute(actor, AgentId(agent_id))
        if agent.project_id != ProjectId(project_id):
            raise AgentNotFoundError(AgentId(agent_id))
        return agent

    async def project_version(
        actor: User,
        project_id: UUID,
        agent_id: UUID,
        version_id: UUID,
    ) -> AgentVersion:
        agent = await project_agent(actor, project_id, agent_id)
        version = await dependencies.get_version.execute(
            actor,
            AgentVersionId(version_id),
        )
        if version.agent_id != agent.agent_id:
            raise AgentVersionNotFoundError(AgentVersionId(version_id))
        return version

    @router.get("", response_model=AgentListResponse)
    async def list_agents(
        request: Request,
        project_id: UUID,
        limit: int = Query(default=50, ge=1, le=100),
        cursor: str | None = None,
    ) -> AgentListResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            items, next_cursor = await dependencies.list_agents.execute(
                actor,
                ProjectId(project_id),
                limit=limit,
                cursor=cursor,
            )
        except ProjectNotFoundError:
            return asset_not_found()
        return AgentListResponse(
            items=[AgentResponse.from_domain(item) for item in items],
            next_cursor=next_cursor,
        )

    @router.post("", response_model=AgentResponse, status_code=201)
    async def create_agent(
        request: Request,
        project_id: UUID,
        payload: CreateAgentRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> AgentResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            async with dependencies.uow_factory():
                agent = await dependencies.create_agent.execute(
                    actor,
                    CreateAgentCommand(
                        project_id=ProjectId(project_id),
                        name=payload.name,
                        agent_type=payload.agent_type,
                        description=payload.description,
                    ),
                )
        except ProjectNotFoundError:
            return asset_not_found()
        except PermissionError:
            return permission_denied()
        return AgentResponse.from_domain(agent)

    @router.get("/{agent_id}", response_model=AgentResponse)
    async def get_agent(
        request: Request,
        project_id: UUID,
        agent_id: UUID,
    ) -> AgentResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            agent = await project_agent(actor, project_id, agent_id)
        except (AgentNotFoundError, ProjectNotFoundError):
            return asset_not_found()
        return AgentResponse.from_domain(agent)

    @router.patch("/{agent_id}", response_model=AgentResponse)
    async def update_agent(
        request: Request,
        project_id: UUID,
        agent_id: UUID,
        payload: UpdateAgentRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> AgentResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_agent(actor, project_id, agent_id)
            async with dependencies.uow_factory():
                agent = await dependencies.update_agent.execute(
                    actor,
                    UpdateAgentCommand(
                        agent_id=AgentId(agent_id),
                        name=payload.name,
                        description=payload.description,
                    ),
                )
        except (AgentNotFoundError, ProjectNotFoundError):
            return asset_not_found()
        except PermissionError:
            return permission_denied()
        except ValueError as error:
            return invalid_request(str(error))
        return AgentResponse.from_domain(agent)

    @router.get("/{agent_id}/versions", response_model=AgentVersionListResponse)
    async def list_versions(
        request: Request,
        project_id: UUID,
        agent_id: UUID,
    ) -> AgentVersionListResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_agent(actor, project_id, agent_id)
            versions = await dependencies.list_versions.execute(actor, AgentId(agent_id))
        except (AgentNotFoundError, ProjectNotFoundError):
            return asset_not_found()
        return AgentVersionListResponse(
            items=[AgentVersionResponse.from_domain(item) for item in versions]
        )

    @router.post(
        "/{agent_id}/versions",
        response_model=AgentVersionResponse,
        status_code=201,
    )
    async def create_version(
        request: Request,
        project_id: UUID,
        agent_id: UUID,
        payload: CreateAgentVersionRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> AgentVersionResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_agent(actor, project_id, agent_id)
            async with dependencies.uow_factory():
                version = await dependencies.create_version.execute(
                    actor,
                    CreateAgentVersionCommand(
                        agent_id=AgentId(agent_id),
                        config=payload.config.to_domain(),
                    ),
                )
        except (AgentNotFoundError, ProjectNotFoundError):
            return asset_not_found()
        except PermissionError:
            return permission_denied()
        except ValueError as error:
            return invalid_request(str(error))
        return AgentVersionResponse.from_domain(version)

    @router.get(
        "/{agent_id}/versions/{version_id}",
        response_model=AgentVersionResponse,
    )
    async def get_version(
        request: Request,
        project_id: UUID,
        agent_id: UUID,
        version_id: UUID,
    ) -> AgentVersionResponse | JSONResponse:
        actor = await actor_for(request)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            version = await project_version(actor, project_id, agent_id, version_id)
        except (
            AgentNotFoundError,
            AgentVersionNotFoundError,
            ProjectNotFoundError,
        ):
            return asset_not_found()
        return AgentVersionResponse.from_domain(version)

    @router.patch(
        "/{agent_id}/versions/{version_id}",
        response_model=AgentVersionResponse,
    )
    async def update_version(
        request: Request,
        project_id: UUID,
        agent_id: UUID,
        version_id: UUID,
        payload: UpdateAgentVersionRequest,
        x_csrf_token: str | None = Header(default=None),
    ) -> AgentVersionResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_version(actor, project_id, agent_id, version_id)
            async with dependencies.uow_factory():
                version = await dependencies.update_version.execute(
                    actor,
                    UpdateAgentVersionCommand(
                        version_id=AgentVersionId(version_id),
                        config=payload.config.to_domain(),
                    ),
                )
        except (
            AgentNotFoundError,
            AgentVersionNotFoundError,
            ProjectNotFoundError,
        ):
            return asset_not_found()
        except PermissionError:
            return permission_denied()
        except ValueError as error:
            return conflict(str(error))
        return AgentVersionResponse.from_domain(version)

    @router.post(
        "/{agent_id}/versions/{version_id}/publish",
        response_model=AgentVersionResponse,
    )
    async def publish_version(
        request: Request,
        project_id: UUID,
        agent_id: UUID,
        version_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> AgentVersionResponse | JSONResponse:
        actor = await writer(request, x_csrf_token)
        if isinstance(actor, JSONResponse):
            return actor
        try:
            await project_version(actor, project_id, agent_id, version_id)
            async with dependencies.uow_factory():
                version = await dependencies.publish_version.execute(
                    actor,
                    PublishAgentVersionCommand(
                        version_id=AgentVersionId(version_id),
                    ),
                )
        except (
            AgentNotFoundError,
            AgentVersionNotFoundError,
            ProjectNotFoundError,
        ):
            return asset_not_found()
        except PermissionError:
            return permission_denied()
        except ValueError as error:
            return conflict(str(error))
        return AgentVersionResponse.from_domain(version)

    return router


def authentication_required() -> JSONResponse:
    return problem_response(401, "Authentication required", "A valid session is required")


def csrf_failed() -> JSONResponse:
    return problem_response(403, "CSRF validation failed", "A valid CSRF token is required")


def permission_denied() -> JSONResponse:
    return problem_response(403, "Permission denied", "Project editor access is required")


def asset_not_found() -> JSONResponse:
    return problem_response(404, "Asset not found", "Asset was not found")


def invalid_request(detail: str) -> JSONResponse:
    return problem_response(400, "Invalid request", detail)


def conflict(detail: str) -> JSONResponse:
    return problem_response(409, "Conflict", detail)


def problem_response(status: int, title: str, detail: str) -> JSONResponse:
    problem = ProblemDetails(title=title, status=status, detail=detail)
    return JSONResponse(
        status_code=status,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )
