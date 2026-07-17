from pathlib import Path

from fastapi import FastAPI
from starlette.requests import Request

from agenttest.bootstrap.project_access import ProjectAccessAdapter
from agenttest.bootstrap.settings import Settings
from agenttest.modules.projects.infrastructure.persistence.repositories import (
    SqlAlchemyProjectRepository,
)
from agenttest.modules.runs.infrastructure.persistence.repositories import (
    SqlAlchemyRunRepository,
)
from agenttest.shared.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)


def _register_artifact_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,  # AuthApiDependencies
) -> None:
    """注册产物上传/列表/下载端点（auth+csrf+project 保护）。"""
    from uuid import UUID

    from fastapi import Request

    from agenttest.bootstrap.project_access import ProjectAccessAdapter
    from agenttest.modules.artifacts.api.router import (
        ArtifactApiDependencies,
        create_artifact_router,
    )
    from agenttest.modules.artifacts.application.service import ArtifactService
    from agenttest.modules.artifacts.infrastructure.repositories import (
        SqlAlchemyArtifactRepository,
    )
    from agenttest.modules.artifacts.infrastructure.storage import (
        FileSystemArtifactStorage,
    )
    from agenttest.modules.identity.application.queries.current_user import (
        InvalidSessionError,
    )
    from agenttest.modules.identity.public import User
    from agenttest.modules.projects.infrastructure.persistence.repositories import (
        SqlAlchemyProjectRepository,
    )
    from agenttest.modules.projects.public import ProjectId
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    CSRF_NAME = "agenttest_csrf"

    artifacts_dir = Path(".data/artifacts")
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    storage = FileSystemArtifactStorage(artifacts_dir)

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    access = ProjectAccessAdapter(SqlAlchemyProjectRepository(session_factory))
    service = ArtifactService(
        repository=SqlAlchemyArtifactRepository(session_factory),
        storage=storage,
        user_limit_bytes=settings.artifact_user_upload_max_bytes,
        internal_limit_bytes=settings.artifact_internal_upload_max_bytes,
    )

    async def _actor(request: Request) -> User:
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            raise InvalidSessionError
        return await auth_deps.current_user.execute(token)

    def _check_csrf(request: Request) -> None:
        header = request.headers.get("X-Csrf-Token")
        if not header or header != request.cookies.get(CSRF_NAME):
            raise PermissionError("CSRF mismatch")

    async def _check_project(actor: User, project_id: UUID, write: bool) -> None:
        if write:
            await access.ensure_editor(actor, ProjectId(project_id))
        else:
            await access.ensure_member(actor, ProjectId(project_id))

    router = create_artifact_router(
        ArtifactApiDependencies(
            service=service,
            actor=_actor,
            csrf=_check_csrf,
            project_access=_check_project,
            internal_token=settings.internal_api_token,
        )
    )
    app.include_router(router, prefix="/api/v1")


def _register_trace_diff_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,  # AuthApiDependencies
) -> None:
    """注册 Trace 对比 API。"""
    from agenttest.modules.runs.api.trace_diff import (
        TraceDiffApiDependencies,
        create_trace_diff_router,
    )
    from agenttest.modules.runs.application.comparison import RunComparisonService

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    runs = SqlAlchemyRunRepository(session_factory)
    access = ProjectAccessAdapter(SqlAlchemyProjectRepository(session_factory))

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_trace_diff_router(
        TraceDiffApiDependencies(
            compare=RunComparisonService(runs=runs, project_access=access),
            actor_for=actor_for,
            settings=settings,
        )
    )
    app.include_router(router, prefix="/api/v1")


def _register_run_stream_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,
) -> None:
    """注册运行进度 SSE 端点。"""
    from agenttest.modules.runs.api.stream import (
        RunStreamApiDependencies,
        create_run_stream_router,
    )
    from agenttest.modules.runs.application.event_stream import RunProgressService

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    runs = SqlAlchemyRunRepository(session_factory)
    access = ProjectAccessAdapter(SqlAlchemyProjectRepository(session_factory))

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_run_stream_router(
        RunStreamApiDependencies(
            progress=RunProgressService(runs=runs, project_access=access),
            actor_for=actor_for,
            settings=settings,
        )
    )
    app.include_router(router, prefix="/api/v1")
