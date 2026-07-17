from agenttest.bootstrap.agent_relationships import SqlAlchemyAgentRelationshipsReader
from agenttest.bootstrap.core_summaries import SqlAlchemyCoreSummaryReader
from agenttest.bootstrap.project_access import ProjectAccessAdapter
from agenttest.bootstrap.review_collector import SqlAlchemyRunReviewCollector
from agenttest.bootstrap.run_source import (
    SqlAlchemyCaseTrialRuntimeSource,
    SqlAlchemyRunSource,
)
from agenttest.bootstrap.settings import Settings
from agenttest.modules.agents.api.router import (
    AgentApiDependencies,
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
from agenttest.modules.audit.api.router import AuditApiDependencies
from agenttest.modules.audit.application.record import AuditRecorder
from agenttest.modules.audit.infrastructure.persistence.repositories import (
    SqlAlchemyAuditRepository,
)
from agenttest.modules.datasets.api.router import (
    DatasetApiDependencies,
)
from agenttest.modules.datasets.application.commands import (
    AddTestCaseHandler,
    CreateDatasetHandler,
    CreateDatasetVersionHandler,
    DeleteTestCaseHandler,
    DuplicateTestCaseHandler,
    MarkTestCaseReadyHandler,
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
from agenttest.modules.datasets.application.trial_runs import CreateCaseTrialRunHandler
from agenttest.modules.datasets.infrastructure.persistence.repositories import (
    SqlAlchemyDatasetRepository,
    SqlAlchemyDatasetVersionRepository,
    SqlAlchemyTestCaseRepository,
)
from agenttest.modules.environments.api.router import (
    EnvironmentApiDependencies,
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
)
from agenttest.modules.feedback.application.commands import CreateFeedbackHandler
from agenttest.modules.feedback.infrastructure.persistence.repositories import (
    SqlAlchemyFeedbackRepository,
)
from agenttest.modules.identity.api.admin_router import (
    AdminApiDependencies,
)
from agenttest.modules.identity.application.commands.create_user import CreateUserHandler
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
from agenttest.modules.model_configs.application.service import ModelConfigService
from agenttest.modules.model_configs.infrastructure.credentials import AesGcmCredentialCipher
from agenttest.modules.model_configs.infrastructure.persistence.repositories import (
    SqlAlchemyModelConfigRepository,
)
from agenttest.modules.projects.api.router import (
    ProjectApiDependencies,
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
    SqlAlchemyProjectAssetKeyAllocator,
    SqlAlchemyProjectRepository,
)
from agenttest.modules.reviews.infrastructure.persistence.repositories import (
    SqlAlchemyReviewTaskRepository,
)
from agenttest.modules.runs.api.router import RunApiDependencies
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
        summaries=SqlAlchemyCoreSummaryReader(session_factory),
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
        summaries=SqlAlchemyCoreSummaryReader(session_factory),
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
        case_key_allocator=SqlAlchemyProjectAssetKeyAllocator(session_factory),
        audit=audit,
    )
    runs = SqlAlchemyRunRepository(session_factory)
    trial_orchestrator = (
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
        mark_case_ready=MarkTestCaseReadyHandler(
            datasets=datasets,
            versions=versions,
            cases=cases,
            project_access=access,
            audit=audit,
        ),
        duplicate_case=DuplicateTestCaseHandler(cases=cases, add_case=add_case),
        trial_run=CreateCaseTrialRunHandler(
            datasets=datasets,
            versions=versions,
            cases=cases,
            runs=runs,
            project_access=access,
            runtime_source=SqlAlchemyCaseTrialRuntimeSource(session_factory),
            orchestrator=trial_orchestrator,
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
            case_key_allocator=SqlAlchemyProjectAssetKeyAllocator(session_factory),
        ),
        generate_from_run=GenerateCasesFromFailedRunHandler(
            runs=runs,
            cases=cases,
            add_case=add_case,
        ),
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
        summaries=SqlAlchemyCoreSummaryReader(session_factory),
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
        summaries=SqlAlchemyCoreSummaryReader(session_factory),
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
        summaries=SqlAlchemyCoreSummaryReader(session_factory),
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
    from agenttest.modules.run_postprocessing.application import PostprocessJobService
    from agenttest.modules.run_postprocessing.infrastructure.repository import (
        SqlAlchemyPostprocessRepository,
    )
    from agenttest.modules.run_postprocessing.infrastructure.temporal import (
        TemporalPostprocessScheduler,
    )

    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    runs = SqlAlchemyRunRepository(session_factory)
    projects = SqlAlchemyProjectRepository(session_factory)
    access = ProjectAccessAdapter(projects)
    postprocess_scheduler = (
        TemporalPostprocessScheduler(
            address=settings.temporal_address,
            namespace=settings.temporal_namespace,
            task_queue=settings.temporal_task_queue,
            callback_base_url=settings.control_api_base_url,
        )
        if settings.temporal_address
        else None
    )
    postprocess = PostprocessJobService(
        SqlAlchemyPostprocessRepository(session_factory), postprocess_scheduler
    )
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
            postprocess=postprocess,
        ),
        postprocess=postprocess,
        uow_factory=lambda: SqlAlchemyUnitOfWork(session_factory),
        summaries=SqlAlchemyCoreSummaryReader(session_factory),
    )
