from datetime import timedelta
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from agenttest.bootstrap.agent_relationships import SqlAlchemyAgentRelationshipsReader
from agenttest.bootstrap.gate_evidence import SqlAlchemyGateEvidence
from agenttest.bootstrap.project_access import ProjectAccessAdapter
from agenttest.bootstrap.review_collector import SqlAlchemyRunReviewCollector
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
    DeleteAgentHandler,
    PublishAgentVersionHandler,
    SetBaselineAgentVersionHandler,
    SetCurrentAgentVersionHandler,
    UpdateAgentHandler,
    UpdateAgentVersionHandler,
)
from agenttest.modules.agents.application.queries import (
    GetAgentHandler,
    GetAgentVersionHandler,
    ListAgentsHandler,
    ListAgentVersionsHandler,
)
from agenttest.modules.agents.infrastructure.connection_validator import (
    HttpAgentConnectionValidator,
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
from agenttest.modules.datasets.application.generate_from_run import (
    GenerateCasesFromFailedRunHandler,
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
from agenttest.modules.environments.application.versions import (
    CreateEnvironmentVersionHandler,
    GetEnvironmentVersionHandler,
    ListEnvironmentVersionsHandler,
    PublishEnvironmentVersionHandler,
    UpdateEnvironmentVersionHandler,
)
from agenttest.modules.environments.infrastructure.persistence.repositories import (
    SqlAlchemyEnvironmentTemplateRepository,
    SqlAlchemyEnvironmentVersionRepository,
)
from agenttest.modules.feedback.api.router import (
    FeedbackApiDependencies,
    create_feedback_router,
)
from agenttest.modules.feedback.application.commands import CreateFeedbackHandler
from agenttest.modules.feedback.infrastructure.persistence.repositories import (
    SqlAlchemyFeedbackRepository,
)
from agenttest.modules.identity.api.admin_router import (
    AdminApiDependencies,
    create_admin_router,
)
from agenttest.modules.identity.api.router import (
    AuthApiDependencies,
    create_auth_router,
)
from agenttest.modules.identity.application.commands.change_password import (
    ChangePasswordHandler,
)
from agenttest.modules.identity.application.commands.create_user import CreateUserHandler
from agenttest.modules.identity.application.commands.login import LoginHandler
from agenttest.modules.identity.application.commands.logout import LogoutHandler
from agenttest.modules.identity.application.commands.reset_password import ResetPasswordHandler
from agenttest.modules.identity.application.commands.set_user_status import (
    DeleteUserHandler,
    SetUserStatusHandler,
)
from agenttest.modules.identity.application.commands.update_profile import (
    UpdateProfileHandler,
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
from agenttest.modules.model_configs.api.router import create_model_config_router
from agenttest.modules.model_configs.application.service import ModelConfigService
from agenttest.modules.model_configs.infrastructure.credentials import AesGcmCredentialCipher
from agenttest.modules.model_configs.infrastructure.persistence.repositories import (
    SqlAlchemyModelConfigRepository,
)
from agenttest.modules.model_configs.infrastructure.temporal_invoker import TemporalModelInvoker
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
from agenttest.modules.reports.api.router import create_report_router
from agenttest.modules.reports.application.service import ReportService
from agenttest.modules.reviews.infrastructure.persistence.repositories import (
    SqlAlchemyReviewTaskRepository,
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
from agenttest.modules.user_settings.api.router import (
    UserSettingsApiDependencies,
    create_user_settings_router,
)
from agenttest.modules.user_settings.application.commands import (
    UpdateUserSettingsHandler,
)
from agenttest.modules.user_settings.application.queries import GetUserSettingsHandler
from agenttest.modules.user_settings.infrastructure.persistence.repositories import (
    SqlAlchemyUserSettingsRepository,
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
    user_settings_dependencies: UserSettingsApiDependencies | None = None,
    feedback_dependencies: FeedbackApiDependencies | None = None,
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

    # CORS 中间件在最外层，凭证请求只允许已配置的 Web Origin。
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(resolved_settings.web_origin).rstrip("/")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # GZip 响应压缩，阈值 500 字节
    app.add_middleware(GZipMiddleware, minimum_size=500)

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
    test_plans = test_plan_dependencies or build_test_plan_dependencies(resolved_settings)
    app.include_router(
        create_test_plan_router(
            test_plans,
            current_user=dependencies.current_user,
            csrf=dependencies.csrf,
            settings=resolved_settings,
        ),
        prefix="/api/v1",
    )
    environments = environment_dependencies or build_environment_dependencies(resolved_settings)
    app.include_router(
        create_environment_router(
            environments,
            current_user=dependencies.current_user,
            csrf=dependencies.csrf,
            settings=resolved_settings,
        ),
        prefix="/api/v1",
    )
    app.include_router(
        create_model_config_router(
            service=build_model_config_service(resolved_settings),
            invoker=TemporalModelInvoker(
                address=resolved_settings.temporal_address,
                namespace=resolved_settings.temporal_namespace,
                task_queue=resolved_settings.model_runner_task_queue,
                allow_private_network=resolved_settings.model_allow_private_network,
            ),
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
    report_engine = create_database_engine(str(resolved_settings.database_url))
    report_session_factory = create_session_factory(report_engine)
    report_runs = SqlAlchemyRunRepository(report_session_factory)
    report_projects = SqlAlchemyProjectRepository(report_session_factory)
    app.include_router(
        create_report_router(
            service=ReportService(
                runs=report_runs,
                project_access=ProjectAccessAdapter(report_projects),
            ),
            current_user=dependencies.current_user,
            settings=resolved_settings,
        ),
        prefix="/api/v1",
    )
    user_settings = user_settings_dependencies or build_user_settings_dependencies(
        resolved_settings
    )
    app.include_router(
        create_user_settings_router(user_settings, resolved_settings),
        prefix="/api/v1",
    )
    feedback = feedback_dependencies or build_feedback_dependencies(resolved_settings)
    app.include_router(
        create_feedback_router(feedback, resolved_settings),
        prefix="/api/v1",
    )

    # ── 归档端点（Agents/Datasets/TestPlans）────────────────────────────────
    _register_archive_endpoints(app, resolved_settings, dependencies)

    # ── Artifact 产物上传/下载 ────────────────────────────────────────────
    _register_artifact_endpoints(app, resolved_settings, dependencies)

    # ── Security Policy Engine ──────────────────────────────────────────────
    _register_security_endpoints(app, resolved_settings, dependencies)

    # ── Environment Snapshot API ─────────────────────────────────────────
    _register_snapshot_endpoints(app, resolved_settings, dependencies)

    # ── Test Plan Dry-Run API ────────────────────────────────────────────
    _register_dry_run_endpoints(app, resolved_settings, dependencies)

    # ── Trace Diff API ──────────────────────────────────────────────────
    _register_trace_diff_endpoints(app, resolved_settings, dependencies)

    # ── Scorer CRUD API ────────────────────────────────────────────────
    _register_scorer_endpoints(app, resolved_settings, dependencies)

    # ── Experiment API ─────────────────────────────────────────────────
    _register_experiment_endpoints(app, resolved_settings, dependencies)

    # ── Review API ─────────────────────────────────────────────────────
    _register_review_endpoints(app, resolved_settings, dependencies)

    # ── Security Scan API ───────────────────────────────────────────────
    _register_security_scan_endpoints(app, resolved_settings, dependencies)
    _register_credential_endpoints(app, resolved_settings, dependencies)

    # ── Release Gate API ────────────────────────────────────────────────
    _register_gate_endpoints(app, resolved_settings, dependencies)

    # ── Test Agent Chat API ────────────────────────────────────────────
    _register_test_agent_endpoints(app, resolved_settings, dependencies)

    # ── Test Account API ───────────────────────────────────────────────
    _register_test_account_endpoints(app, resolved_settings, dependencies)

    # ── Run Progress SSE ───────────────────────────────────────────────
    _register_run_stream_endpoints(app, resolved_settings, dependencies)

    # ── Browser Profile API ───────────────────────────────────────────
    _register_browser_profile_endpoints(app, resolved_settings, dependencies)

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
        update_profile=UpdateProfileHandler(users=users),
        change_password=ChangePasswordHandler(
            credentials=credentials,
            password_hasher=Argon2PasswordHasher(),
        ),
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
    )


def build_user_settings_dependencies(settings: Settings) -> UserSettingsApiDependencies:
    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    users = SqlAlchemyUserRepository(session_factory)
    sessions = SqlAlchemySessionRepository(session_factory)
    clock = SystemClock()
    repository = SqlAlchemyUserSettingsRepository(session_factory)
    return UserSettingsApiDependencies(
        current_user=CurrentUserQuery(users=users, sessions=sessions, clock=clock),
        get_settings=GetUserSettingsHandler(repository=repository),
        update_settings=UpdateUserSettingsHandler(repository=repository),
        csrf=CsrfValidator(sessions=sessions, clock=clock),
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
    )


def build_feedback_dependencies(settings: Settings) -> FeedbackApiDependencies:
    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    users = SqlAlchemyUserRepository(session_factory)
    sessions = SqlAlchemySessionRepository(session_factory)
    repository = SqlAlchemyFeedbackRepository(session_factory)
    return FeedbackApiDependencies(
        current_user=CurrentUserQuery(
            users=users,
            sessions=sessions,
            clock=SystemClock(),
        ),
        create_feedback=CreateFeedbackHandler(repository=repository),
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
    from agenttest.modules.browser_profiles.application.publication import (
        BrowserProfilePublicationValidator,
    )
    from agenttest.modules.browser_profiles.infrastructure.repository import (
        SqlAlchemyBrowserProfileRepository,
    )

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
        set_current_version=SetCurrentAgentVersionHandler(
            agents=agents, versions=versions, project_access=access, audit=audit
        ),
        set_baseline_version=SetBaselineAgentVersionHandler(
            agents=agents, versions=versions, project_access=access, audit=audit
        ),
        delete_agent=DeleteAgentHandler(
            agents=agents, versions=versions, project_access=access, audit=audit
        ),
        relationships=SqlAlchemyAgentRelationshipsReader(session_factory),
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
        connection_validator=HttpAgentConnectionValidator(
            allow_private_network=settings.security_scan_allow_private_network
        ),
        publication_validator=BrowserProfilePublicationValidator(
            SqlAlchemyBrowserProfileRepository(session_factory)
        ),
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
    add_case = AddTestCaseHandler(
        datasets=datasets,
        versions=versions,
        cases=cases,
        project_access=access,
        audit=audit,
    )
    runs = SqlAlchemyRunRepository(session_factory)
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
        add_case=add_case,
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
        generate_from_run=GenerateCasesFromFailedRunHandler(
            runs=runs,
            cases=cases,
            add_case=add_case,
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
    versions = SqlAlchemyEnvironmentVersionRepository(session_factory)
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
        list_versions=ListEnvironmentVersionsHandler(
            versions=versions,
            templates=templates,
            project_access=access,
        ),
        get_version=GetEnvironmentVersionHandler(
            versions=versions,
            templates=templates,
            project_access=access,
        ),
        create_version=CreateEnvironmentVersionHandler(
            versions=versions,
            templates=templates,
            project_access=access,
            audit=audit,
        ),
        update_version=UpdateEnvironmentVersionHandler(
            versions=versions,
            templates=templates,
            project_access=access,
            audit=audit,
        ),
        publish_version=PublishEnvironmentVersionHandler(
            versions=versions,
            templates=templates,
            project_access=access,
            audit=audit,
        ),
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
    )


class _UnavailableCredentialCipher:
    """在部署未配置主密钥时拒绝保存凭证。"""

    def encrypt(self, value: str) -> str:
        del value
        raise ValueError("部署未配置 AGENTTEST_MODEL_CREDENTIAL_KEY")


def build_model_config_service(settings: Settings) -> ModelConfigService:
    """构建项目模型配置应用服务。"""

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    repository = SqlAlchemyModelConfigRepository(session_factory)
    projects = SqlAlchemyProjectRepository(session_factory)
    cipher = (
        AesGcmCredentialCipher(settings.model_credential_key)
        if settings.model_credential_key
        else _UnavailableCredentialCipher()
    )
    return ModelConfigService(repository, ProjectAccessAdapter(projects), cipher)


def build_browser_auth_state_service(settings: Settings):
    """Build the profile-bound auth-state cipher from the deployment master key."""
    from base64 import urlsafe_b64decode
    from hashlib import sha256

    from agenttest.modules.browser_profiles.application.auth_state import (
        BrowserAuthStateService,
    )
    from agenttest.modules.browser_profiles.infrastructure.auth_state_cipher import (
        BrowserAuthStateCipher,
    )

    if settings.model_credential_key:
        encoded = settings.model_credential_key
        key = urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    else:
        key = sha256(f"local-browser-auth:{settings.internal_api_token}".encode()).digest()
    return BrowserAuthStateService(BrowserAuthStateCipher(key))


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
        apply_result=ApplyRunResultHandler(
            runs=runs,
            review_collector=SqlAlchemyRunReviewCollector(
                SqlAlchemyReviewTaskRepository(session_factory)
            ),
        ),
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
    )


def _register_artifact_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,  # AuthApiDependencies
) -> None:
    """注册产物上传/列表/下载端点（auth+csrf+project 保护）。"""
    from pathlib import Path
    from uuid import UUID

    from fastapi import Request

    from agenttest.modules.artifacts.api.router import create_artifact_router
    from agenttest.modules.artifacts.infrastructure.storage import (
        FileSystemArtifactStorage,
    )
    from agenttest.modules.identity.application.queries.current_user import (
        InvalidSessionError,
    )
    from agenttest.modules.identity.public import User
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

    async def _actor(request: Request) -> User:
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            raise InvalidSessionError
        return await auth_deps.current_user.execute(token)

    def _check_csrf(request: Request) -> None:
        header = request.headers.get("X-Csrf-Token")
        if not header or header != request.cookies.get(CSRF_NAME):
            raise PermissionError("CSRF mismatch")

    async def _check_project(project_id: UUID) -> None:
        """验证项目存在（SQL 查询）。"""
        from sqlalchemy import text

        async with session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM projects WHERE id = :pid"),
                {"pid": project_id},
            )
            if result.scalar() is None:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="Project not found")

    router = create_artifact_router(
        storage,
        session_factory=session_factory,
        _actor=_actor,
        _check_csrf=_check_csrf,
        _check_project=_check_project,
        internal_token=settings.internal_api_token,
    )
    app.include_router(router, prefix="/api/v1")


def _register_security_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,  # AuthApiDependencies
) -> None:
    """注册安全策略 CRUD 端点（auth+csrf+project 保护）。"""
    from uuid import UUID, uuid4

    from fastapi import Header, Request
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel

    from agenttest.bootstrap.project_access import ProjectAccessAdapter
    from agenttest.modules.identity.application.queries.current_user import (
        InvalidSessionError,
    )
    from agenttest.modules.identity.public import User
    from agenttest.modules.projects.infrastructure.persistence.repositories import (
        SqlAlchemyProjectRepository,
    )
    from agenttest.modules.projects.public import ProjectId, ProjectNotFoundError
    from agenttest.modules.security.domain.models import (
        SecurityPolicy,
    )
    from agenttest.modules.security.infrastructure.repositories import (
        SqlAlchemySecurityPolicyRepository,
    )
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    class CreatePolicyRequest(BaseModel):
        name: str
        max_steps: int = 20
        timeout_seconds: int = 300
        blocked_tools: list[str] = []
        require_confirmation: bool = True
        enabled: bool = True

    CSRF_NAME = "agenttest_csrf"
    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    project_repo = SqlAlchemyProjectRepository(session_factory)
    access = ProjectAccessAdapter(project_repo)

    async def _actor(request: Request) -> User:
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            raise InvalidSessionError
        return await auth_deps.current_user.execute(token)

    @app.get("/api/v1/projects/{project_id}/security/policies")
    async def list_policies(
        request: Request,
        project_id: UUID,
    ):
        try:
            await _actor(request)
            # 项目存在性检查
            from sqlalchemy import text

            async with session_factory() as session:
                result = await session.execute(
                    text("SELECT 1 FROM projects WHERE id = :pid"),
                    {"pid": project_id},
                )
                if result.scalar() is None:
                    return JSONResponse(status_code=404, content={"detail": "Not Found"})
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        async with session_factory() as session:
            repo = SqlAlchemySecurityPolicyRepository(session)
            policies = await repo.list_all(project_id=project_id)
            return {
                "items": [
                    {
                        "id": str(p.id),
                        "name": p.name,
                        "max_steps": p.max_steps,
                        "timeout_seconds": p.timeout_seconds,
                        "blocked_tools": p.blocked_tools,
                        "require_confirmation": p.require_confirmation,
                        "enabled": p.enabled,
                    }
                    for p in policies
                ]
            }

    @app.post("/api/v1/projects/{project_id}/security/policies")
    async def create_policy(
        request: Request,
        project_id: UUID,
        body: CreatePolicyRequest,
        x_csrf_token: str | None = Header(default=None),
    ):
        try:
            actor = await _actor(request)
            if not x_csrf_token or x_csrf_token != request.cookies.get(CSRF_NAME):
                return JSONResponse(status_code=403, content={"detail": "Forbidden"})
            await access.ensure_editor(actor, ProjectId(project_id))
        except InvalidSessionError:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        except ProjectNotFoundError:
            return JSONResponse(status_code=404, content={"detail": "Not Found"})

        async with session_factory() as session:
            repo = SqlAlchemySecurityPolicyRepository(session)
            policy = SecurityPolicy(
                id=uuid4(),
                project_id=project_id,
                name=body.name,
                max_steps=body.max_steps,
                timeout_seconds=body.timeout_seconds,
                blocked_tools=body.blocked_tools,
                require_confirmation=body.require_confirmation,
                enabled=body.enabled,
            )
            await repo.save(policy, project_id=project_id)
            await session.commit()
            return {"id": str(policy.id), "name": policy.name}


def _register_snapshot_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,  # AuthApiDependencies
) -> None:
    """注册环境快照 API。"""
    from agenttest.modules.environments.api.snapshots import create_snapshot_router
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)

    async def check_project(project_id):
        from sqlalchemy import text

        async with session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM projects WHERE id = :pid"),
                {"pid": project_id},
            )
            if result.scalar() is None:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="Project not found")

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_snapshot_router(
        session_factory=session_factory,
        actor_for=actor_for,
        check_project=check_project,
        settings=settings,
    )
    app.include_router(router, prefix="/api/v1")


def _register_dry_run_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,  # AuthApiDependencies
) -> None:
    """注册测试计划试运行 API。"""
    from agenttest.modules.test_plans.api.dry_run import create_dry_run_router
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)

    async def check_project(project_id):
        from sqlalchemy import text

        async with session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM projects WHERE id = :pid"),
                {"pid": project_id},
            )
            if result.scalar() is None:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="Project not found")

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_dry_run_router(
        session_factory=session_factory,
        actor_for=actor_for,
        check_project=check_project,
        settings=settings,
    )
    app.include_router(router, prefix="/api/v1")


def _register_trace_diff_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,  # AuthApiDependencies
) -> None:
    """注册 Trace 对比 API。"""
    from agenttest.modules.runs.api.trace_diff import create_trace_diff_router
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)

    async def check_project(project_id):
        from sqlalchemy import text

        async with session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM projects WHERE id = :pid"),
                {"pid": project_id},
            )
            if result.scalar() is None:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="Project not found")

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_trace_diff_router(
        session_factory=session_factory,
        actor_for=actor_for,
        check_project=check_project,
        settings=settings,
    )
    app.include_router(router, prefix="/api/v1")


def _register_scorer_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,  # AuthApiDependencies
) -> None:
    """注册评分器 CRUD API。"""
    from agenttest.modules.scorers.api.router import create_scorer_router
    from agenttest.modules.scorers.application.model_judge import ModelJudge
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)

    async def check_project(project_id):
        from sqlalchemy import text

        async with session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM projects WHERE id = :pid"),
                {"pid": project_id},
            )
            if result.scalar() is None:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="Project not found")

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_scorer_router(
        session_factory=session_factory,
        actor_for=actor_for,
        check_project=check_project,
        settings=settings,
        model_judge=ModelJudge(
            build_model_config_service(settings),
            TemporalModelInvoker(
                address=settings.temporal_address,
                namespace=settings.temporal_namespace,
                task_queue=settings.model_runner_task_queue,
                allow_private_network=settings.model_allow_private_network,
            ),
        ),
    )
    app.include_router(router, prefix="/api/v1")


def _register_experiment_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,
) -> None:
    """注册实验对比 API。"""
    from agenttest.modules.experiments.api.router import create_experiment_router
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)

    async def check_project(project_id):
        from sqlalchemy import text

        async with session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM projects WHERE id = :pid"),
                {"pid": project_id},
            )
            if result.scalar() is None:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="Project not found")

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_experiment_router(
        session_factory=session_factory,
        actor_for=actor_for,
        check_project=check_project,
        settings=settings,
    )
    app.include_router(router, prefix="/api/v1")


def _register_review_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,
) -> None:
    """注册人工审核 API。"""
    from agenttest.modules.reviews.api.router import create_review_router
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)

    async def check_project(project_id):
        from sqlalchemy import text

        async with session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM projects WHERE id = :pid"),
                {"pid": project_id},
            )
            if result.scalar() is None:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="Project not found")

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_review_router(
        session_factory=session_factory,
        actor_for=actor_for,
        check_project=check_project,
        settings=settings,
    )
    app.include_router(router, prefix="/api/v1")


def _register_security_scan_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,
) -> None:
    """注册安全扫描 API。"""
    from agenttest.modules.security.api.scan_router import create_security_scan_router
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)

    async def check_project(project_id):
        from sqlalchemy import text

        async with session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM projects WHERE id = :pid"),
                {"pid": project_id},
            )
            if result.scalar() is None:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="Project not found")

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    from agenttest.bootstrap.security_target import SqlAlchemySecurityTargetResolver

    router = create_security_scan_router(
        session_factory=session_factory,
        actor_for=actor_for,
        check_project=check_project,
        settings=settings,
        target_resolver=SqlAlchemySecurityTargetResolver(session_factory),
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


def _register_gate_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,
) -> None:
    """注册发布门禁 API。"""
    from agenttest.bootstrap.gate_evidence import SqlAlchemyGateEvidence
    from agenttest.modules.gates.api.router import create_gate_router
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)

    async def check_project(project_id):
        from sqlalchemy import text

        async with session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM projects WHERE id = :pid"),
                {"pid": project_id},
            )
            if result.scalar() is None:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=404,
                    detail="Project not found",
                )

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_gate_router(
        session_factory=session_factory,
        actor_for=actor_for,
        check_project=check_project,
        settings=settings,
        evidence_reader=SqlAlchemyGateEvidence(session_factory),
    )
    app.include_router(router, prefix="/api/v1")


def _register_test_agent_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,
) -> None:
    """注册测试 Agent 对话 API。"""
    from agenttest.modules.agents.infrastructure.persistence.repositories import (
        SqlAlchemyAgentVersionRepository,
    )
    from agenttest.modules.browser_profiles.infrastructure.repository import (
        SqlAlchemyBrowserProfileRepository,
    )
    from agenttest.modules.experiments.infrastructure.persistence.repositories import (
        SqlAlchemyExperimentRepository,
    )
    from agenttest.modules.gates.infrastructure.persistence.repositories import (
        SqlAlchemyReleaseGateRepository,
    )
    from agenttest.modules.identity.infrastructure.persistence.repositories import (
        SqlAlchemyUserRepository,
    )
    from agenttest.modules.model_configs.infrastructure.temporal_invoker import (
        TemporalModelInvoker,
    )
    from agenttest.modules.reviews.infrastructure.persistence.repositories import (
        SqlAlchemyReviewTaskRepository,
    )
    from agenttest.modules.scorers.infrastructure.persistence.repositories import (
        SqlAlchemyScorerRepository,
    )
    from agenttest.modules.security.infrastructure.repositories import (
        SqlAlchemySecurityScanRepository,
    )
    from agenttest.modules.test_accounts.infrastructure.persistence.repositories import (
        SqlAlchemyTestAccountRepository,
    )
    from agenttest.modules.test_agent.adapters.platform import (
        CompositePlatformGateway,
        HandlerPlatformGateway,
    )
    from agenttest.modules.test_agent.api.router import create_test_agent_router
    from agenttest.modules.test_agent.api.target_chat import create_target_chat_router
    from agenttest.modules.test_agent.application.conversation import SuperAgentConversation
    from agenttest.modules.test_agent.application.generations import GenerationCoordinator
    from agenttest.modules.test_agent.application.mission_executor import (
        ConfirmedMissionAssetExecutor,
    )
    from agenttest.modules.test_agent.application.orchestrator import SuperAgentOrchestrator
    from agenttest.modules.test_agent.application.platform_catalog import (
        build_platform_registry,
    )
    from agenttest.modules.test_agent.application.target_chat import TargetChatService
    from agenttest.modules.test_agent.infrastructure.repositories import (
        SqlAlchemyChatGenerationRepository,
        SqlAlchemyChatSessionRepository,
        SqlAlchemyOrchestrationRepository,
        SqlAlchemyTargetChatRepository,
    )
    from agenttest.modules.test_agent.infrastructure.target_runtime import (
        TemporalTargetAgentRuntime,
    )
    from agenttest.modules.test_missions.api.internal_router import (
        create_internal_mission_stage_router,
    )
    from agenttest.modules.test_missions.api.router import (
        MissionApiDependencies,
        create_test_mission_router,
    )
    from agenttest.modules.test_missions.application.capability_gateway import (
        MissionCapabilityGateway,
    )
    from agenttest.modules.test_missions.application.commands import (
        CancelMissionHandler,
        ConfirmMissionHandler,
        DiscoverMissionHandler,
        PreviewMissionHandler,
        ResumeMissionHandler,
        UpsertMissionHandler,
    )
    from agenttest.modules.test_missions.application.compiler import MissionCompiler
    from agenttest.modules.test_missions.application.discovery import MissionDiscovery
    from agenttest.modules.test_missions.application.intake import MissionIntake
    from agenttest.modules.test_missions.application.preflight import MissionPreflight
    from agenttest.modules.test_missions.application.queries import GetMissionHandler
    from agenttest.modules.test_missions.application.resolution import PlatformAssetResolver
    from agenttest.modules.test_missions.application.stage_controller import (
        MissionStageController,
    )
    from agenttest.modules.test_missions.application.stages import MissionStageService
    from agenttest.modules.test_missions.infrastructure.http_discovery import (
        HttpTargetDiscoveryProbe,
        ProjectMissionAccessCatalog,
    )
    from agenttest.modules.test_missions.infrastructure.platform_resolver import (
        PublishedAgentMissionCatalog,
    )
    from agenttest.modules.test_missions.infrastructure.repositories import (
        SqlAlchemyMissionRepository,
    )
    from agenttest.modules.test_missions.infrastructure.temporal_orchestrator import (
        TemporalMissionOrchestrator,
    )
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    orchestration = SqlAlchemyOrchestrationRepository(session_factory)
    model_config_service = build_model_config_service(settings)
    temporal_invoker = TemporalModelInvoker(
        address=settings.temporal_address,
        namespace=settings.temporal_namespace,
        task_queue=settings.model_runner_task_queue,
        allow_private_network=settings.model_allow_private_network,
    )
    mission_repository = SqlAlchemyMissionRepository(session_factory)
    mission_preflight = MissionPreflight()
    mission_runtime = TemporalMissionOrchestrator(
        address=settings.temporal_address,
        namespace=settings.temporal_namespace,
        task_queue=settings.temporal_task_queue,
        callback_base_url=str(settings.control_api_base_url),
    )
    mission_audit = AuditRecorder(SqlAlchemyAuditRepository(session_factory))
    mission_upsert = UpsertMissionHandler(mission_repository, MissionIntake())
    browser_profiles = SqlAlchemyBrowserProfileRepository(session_factory)
    test_accounts = SqlAlchemyTestAccountRepository(session_factory)
    mission_discover = DiscoverMissionHandler(
        mission_repository,
        MissionDiscovery(
            HttpTargetDiscoveryProbe(
                access_catalog=ProjectMissionAccessCatalog(browser_profiles, test_accounts)
            )
        ),
        PlatformAssetResolver(
            PublishedAgentMissionCatalog(SqlAlchemyAgentVersionRepository(session_factory))
        ),
    )
    mission_preview = PreviewMissionHandler(mission_repository, mission_preflight)
    mission_confirm = ConfirmMissionHandler(
        mission_repository, mission_preflight, mission_runtime, mission_audit
    )
    mission_get = GetMissionHandler(mission_repository, mission_preflight)
    gateway = HandlerPlatformGateway(
        agents=build_agent_dependencies(settings),
        datasets=build_dataset_dependencies(settings),
        environments=build_environment_dependencies(settings),
        plans=build_test_plan_dependencies(settings),
        runs=build_run_dependencies(settings),
        scorers=SqlAlchemyScorerRepository(session_factory),
        experiments=SqlAlchemyExperimentRepository(session_factory),
        reviews=SqlAlchemyReviewTaskRepository(session_factory),
        gates=SqlAlchemyReleaseGateRepository(session_factory),
        security=SqlAlchemySecurityScanRepository(session_factory),
        accounts=test_accounts,
        promptfoo_bin=settings.promptfoo_bin,
        allow_private_security_targets=settings.security_scan_allow_private_network,
        gate_evidence=SqlAlchemyGateEvidence(session_factory),
        models=model_config_service,
        invoker=temporal_invoker,
        connection_validator=HttpAgentConnectionValidator(
            allow_private_network=settings.security_scan_allow_private_network
        ),
    )
    composite_gateway = CompositePlatformGateway(
        gateway,
        MissionCapabilityGateway(
            upsert=mission_upsert,
            discover=mission_discover,
            preview=mission_preview,
            confirm=mission_confirm,
            get=mission_get,
        ),
    )
    registry = build_platform_registry(composite_gateway)

    async def check_project(project_id):
        from sqlalchemy import text

        # Convert UUID to hex format (no hyphens) for SQLite compatibility
        if isinstance(project_id, str):
            pid_str = project_id.replace("-", "")
        else:
            pid_str = (
                project_id.hex if hasattr(project_id, "hex") else str(project_id).replace("-", "")
            )

        async with session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM projects WHERE id = :pid"),
                {"pid": pid_str},
            )
            if result.scalar() is None:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=404,
                    detail="Project not found",
                )

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_test_agent_router(
        sessions=SqlAlchemyChatSessionRepository(session_factory),
        orchestration=orchestration,
        actor_for=actor_for,
        check_project=check_project,
        settings=settings,
        conversation=SuperAgentConversation(
            model_config_service,
            temporal_invoker,
            capabilities=registry.describe_all(),
            platform_gateway=composite_gateway,
        ),
        agent_orchestrator=SuperAgentOrchestrator(registry, orchestration),
        generation_coordinator=GenerationCoordinator(
            SqlAlchemyChatGenerationRepository(session_factory),
            orchestration,
            temporal_invoker,
        ),
    )
    app.include_router(router, prefix="/api/v1")
    app.include_router(
        create_test_mission_router(
            dependencies=MissionApiDependencies(
                upsert=mission_upsert,
                discover=mission_discover,
                preview=mission_preview,
                confirm=mission_confirm,
                get=mission_get,
                cancel=CancelMissionHandler(
                    mission_repository, mission_runtime, mission_audit
                ),
                resume=ResumeMissionHandler(
                    mission_repository, mission_runtime, mission_audit
                ),
            ),
            actor_for=actor_for,
            check_project=check_project,
            settings=settings,
        ),
        prefix="/api/v1",
    )
    mission_stages = MissionStageService(
        MissionCompiler(), ConfirmedMissionAssetExecutor(registry), mission_repository
    )
    app.include_router(
        create_internal_mission_stage_router(
            internal_token=settings.internal_api_token,
            controller=MissionStageController(
                mission_repository,
                mission_stages,
                SqlAlchemyUserRepository(session_factory),
            ),
        ),
        prefix="/api/v1",
    )
    target_repository = SqlAlchemyTargetChatRepository(session_factory)
    app.include_router(
        create_target_chat_router(
            service=TargetChatService(
                target_repository,
                TemporalTargetAgentRuntime(
                    address=settings.temporal_address,
                    namespace=settings.temporal_namespace,
                    task_queue=settings.temporal_task_queue,
                ),
            ),
            repository=target_repository,
            agents=build_agent_dependencies(settings),
            environments=build_environment_dependencies(settings),
            datasets=build_dataset_dependencies(settings),
            actor_for=actor_for,
            settings=settings,
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
        create_test_account_router,
    )
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)

    async def check_project(project_id):
        from sqlalchemy import text

        async with session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM projects WHERE id = :pid"),
                {"pid": project_id},
            )
            if result.scalar() is None:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=404,
                    detail="Project not found",
                )

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_test_account_router(
        session_factory=session_factory,
        actor_for=actor_for,
        check_project=check_project,
        settings=settings,
    )
    app.include_router(router, prefix="/api/v1")


def _register_run_stream_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,
) -> None:
    """注册运行进度 SSE 端点。"""
    from agenttest.modules.runs.api.stream import create_run_stream_router
    from agenttest.shared.infrastructure.database import (
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)

    async def check_project(project_id):
        from sqlalchemy import text

        async with session_factory() as session:
            result = await session.execute(
                text("SELECT 1 FROM projects WHERE id = :pid"),
                {"pid": project_id},
            )
            if result.scalar() is None:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=404,
                    detail="Project not found",
                )

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_run_stream_router(
        session_factory=session_factory,
        actor_for=actor_for,
        check_project=check_project,
        settings=settings,
    )
    app.include_router(router, prefix="/api/v1")


def _register_browser_profile_endpoints(
    app: FastAPI,
    settings: Settings,
    auth_deps,  # AuthApiDependencies
) -> None:
    """注册浏览器实例 Profile CRUD API。"""
    from pathlib import Path

    from fastapi import Request
    from sqlalchemy import text

    from agenttest.modules.browser_profiles.api.router import (
        BrowserProfileApiDependencies,
        create_browser_profile_router,
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

    async def check_project(actor, project_id, write):
        role = str(getattr(actor, "role", ""))
        if role == "super_admin":
            return
        user_id = getattr(getattr(actor, "user_id", None), "value", None)
        async with session_factory() as session:
            result = await session.execute(
                text("SELECT role FROM project_members WHERE project_id = :pid AND user_id = :uid"),
                {"pid": project_id, "uid": user_id},
            )
            membership_role = result.scalar()
            if membership_role is None or (
                write and str(membership_role) not in {"developer", "tester"}
            ):
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="Project not found")

    async def actor_for(request: Request):
        token = request.cookies.get(settings.session_cookie_name)
        if not token:
            return None
        return await auth_deps.current_user.execute(token)

    router = create_browser_profile_router(
        settings=settings,
        actor_for=actor_for,
        check_project=check_project,
        dependencies=BrowserProfileApiDependencies(
            repository=SqlAlchemyBrowserProfileRepository(session_factory),
            runtime=ManagedBrowserProfileRuntime(Path(settings.browser_profile_root)),
            auth_state=build_browser_auth_state_service(settings),
        ),
    )
    app.include_router(router)
