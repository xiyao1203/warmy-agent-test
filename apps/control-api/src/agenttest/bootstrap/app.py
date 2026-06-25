from datetime import timedelta

from fastapi import FastAPI

from agenttest.bootstrap.settings import Settings, get_settings
from agenttest.entrypoints.http.health import router as health_router
from agenttest.modules.audit.api.router import AuditApiDependencies, create_audit_router
from agenttest.modules.audit.application.record import AuditRecorder
from agenttest.modules.audit.infrastructure.persistence.repositories import (
    SqlAlchemyAuditRepository,
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
) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(
        title="Warmy Agent Test Control API",
        version=resolved_settings.app_version,
    )
    app.state.settings = resolved_settings
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
    return app


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
