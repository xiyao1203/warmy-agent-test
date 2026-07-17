from __future__ import annotations

from datetime import timedelta

from agenttest.bootstrap.settings import Settings
from agenttest.modules.audit.application.record import AuditRecorder
from agenttest.modules.audit.infrastructure.persistence.repositories import (
    SqlAlchemyAuditRepository,
)
from agenttest.modules.identity.api.router import AuthApiDependencies
from agenttest.modules.identity.application.commands.change_password import (
    ChangePasswordHandler,
)
from agenttest.modules.identity.application.commands.login import LoginHandler
from agenttest.modules.identity.application.commands.logout import LogoutHandler
from agenttest.modules.identity.application.commands.update_profile import (
    UpdateProfileHandler,
)
from agenttest.modules.identity.application.login_throttle import (
    LoginThrottle,
    LoginThrottlePolicy,
)
from agenttest.modules.identity.application.queries.current_user import (
    CsrfValidator,
    CurrentUserQuery,
)
from agenttest.modules.identity.infrastructure.passwords import Argon2PasswordHasher
from agenttest.modules.identity.infrastructure.persistence.repositories import (
    SqlAlchemyCredentialRepository,
    SqlAlchemyLoginThrottleRepository,
    SqlAlchemySessionRepository,
    SqlAlchemyUserRepository,
)
from agenttest.shared.domain.clock import SystemClock
from agenttest.shared.infrastructure.database import (
    SqlAlchemyUnitOfWork,
    create_database_engine,
    create_session_factory,
)


def build_auth_dependencies(settings: Settings) -> AuthApiDependencies:
    engine = create_database_engine(str(settings.database_url))
    session_factory = create_session_factory(engine)
    users = SqlAlchemyUserRepository(session_factory)
    credentials = SqlAlchemyCredentialRepository(session_factory)
    sessions = SqlAlchemySessionRepository(session_factory)
    audit = AuditRecorder(SqlAlchemyAuditRepository(session_factory))
    clock = SystemClock()
    throttle = LoginThrottle(
        repository=SqlAlchemyLoginThrottleRepository(session_factory),
        clock=clock,
        policy=LoginThrottlePolicy(
            window=timedelta(seconds=settings.login_throttle_window_seconds),
            max_failures=settings.login_throttle_max_failures,
            blocked_for=timedelta(seconds=settings.login_throttle_block_seconds),
        ),
        pepper=(settings.login_throttle_pepper or settings.internal_api_token).encode(),
    )
    return AuthApiDependencies(
        login=LoginHandler(
            users=users,
            credentials=credentials,
            sessions=sessions,
            password_hasher=Argon2PasswordHasher(),
            clock=clock,
            session_ttl=timedelta(seconds=settings.session_ttl_seconds),
            throttle=throttle,
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
