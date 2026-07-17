from pathlib import Path

from fastapi import FastAPI
from starlette.requests import Request

from agenttest.bootstrap.project_access import ProjectAccessAdapter
from agenttest.bootstrap.providers.core import build_browser_auth_state_service
from agenttest.bootstrap.settings import Settings
from agenttest.modules.datasets.infrastructure.persistence.repositories import (
    SqlAlchemyDatasetRepository,
)
from agenttest.modules.environments.infrastructure.persistence.repositories import (
    SqlAlchemyEnvironmentTemplateRepository,
)
from agenttest.modules.identity.api.router import (
    AuthApiDependencies,
)
from agenttest.modules.model_configs.infrastructure.credentials import AesGcmCredentialCipher
from agenttest.modules.projects.infrastructure.persistence.repositories import (
    SqlAlchemyProjectRepository,
)
from agenttest.modules.test_plans.infrastructure.persistence.repositories import (
    SqlAlchemyTestPlanRepository,
    SqlAlchemyTestPlanVersionRepository,
)
from agenttest.shared.domain.clock import SystemClock
from agenttest.shared.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)


def _register_archive_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps: AuthApiDependencies,
) -> None:
    """注册资产归档（软删除）端点，避免修改各模块 router 内部结构。"""
    from uuid import UUID

    from fastapi import Header, Request
    from fastapi.responses import JSONResponse, Response

    from agenttest.bootstrap.project_access import ProjectAccessAdapter
    from agenttest.modules.datasets.domain.entities import DatasetId
    from agenttest.modules.identity.application.queries.current_user import (
        InvalidSessionError,
    )
    from agenttest.modules.identity.public import User
    from agenttest.modules.projects.infrastructure.persistence.repositories import (
        SqlAlchemyProjectRepository,
    )
    from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
    from agenttest.modules.test_plans.domain.entities import TestPlanId
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    CSRF_NAME = "agenttest_csrf"
    engine = create_database_engine(str(settings.database_url))
    sf = create_session_factory(engine)
    dataset_repo = SqlAlchemyDatasetRepository(sf)
    plan_repo = SqlAlchemyTestPlanRepository(sf)
    project_repo = SqlAlchemyProjectRepository(sf)
    access = ProjectAccessAdapter(project_repo)

    async def _actor(request: Request) -> User:
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            raise InvalidSessionError
        return await auth_deps.current_user.execute(token)

    def _check_csrf(request: Request, header: str | None) -> None:
        if not header or header != request.cookies.get(CSRF_NAME):
            raise PermissionError("CSRF mismatch")

    @app.delete("/api/v1/projects/{project_id}/datasets/{dataset_id}", status_code=204)
    async def delete_dataset(
        request: Request,
        project_id: UUID,
        dataset_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> Response:
        try:
            actor = await _actor(request)
            _check_csrf(request, x_csrf_token)
            await access.ensure_editor(actor, ProjectId(project_id))
            await dataset_repo.delete(DatasetId(dataset_id))
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        except PermissionError:
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        return Response(status_code=204)

    @app.delete("/api/v1/projects/{project_id}/test-plans/{plan_id}", status_code=204)
    async def delete_test_plan(
        request: Request,
        project_id: UUID,
        plan_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> Response:
        try:
            actor = await _actor(request)
            _check_csrf(request, x_csrf_token)
            await access.ensure_editor(actor, ProjectId(project_id))
            await plan_repo.delete(TestPlanId(plan_id))
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        except PermissionError:
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        return Response(status_code=204)


def _register_snapshot_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,  # AuthApiDependencies
) -> None:
    """注册环境快照 API。"""
    from agenttest.modules.environments.api.snapshots import (
        SnapshotApiDependencies,
        create_snapshot_router,
    )
    from agenttest.modules.environments.application.snapshots import (
        EnvironmentSnapshotService,
    )
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    templates = SqlAlchemyEnvironmentTemplateRepository(session_factory)
    access = ProjectAccessAdapter(SqlAlchemyProjectRepository(session_factory))

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_snapshot_router(
        SnapshotApiDependencies(
            service=EnvironmentSnapshotService(
                templates=templates,
                project_access=access,
                clock=SystemClock(),
            ),
            actor_for=actor_for,
            settings=settings,
        )
    )
    app.include_router(router, prefix="/api/v1")


def _register_dry_run_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,  # AuthApiDependencies
) -> None:
    """注册测试计划试运行 API。"""
    from agenttest.modules.test_plans.api.dry_run import (
        DryRunApiDependencies,
        create_dry_run_router,
    )
    from agenttest.modules.test_plans.application.dry_run import DryRunService
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    versions = SqlAlchemyTestPlanVersionRepository(session_factory)
    access = ProjectAccessAdapter(SqlAlchemyProjectRepository(session_factory))

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_dry_run_router(
        DryRunApiDependencies(
            service=DryRunService(reader=versions, project_access=access),
            actor_for=actor_for,
            settings=settings,
        )
    )
    app.include_router(router, prefix="/api/v1")


def _register_credential_endpoints(app: FastAPI, settings: Settings, auth_deps) -> None:
    from agenttest.modules.browser_profiles.api.lease_router import (
        create_browser_session_lease_router,
    )
    from agenttest.modules.browser_profiles.application.leases import (
        BrowserSessionLeaseService,
    )
    from agenttest.modules.browser_profiles.infrastructure.repository import (
        SqlAlchemyBrowserProfileRepository,
    )
    from agenttest.modules.environments.api.credential_router import create_credential_router
    from agenttest.modules.environments.api.lease_router import create_credential_lease_router
    from agenttest.modules.environments.application.credentials import CredentialBindingService
    from agenttest.modules.environments.application.leases import CredentialLeaseService
    from agenttest.modules.environments.infrastructure.credential_store import (
        SqlAlchemyCredentialRepository,
    )
    from agenttest.modules.projects.public import ProjectNotFoundError
    from agenttest.modules.runs.infrastructure.browser_session_scope_reader import (
        SqlAlchemyBrowserSessionScopeReader,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)

    async def check_project(project_id):
        from sqlalchemy import text

        async with session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM projects WHERE id = :pid"), {"pid": project_id}
            )
            if result.scalar() is None:
                raise ProjectNotFoundError

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    cipher = (
        AesGcmCredentialCipher(settings.model_credential_key)
        if settings.model_credential_key
        else None
    )
    app.include_router(
        create_credential_router(
            actor_for=actor_for,
            check_project=check_project,
            settings=settings,
            service=CredentialBindingService(
                SqlAlchemyCredentialRepository(session_factory), cipher
            ),
        ),
        prefix="/api/v1",
    )
    if cipher is not None:

        async def scope_check(project_id, run_id, run_case_id):
            from sqlalchemy import text

            async with session_factory() as session:
                result = await session.scalar(
                    text(
                        """
                        SELECT 1
                        FROM run_cases rc
                        JOIN runs r ON r.id = rc.run_id
                        WHERE r.project_id = :project_id
                          AND r.id = :run_id
                          AND rc.id = :run_case_id
                          AND r.status = 'running'
                        """
                    ),
                    {
                        "project_id": project_id,
                        "run_id": run_id,
                        "run_case_id": run_case_id,
                    },
                )
            return result is not None

        app.include_router(
            create_credential_lease_router(
                internal_token=settings.internal_api_token,
                service=CredentialLeaseService(
                    SqlAlchemyCredentialRepository(session_factory), cipher
                ),
                scope_check=scope_check,
            ),
            prefix="/api/v1",
        )
    app.include_router(
        create_browser_session_lease_router(
            internal_token=settings.internal_api_token,
            service=BrowserSessionLeaseService(
                repository=SqlAlchemyBrowserProfileRepository(session_factory),
                auth_state=build_browser_auth_state_service(settings),
                scope_reader=SqlAlchemyBrowserSessionScopeReader(session_factory),
            ),
        ),
        prefix="/api/v1",
    )


def _register_test_account_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,
) -> None:
    """注册测试账号 API。"""
    from agenttest.modules.test_accounts.api.router import (
        TestAccountApiDependencies,
        create_test_account_router,
    )
    from agenttest.modules.test_accounts.application.service import TestAccountService
    from agenttest.modules.test_accounts.infrastructure.persistence.repositories import (
        SqlAlchemyTestAccountRepository,
    )
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_test_account_router(
        TestAccountApiDependencies(
            service=TestAccountService(
                accounts=SqlAlchemyTestAccountRepository(session_factory),
                project_access=ProjectAccessAdapter(SqlAlchemyProjectRepository(session_factory)),
            ),
            actor_for=actor_for,
            settings=settings,
        )
    )
    app.include_router(router, prefix="/api/v1")


def _register_browser_profile_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,  # AuthApiDependencies
) -> None:
    """注册浏览器实例 Profile CRUD API。"""

    from fastapi import Request

    from agenttest.modules.browser_profiles.api.router import (
        BrowserProfileApiDependencies,
        create_browser_profile_router,
    )
    from agenttest.modules.browser_profiles.application.service import (
        BrowserProfileService,
    )
    from agenttest.modules.browser_profiles.infrastructure.repository import (
        SqlAlchemyBrowserProfileRepository,
    )
    from agenttest.modules.browser_profiles.infrastructure.runtime import (
        ManagedBrowserProfileRuntime,
    )
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_browser_profile_router(
        BrowserProfileApiDependencies(
            service=BrowserProfileService(
                repository=SqlAlchemyBrowserProfileRepository(session_factory),
                runtime=ManagedBrowserProfileRuntime(Path(settings.browser_profile_root)),
                auth_state=build_browser_auth_state_service(settings),
                project_access=ProjectAccessAdapter(SqlAlchemyProjectRepository(session_factory)),
            ),
            actor_for=actor_for,
            settings=settings,
        )
    )
    app.include_router(router)
