from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import pytest
from agenttest.modules.identity.application.commands.login import (
    InvalidCredentialsError,
    LoginCommand,
    LoginHandler,
)
from agenttest.modules.identity.application.commands.logout import LogoutHandler
from agenttest.modules.identity.application.ports import SessionRecord
from agenttest.modules.identity.application.queries.current_user import (
    CurrentUserQuery,
    InvalidSessionError,
)
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email, SystemRole, UserId
from agenttest.modules.identity.infrastructure.passwords import Argon2PasswordHasher


class FrozenClock:
    def __init__(self, current: datetime) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current


class FakeUserRepository:
    def __init__(self, user: User | None) -> None:
        self.user = user

    async def get_by_email(self, email: Email) -> User | None:
        if self.user is not None and self.user.email == email:
            return self.user
        return None

    async def get_by_id(self, user_id: UserId) -> User | None:
        if self.user is not None and self.user.user_id == user_id:
            return self.user
        return None


class FakeCredentialRepository:
    def __init__(self, password_hash: str | None) -> None:
        self.password_hash = password_hash

    async def get_password_hash(self, user_id: UserId) -> str | None:
        return self.password_hash


class FakeSessionRepository:
    def __init__(self) -> None:
        self.session: SessionRecord | None = None

    async def add(self, session: SessionRecord) -> None:
        self.session = session

    async def get_by_token_hash(self, token_hash: str) -> SessionRecord | None:
        if self.session is not None and self.session.token_hash == token_hash:
            return self.session
        return None

    async def revoke_by_token_hash(self, token_hash: str, revoked_at: datetime) -> None:
        if self.session is not None and self.session.token_hash == token_hash:
            self.session = replace(self.session, revoked_at=revoked_at)


def create_user() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("user@example.com"),
        display_name="User",
        role=SystemRole.DEVELOPER,
    )


@pytest.mark.asyncio
async def test_correct_password_creates_hashed_server_session() -> None:
    now = datetime(2026, 6, 25, tzinfo=UTC)
    user = create_user()
    hasher = Argon2PasswordHasher()
    sessions = FakeSessionRepository()
    handler = LoginHandler(
        users=FakeUserRepository(user),
        credentials=FakeCredentialRepository(hasher.hash("correct-password")),
        sessions=sessions,
        password_hasher=hasher,
        clock=FrozenClock(now),
        session_ttl=timedelta(hours=8),
    )

    result = await handler.execute(LoginCommand(email=user.email, password="correct-password"))

    assert sessions.session is not None
    assert sessions.session.user_id == user.user_id
    assert sessions.session.token_hash == sha256(result.session_token.encode()).hexdigest()
    assert sessions.session.token_hash != result.session_token
    assert sessions.session.expires_at == now + timedelta(hours=8)
    assert len(result.session_token) >= 43
    assert len(result.csrf_token) >= 43


@pytest.mark.asyncio
@pytest.mark.parametrize("known_user", [True, False])
async def test_wrong_password_and_unknown_email_share_public_error(known_user: bool) -> None:
    user = create_user()
    hasher = Argon2PasswordHasher()
    handler = LoginHandler(
        users=FakeUserRepository(user if known_user else None),
        credentials=FakeCredentialRepository(
            hasher.hash("correct-password") if known_user else None
        ),
        sessions=FakeSessionRepository(),
        password_hasher=hasher,
        clock=FrozenClock(datetime(2026, 6, 25, tzinfo=UTC)),
        session_ttl=timedelta(hours=8),
    )

    with pytest.raises(InvalidCredentialsError, match="Invalid email or password"):
        await handler.execute(LoginCommand(email=user.email, password="wrong-password"))


@pytest.mark.asyncio
async def test_disabled_user_cannot_log_in() -> None:
    user = create_user()
    user.disable()
    hasher = Argon2PasswordHasher()
    handler = LoginHandler(
        users=FakeUserRepository(user),
        credentials=FakeCredentialRepository(hasher.hash("correct-password")),
        sessions=FakeSessionRepository(),
        password_hasher=hasher,
        clock=FrozenClock(datetime(2026, 6, 25, tzinfo=UTC)),
        session_ttl=timedelta(hours=8),
    )

    with pytest.raises(InvalidCredentialsError, match="Invalid email or password"):
        await handler.execute(LoginCommand(email=user.email, password="correct-password"))


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["expired", "revoked"])
async def test_expired_and_revoked_sessions_are_rejected(state: str) -> None:
    now = datetime(2026, 6, 25, tzinfo=UTC)
    user = create_user()
    sessions = FakeSessionRepository()
    token = "raw-session-token"
    sessions.session = SessionRecord(
        user_id=user.user_id,
        token_hash=sha256(token.encode()).hexdigest(),
        csrf_token_hash=sha256(b"csrf").hexdigest(),
        expires_at=now - timedelta(seconds=1) if state == "expired" else now + timedelta(hours=1),
        revoked_at=now if state == "revoked" else None,
        created_at=now - timedelta(hours=1),
    )
    query = CurrentUserQuery(
        users=FakeUserRepository(user),
        sessions=sessions,
        clock=FrozenClock(now),
    )

    with pytest.raises(InvalidSessionError):
        await query.execute(token)


@pytest.mark.asyncio
async def test_logout_revokes_current_session() -> None:
    now = datetime(2026, 6, 25, tzinfo=UTC)
    sessions = FakeSessionRepository()
    token = "raw-session-token"
    sessions.session = SessionRecord(
        user_id=create_user().user_id,
        token_hash=sha256(token.encode()).hexdigest(),
        csrf_token_hash=sha256(b"csrf").hexdigest(),
        expires_at=now + timedelta(hours=1),
        revoked_at=None,
        created_at=now,
    )

    await LogoutHandler(sessions=sessions, clock=FrozenClock(now)).execute(token)

    assert sessions.session.revoked_at == now


def test_password_hasher_uses_argon2id() -> None:
    password_hash = Argon2PasswordHasher().hash("correct-password")

    assert password_hash.startswith("$argon2id$")
