from datetime import timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from agenttest.bootstrap.project_access import ProjectAccessAdapter
from agenttest.bootstrap.run_source import SqlAlchemyRunSource
from agenttest.bootstrap.settings import Settings, get_settings
from agenttest.entrypoints.http.health import router as health_router
from agenttest.modules.agents.api.router import (
    AgentApiDependencies,
    create_agent_router,
)
from agenttest.modules.agents.application.commands import (
    CreateAgentHandler,
    CreateAgentVersionHandler,
    PublishAgentVersionHandler,
    UpdateAgentHandler,
    UpdateAgentVersionHandler,
)
from agenttest.modules.agents.application.queries import (
    GetAgentHandler,
    GetAgentVersionHandler,
    ListAgentsHandler,
    ListAgentVersionsHandler,
)
from agenttest.modules.agents.infrastructure.persistence.repositories import (
    SqlAlchemyAgentRepository,
    SqlAlchemyAgentVersionRepository,
)
from agenttest.modules.audit.api.router import AuditApiDependencies, create_audit_router
from agenttest.modules.audit.application.record import AuditRecorder
from agenttest.modules.audit.infrastructure.persistence.repositories import (
    SqlAlchemyAuditRepository,
)
from agenttest.modules.datasets.api.router import (
    DatasetApiDependencies,
    create_dataset_router,
)
from agenttest.modules.datasets.application.commands import (
    AddTestCaseHandler,
    CreateDatasetHandler,
    CreateDatasetVersionHandler,
    DeleteTestCaseHandler,
    PublishDatasetVersionHandler,
    UpdateDatasetHandler,
    UpdateTestCaseHandler,
)
from agenttest.modules.datasets.application.import_export import ImportExportService
from agenttest.modules.datasets.application.queries import (
    GetDatasetHandler,
    GetDatasetVersionHandler,
    GetTestCaseHandler,
    ListDatasetsHandler,
    ListDatasetVersionsHandler,
    ListTestCasesHandler,
)
from agenttest.modules.datasets.infrastructure.persistence.repositories import (
    SqlAlchemyDatasetRepository,
    SqlAlchemyDatasetVersionRepository,
    SqlAlchemyTestCaseRepository,
)
from agenttest.modules.environments.api.router import (
    EnvironmentApiDependencies,
    create_environment_router,
)
from agenttest.modules.environments.application.commands import (
    CreateEnvironmentTemplateHandler,
    DeleteEnvironmentTemplateHandler,
    UpdateEnvironmentTemplateHandler,
)
from agenttest.modules.environments.application.queries import (
    GetEnvironmentTemplateHandler,
    ListEnvironmentTemplatesHandler,
)
from agenttest.modules.environments.infrastructure.persistence.repositories import (
    SqlAlchemyEnvironmentTemplateRepository,
)
from agenttest.modules.identity.api.admin_router import (
    AdminApiDependencies,
    create_admin_router,
)
from agenttest.modules.identity.api.router import (
    AuthApiDependencies,
    create_auth_router,
)
from agenttest.modules.identity.application.commands.create_user import CreateUserHandler
from agenttest.modules.identity.application.commands.login import LoginHandler
from agenttest.modules.identity.application.commands.logout import LogoutHandler
from agenttest.modules.identity.application.commands.reset_password import ResetPasswordHandler
from agenttest.modules.identity.application.commands.set_user_status import (
    DeleteUserHandler,
    SetUserStatusHandler,
)
from agenttest.modules.identity.application.commands.update_user import UpdateUserHandler
from agenttest.modules.identity.application.queries.current_user import (
    CsrfValidator,
    CurrentUserQuery,
)
from agenttest.modules.identity.application.queries.list_users import (
    GetUserQuery,
    ListUsersQuery,
)
from agenttest.modules.identity.infrastructure.passwords import Argon2PasswordHasher
from agenttest.modules.identity.infrastructure.persistence.repositories import (
    SqlAlchemyCredentialRepository,
    SqlAlchemySessionRepository,
    SqlAlchemyUserRepository,
)
from agenttest.modules.projects.api.router import (
    ProjectApiDependencies,
    create_project_router,
)
from agenttest.modules.projects.application.commands.create_project import (
    CreateProjectHandler,
)
from agenttest.modules.projects.application.commands.manage_members import (
    AddProjectMemberHandler,
    ArchiveProjectHandler,
    RemoveProjectMemberHandler,
    RenameProjectHandler,
    UpdateProjectMemberHandler,
)
from agenttest.modules.projects.application.queries.list_projects import (
    GetProjectHandler,
    ListProjectMembersHandler,
    ListProjectsHandler,
)
from agenttest.modules.projects.infrastructure.persistence.repositories import (
    SqlAlchemyProjectRepository,
)
from agenttest.modules.runs.api.router import RunApiDependencies, create_run_router
from agenttest.modules.runs.application.commands import (
    ApplyRunResultHandler,
    CancelRunHandler,
    CreateRunHandler,
)
from agenttest.modules.runs.application.queries import (
    GetRunHandler,
    ListRunCasesHandler,
    ListRunsHandler,
)
from agenttest.modules.runs.infrastructure.orchestrator import LocalRunOrchestrator
from agenttest.modules.runs.infrastructure.persistence.repositories import (
    SqlAlchemyRunRepository,
)
from agenttest.modules.runs.infrastructure.temporal_orchestrator import (
    TemporalRunOrchestrator,
)
from agenttest.modules.test_plans.api.router import (
    TestPlanApiDependencies,
    create_test_plan_router,
)
from agenttest.modules.test_plans.application.commands import (
    CreateTestPlanHandler,
    CreateTestPlanVersionHandler,
    PublishTestPlanVersionHandler,
    UpdateTestPlanHandler,
    UpdateTestPlanVersionHandler,
)
from agenttest.modules.test_plans.application.queries import (
    GetTestPlanHandler,
    GetTestPlanVersionHandler,
    ListTestPlansHandler,
    ListTestPlanVersionsHandler,
)
from agenttest.modules.test_plans.infrastructure.persistence.repositories import (
    SqlAlchemyTestPlanRepository,
    SqlAlchemyTestPlanVersionRepository,
)
from agenttest.shared.domain.clock import SystemClock
from agenttest.shared.infrastructure.database import (
    SqlAlchemyUnitOfWork,
    create_database_engine,
    create_session_factory,
)


def create_app(
    settings: Settings | None = None,
    auth_dependencies: AuthApiDependencies | None = None,
    admin_dependencies: AdminApiDependencies | None = None,
    project_dependencies: ProjectApiDependencies | None = None,
    audit_dependencies: AuditApiDependencies | None = None,
    agent_dependencies: AgentApiDependencies | None = None,
    dataset_dependencies: DatasetApiDependencies | None = None,
    test_plan_dependencies: TestPlanApiDependencies | None = None,
    environment_dependencies: EnvironmentApiDependencies | None = None,
    run_dependencies: RunApiDependencies | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(
        title="Warmy Agent Test Control API",
        version=resolved_settings.app_version,
    )
    app.state.settings = resolved_settings

    # 全局 OPTIONS 处理：先拦截 OPTIONS 返回 200，再经过 CORS 添加响应头
    class PreflightMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            if request.method == "OPTIONS":
                return Response()
            return await call_next(request)

    app.add_middleware(PreflightMiddleware)

    # CORS 中间件在最外层，确保所有响应都包含正确的 CORS 头
    # 本地开发环境使用通配符 origin，生产环境应指定具体域名
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api/v1")
    dependencies = auth_dependencies or build_auth_dependencies(resolved_settings)
    app.include_router(
        create_auth_router(dependencies, resolved_settings),
        prefix="/api/v1",
    )
    admin = admin_dependencies or build_admin_dependencies(resolved_settings)
    app.include_router(
        create_admin_router(
            admin,
            current_user=dependencies.current_user,
            csrf=dependencies.csrf,
            settings=resolved_settings,
        ),
        prefix="/api/v1",
    )
    projects = project_dependencies or build_project_dependencies(resolved_settings)
    app.include_router(
        create_project_router(
            projects,
            current_user=dependencies.current_user,
            csrf=dependencies.csrf,
            settings=resolved_settings,
        ),
        prefix="/api/v1",
    )
    audits = audit_dependencies or build_audit_dependencies(resolved_settings)
    app.include_router(
        create_audit_router(
            audits,
            current_user=dependencies.current_user,
            settings=resolved_settings,
        ),
        prefix="/api/v1",
    )
    agents = agent_dependencies or build_agent_dependencies(resolved_settings)
    app.include_router(
        create_agent_router(
            agents,
            current_user=dependencies.current_user,
            csrf=dependencies.csrf,
            settings=resolved_settings,
        ),
        prefix="/api/v1",
    )
    datasets = dataset_dependencies or build_dataset_dependencies(resolved_settings)
    app.include_router(
        create_dataset_router(
            datasets,
            current_user=dependencies.current_user,
            csrf=dependencies.csrf,
            settings=resolved_settings,
        ),
        prefix="/api/v1",
    )
    test_plans = test_plan_dependencies or build_test_plan_dependencies(
        resolved_settings
    )
    app.include_router(
        create_test_plan_router(
            test_plans,
            current_user=dependencies.current_user,
            csrf=dependencies.csrf,
            settings=resolved_settings,
        ),
        prefix="/api/v1",
    )
    environments = environment_dependencies or build_environment_dependencies(
        resolved_settings
    )
    app.include_router(
        create_environment_router(
            environments,
            current_user=dependencies.current_user,
            csrf=dependencies.csrf,
            settings=resolved_settings,
        ),
        prefix="/api/v1",
    )
    runs = run_dependencies or build_run_dependencies(resolved_settings)
    app.include_router(
        create_run_router(
            runs,
            current_user=dependencies.current_user,
            csrf=dependencies.csrf,
            settings=resolved_settings,
        ),
        prefix="/api/v1",
    )

    # ── 归档端点（Agents/Datasets/TestPlans）────────────────────────────────
    _register_archive_endpoints(app, resolved_settings, dependencies)

    # ── 插件注册表 ──────────────────────────────────────────────────────────
    from agenttest.modules.plugins.infrastructure.file_registry import (
        FileBasedPluginRegistry,
    )

    plugins_root = Path(__file__).resolve().parents[5] / "plugins"
    app.state.plugins = FileBasedPluginRegistry(plugins_root)

    return app


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
    from agenttest.modules.agents.domain.entities import AgentId
    from agenttest.modules.agents.infrastructure.persistence.repositories import (
        SqlAlchemyAgentRepository,
    )
    from agenttest.modules.datasets.domain.entities import DatasetId
    from agenttest.modules.datasets.infrastructure.persistence.repositories import (
        SqlAlchemyDatasetRepository,
    )
    from agenttest.modules.identity.application.queries.current_user import (
        InvalidSessionError,
    )
    from agenttest.modules.identity.public import User
    from agenttest.modules.projects.infrastructure.persistence.repositories import (
        SqlAlchemyProjectRepository,
    )
    from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
    from agenttest.modules.test_plans.domain.entities import TestPlanId
    from agenttest.modules.test_plans.infrastructure.persistence.repositories import (
        SqlAlchemyTestPlanRepository,
    )
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    CSRF_NAME = "agenttest_csrf"
    engine = create_database_engine(str(settings.database_url))
    sf = create_session_factory(engine)
    agent_repo = SqlAlchemyAgentRepository(sf)
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

    @app.delete("/api/v1/projects/{project_id}/agents/{agent_id}", status_code=204)
    async def delete_agent(
        request: Request,
        project_id: UUID,
        agent_id: UUID,
        x_csrf_token: str | None = Header(default=None),
    ) -> Response:
        try:
            actor = await _actor(request)
            _check_csrf(request, x_csrf_token)
            await access.ensure_editor(actor, ProjectId(project_id))
            await agent_repo.delete(AgentId(agent_id))
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        except PermissionError:
            return JSONResponse(status_code=403, content={"detail": "Forbidden"})
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "Not Found"})
        return Response(status_code=204)

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


def build_auth_dependencies(settings: Settings) -> AuthApiDependencies:
    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    users = SqlAlchemyUserRepository(session_factory)
    credentials = SqlAlchemyCredentialRepository(session_factory)
    sessions = SqlAlchemySessionRepository(session_factory)
    audit = AuditRecorder(SqlAlchemyAuditRepository(session_factory))
    clock = SystemClock()
    return AuthApiDependencies(
        login=LoginHandler(
            users=users,
            credentials=credentials,
            sessions=sessions,
            password_hasher=Argon2PasswordHasher(),
            clock=clock,
            session_ttl=timedelta(seconds=settings.session_ttl_seconds),
            audit=audit,
        ),
        current_user=CurrentUserQuery(users=users, sessions=sessions, clock=clock),
        logout=LogoutHandler(sessions=sessions, clock=clock, audit=audit),
        csrf=CsrfValidator(sessions=sessions, clock=clock),
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
    )


def build_admin_dependencies(settings: Settings) -> AdminApiDependencies:
    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    users = SqlAlchemyUserRepository(session_factory)
    credentials = SqlAlchemyCredentialRepository(session_factory)
    sessions = SqlAlchemySessionRepository(session_factory)
    audit = AuditRecorder(SqlAlchemyAuditRepository(session_factory))
    clock = SystemClock()
    password_hasher = Argon2PasswordHasher()
    return AdminApiDependencies(
        list_users=ListUsersQuery(users=users),
        get_user=GetUserQuery(users=users),
        create_user=CreateUserHandler(
            users=users,
            credentials=credentials,
            password_hasher=password_hasher,
            audit=audit,
        ),
        update_user=UpdateUserHandler(users=users, audit=audit),
        reset_password=ResetPasswordHandler(
            users=users,
            credentials=credentials,
            sessions=sessions,
            password_hasher=password_hasher,
            clock=clock,
            audit=audit,
        ),
        set_status=SetUserStatusHandler(
            users=users,
            sessions=sessions,
            clock=clock,
            audit=audit,
        ),
        delete_user=DeleteUserHandler(
            users=users,
            sessions=sessions,
            clock=clock,
            audit=audit,
        ),
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
    )


def build_project_dependencies(settings: Settings) -> ProjectApiDependencies:
    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    repository = SqlAlchemyProjectRepository(session_factory)
    audit = AuditRecorder(SqlAlchemyAuditRepository(session_factory))
    return ProjectApiDependencies(
        list_projects=ListProjectsHandler(projects=repository),
        get_project=GetProjectHandler(projects=repository),
        create_project=CreateProjectHandler(projects=repository, audit=audit),
        rename_project=RenameProjectHandler(projects=repository, audit=audit),
        archive_project=ArchiveProjectHandler(projects=repository, audit=audit),
        list_members=ListProjectMembersHandler(projects=repository),
        add_member=AddProjectMemberHandler(projects=repository, audit=audit),
        update_member=UpdateProjectMemberHandler(projects=repository, audit=audit),
        remove_member=RemoveProjectMemberHandler(projects=repository, audit=audit),
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
    )


def build_audit_dependencies(settings: Settings) -> AuditApiDependencies:
    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    return AuditApiDependencies(
        audits=SqlAlchemyAuditRepository(session_factory),
        projects=SqlAlchemyProjectRepository(session_factory),
    )


def build_agent_dependencies(settings: Settings) -> AgentApiDependencies:
    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    agents = SqlAlchemyAgentRepository(session_factory)
    versions = SqlAlchemyAgentVersionRepository(session_factory)
    projects = SqlAlchemyProjectRepository(session_factory)
    access = ProjectAccessAdapter(projects)
    audit = AuditRecorder(SqlAlchemyAuditRepository(session_factory))
    return AgentApiDependencies(
        list_agents=ListAgentsHandler(agents=agents, project_access=access),
        get_agent=GetAgentHandler(agents=agents, project_access=access),
        create_agent=CreateAgentHandler(
            agents=agents,
            project_access=access,
            audit=audit,
        ),
        update_agent=UpdateAgentHandler(
            agents=agents,
            project_access=access,
            audit=audit,
        ),
        list_versions=ListAgentVersionsHandler(
            agents=agents,
            versions=versions,
            project_access=access,
        ),
        get_version=GetAgentVersionHandler(
            agents=agents,
            versions=versions,
            project_access=access,
        ),
        create_version=CreateAgentVersionHandler(
            agents=agents,
            versions=versions,
            project_access=access,
            audit=audit,
        ),
        update_version=UpdateAgentVersionHandler(
            agents=agents,
            versions=versions,
            project_access=access,
            audit=audit,
        ),
        publish_version=PublishAgentVersionHandler(
            agents=agents,
            versions=versions,
            project_access=access,
            audit=audit,
        ),
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
    )


def build_dataset_dependencies(settings: Settings) -> DatasetApiDependencies:
    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    datasets = SqlAlchemyDatasetRepository(session_factory)
    versions = SqlAlchemyDatasetVersionRepository(session_factory)
    cases = SqlAlchemyTestCaseRepository(session_factory)
    projects = SqlAlchemyProjectRepository(session_factory)
    access = ProjectAccessAdapter(projects)
    audit = AuditRecorder(SqlAlchemyAuditRepository(session_factory))
    return DatasetApiDependencies(
        list_datasets=ListDatasetsHandler(
            datasets=datasets,
            project_access=access,
        ),
        get_dataset=GetDatasetHandler(
            datasets=datasets,
            project_access=access,
        ),
        create_dataset=CreateDatasetHandler(
            datasets=datasets,
            project_access=access,
            audit=audit,
        ),
        update_dataset=UpdateDatasetHandler(
            datasets=datasets,
            project_access=access,
            audit=audit,
        ),
        list_versions=ListDatasetVersionsHandler(
            datasets=datasets,
            versions=versions,
            project_access=access,
        ),
        get_version=GetDatasetVersionHandler(
            datasets=datasets,
            versions=versions,
            project_access=access,
        ),
        create_version=CreateDatasetVersionHandler(
            datasets=datasets,
            versions=versions,
            project_access=access,
            audit=audit,
        ),
        list_cases=ListTestCasesHandler(
            datasets=datasets,
            versions=versions,
            cases=cases,
            project_access=access,
        ),
        get_case=GetTestCaseHandler(
            datasets=datasets,
            versions=versions,
            cases=cases,
            project_access=access,
        ),
        add_case=AddTestCaseHandler(
            datasets=datasets,
            versions=versions,
            cases=cases,
            project_access=access,
            audit=audit,
        ),
        update_case=UpdateTestCaseHandler(
            datasets=datasets,
            versions=versions,
            cases=cases,
            project_access=access,
            audit=audit,
        ),
        delete_case=DeleteTestCaseHandler(
            datasets=datasets,
            versions=versions,
            cases=cases,
            project_access=access,
            audit=audit,
        ),
        publish_version=PublishDatasetVersionHandler(
            datasets=datasets,
            versions=versions,
            project_access=access,
            audit=audit,
        ),
        import_export=ImportExportService(
            cases=cases,
            project_access=access,
        ),
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
    )


def build_test_plan_dependencies(settings: Settings) -> TestPlanApiDependencies:
    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    plans = SqlAlchemyTestPlanRepository(session_factory)
    versions = SqlAlchemyTestPlanVersionRepository(session_factory)
    projects = SqlAlchemyProjectRepository(session_factory)
    access = ProjectAccessAdapter(projects)
    audit = AuditRecorder(SqlAlchemyAuditRepository(session_factory))
    return TestPlanApiDependencies(
        list_plans=ListTestPlansHandler(
            test_plans=plans,
            project_access=access,
        ),
        get_plan=GetTestPlanHandler(
            test_plans=plans,
            project_access=access,
        ),
        create_plan=CreateTestPlanHandler(
            test_plans=plans,
            project_access=access,
            audit=audit,
        ),
        update_plan=UpdateTestPlanHandler(
            test_plans=plans,
            project_access=access,
            audit=audit,
        ),
        list_versions=ListTestPlanVersionsHandler(
            test_plans=plans,
            versions=versions,
            project_access=access,
        ),
        get_version=GetTestPlanVersionHandler(
            test_plans=plans,
            versions=versions,
            project_access=access,
        ),
        create_version=CreateTestPlanVersionHandler(
            test_plans=plans,
            versions=versions,
            project_access=access,
            audit=audit,
        ),
        update_version=UpdateTestPlanVersionHandler(
            test_plans=plans,
            versions=versions,
            project_access=access,
            audit=audit,
        ),
        publish_version=PublishTestPlanVersionHandler(
            test_plans=plans,
            versions=versions,
            project_access=access,
            audit=audit,
        ),
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
    )


def build_environment_dependencies(settings: Settings) -> EnvironmentApiDependencies:
    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    templates = SqlAlchemyEnvironmentTemplateRepository(session_factory)
    projects = SqlAlchemyProjectRepository(session_factory)
    access = ProjectAccessAdapter(projects)
    audit = AuditRecorder(SqlAlchemyAuditRepository(session_factory))
    return EnvironmentApiDependencies(
        list_templates=ListEnvironmentTemplatesHandler(
            templates=templates,
            project_access=access,
        ),
        get_template=GetEnvironmentTemplateHandler(
            templates=templates,
            project_access=access,
        ),
        create_template=CreateEnvironmentTemplateHandler(
            templates=templates,
            project_access=access,
            audit=audit,
        ),
        update_template=UpdateEnvironmentTemplateHandler(
            templates=templates,
            project_access=access,
            audit=audit,
        ),
        delete_template=DeleteEnvironmentTemplateHandler(
            templates=templates,
            project_access=access,
            audit=audit,
        ),
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
    )


def build_run_dependencies(settings: Settings) -> RunApiDependencies:
    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    runs = SqlAlchemyRunRepository(session_factory)
    projects = SqlAlchemyProjectRepository(session_factory)
    access = ProjectAccessAdapter(projects)
    source = SqlAlchemyRunSource(session_factory)
    orchestrator = (
        TemporalRunOrchestrator(
            address=settings.temporal_address,
            control_api_base_url=settings.control_api_base_url,
            internal_api_token=settings.internal_api_token,
            namespace=settings.temporal_namespace,
            task_queue=settings.temporal_task_queue,
        )
        if settings.temporal_address
        else LocalRunOrchestrator()
    )
    return RunApiDependencies(
        create_run=CreateRunHandler(
            runs=runs,
            source=source,
            project_access=access,
            orchestrator=orchestrator,
        ),
        list_runs=ListRunsHandler(runs=runs, project_access=access),
        get_run=GetRunHandler(runs=runs, project_access=access),
        list_cases=ListRunCasesHandler(runs=runs, project_access=access),
        cancel_run=CancelRunHandler(
            runs=runs,
            project_access=access,
            orchestrator=orchestrator,
        ),
        apply_result=ApplyRunResultHandler(runs=runs),
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
    )
