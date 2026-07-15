from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from agenttest.modules.audit.public import AuditEntry, AuditRecorder
from agenttest.modules.identity.application.commands.create_user import (
    CreateUserCommand,
    CreateUserHandler,
)
from agenttest.modules.identity.application.commands.login import (
    InvalidCredentialsError,
    LoginCommand,
    LoginHandler,
    NoopLoginThrottle,
)
from agenttest.modules.identity.application.ports import SessionRecord
from agenttest.modules.identity.infrastructure.passwords import Argon2PasswordHasher
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.application.commands.create_project import (
    CreateProjectCommand,
    CreateProjectHandler,
)
from agenttest.modules.projects.domain.entities import Project


class AuditSink:
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    async def append(self, entry: AuditEntry) -> None:
        self.entries.append(entry)


class FrozenClock:
    def now(self) -> datetime:
        return datetime(2026, 6, 25, tzinfo=UTC)


class IdentityRepository:
    def __init__(self, user: User | None = None) -> None:
        self.user = user

    async def get_by_email(self, email: Email) -> User | None:
        return self.user if self.user is not None and self.user.email == email else None

    async def get_by_id(self, user_id: UserId) -> User | None:
        return self.user if self.user is not None and self.user.user_id == user_id else None

    async def add(self, user: User) -> None:
        self.user = user

    async def update_lockout(self, user: User) -> None:
        pass


class Credentials:
    def __init__(self, password_hash: str | None = None) -> None:
        self.password_hash = password_hash

    async def get_password_hash(self, _user_id: UserId) -> str | None:
        return self.password_hash

    async def set_password_hash(self, _user_id: UserId, password_hash: str) -> None:
        self.password_hash = password_hash


class Sessions:
    async def add(self, _session: SessionRecord) -> None:
        return None

    async def get_by_token_hash(self, _token_hash: str) -> SessionRecord | None:
        return None

    async def revoke_by_token_hash(self, _token_hash: str, _revoked_at: datetime) -> None:
        return None


class Projects:
    def __init__(self) -> None:
        self.project: Project | None = None

    async def add(self, project: Project) -> None:
        self.project = project


def user(role: SystemRole = SystemRole.SUPER_ADMIN) -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("admin@example.com"),
        display_name="Admin",
        role=role,
    )


@pytest.mark.asyncio
async def test_successful_login_records_audit_without_raw_password() -> None:
    actor = user(SystemRole.DEVELOPER)
    hasher = Argon2PasswordHasher()
    sink = AuditSink()
    handler = LoginHandler(
        users=IdentityRepository(actor),
        credentials=Credentials(hasher.hash("correct-password")),
        sessions=Sessions(),
        password_hasher=hasher,
        clock=FrozenClock(),
        session_ttl=timedelta(hours=8),
        throttle=NoopLoginThrottle(),
        audit=AuditRecorder(sink),
    )

    await handler.execute(LoginCommand(email=actor.email, password="correct-password"))

    assert sink.entries[0].action == "identity.login.succeeded"
    assert "password" not in str(sink.entries[0].changes).lower()


@pytest.mark.asyncio
async def test_failed_login_records_failure_audit() -> None:
    sink = AuditSink()
    handler = LoginHandler(
        users=IdentityRepository(),
        credentials=Credentials(),
        sessions=Sessions(),
        password_hasher=Argon2PasswordHasher(),
        clock=FrozenClock(),
        session_ttl=timedelta(hours=8),
        throttle=NoopLoginThrottle(),
        audit=AuditRecorder(sink),
    )

    with pytest.raises(InvalidCredentialsError):
        await handler.execute(LoginCommand(email=Email("unknown@example.com"), password="wrong"))

    assert sink.entries[0].action == "identity.login.failed"


@pytest.mark.asyncio
async def test_user_and_project_creation_record_audit_after_success() -> None:
    actor = user()
    identity_sink = AuditSink()
    project_sink = AuditSink()
    credentials = Credentials()
    await CreateUserHandler(
        users=IdentityRepository(),
        credentials=credentials,
        password_hasher=Argon2PasswordHasher(),
        audit=AuditRecorder(identity_sink),
    ).execute(
        actor,
        CreateUserCommand(
            email=Email("new@example.com"),
            display_name="New",
            role=SystemRole.TESTER,
            initial_password="initial-password",
        ),
    )
    await CreateProjectHandler(
        projects=Projects(),
        audit=AuditRecorder(project_sink),
    ).execute(actor, CreateProjectCommand(name="Project"))

    assert identity_sink.entries[0].action == "identity.user.created"
    assert project_sink.entries[0].action == "projects.created"
