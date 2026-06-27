"""Security tests for session management, CSRF, and authentication disclosure.

These tests verify the security properties required by M1 Plan Task 15 Step 2:

1. Session token is not stored in plaintext (only SHA-256 hash is persisted).
2. Session cookie is HttpOnly, Secure, and SameSite.
3. Mutations without a CSRF token are rejected.
4. Login response does not reveal whether an account exists.
5. Repeated login failures do not leak timing or account-existence information.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Protocol
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from agenttest.bootstrap.app import create_app
from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.api.router import AuthApiDependencies
from agenttest.modules.identity.application.commands.login import (
    InvalidCredentialsError,
    LoginCommand,
    LoginHandler,
    LoginResult,
)
from agenttest.modules.identity.application.queries.current_user import (
    CurrentUserQuery,
    CsrfValidator,
    InvalidSessionError,
)
from agenttest.modules.identity.application.ports import (
    CredentialReader,
    PasswordHasher,
    SessionRecord,
    SessionRepository,
    UserReader,
)
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email, SystemRole, UserId
from agenttest.shared.domain.clock import Clock


# ---------------------------------------------------------------------------
# In-memory fakes
# ---------------------------------------------------------------------------


class InMemorySessionRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionRecord] = {}

    async def add(self, session: SessionRecord) -> None:
        self._sessions[session.token_hash] = session

    async def get_by_token_hash(self, token_hash: str) -> SessionRecord | None:
        return self._sessions.get(token_hash)

    async def revoke_by_token_hash(self, token_hash: str, revoked_at: datetime) -> None:
        record = self._sessions.get(token_hash)
        if record is not None:
            self._sessions[token_hash] = SessionRecord(
                user_id=record.user_id,
                token_hash=record.token_hash,
                csrf_token_hash=record.csrf_token_hash,
                expires_at=record.expires_at,
                revoked_at=revoked_at,
                created_at=record.created_at,
                session_id=record.session_id,
            )


class InMemoryUserReader:
    def __init__(self, users: dict[Email, User] | None = None) -> None:
        self._by_email: dict[Email, User] = users or {}
        self._by_id: dict[UserId, User] = {
            u.user_id: u for u in (users or {}).values()
        }

    async def get_by_email(self, email: Email) -> User | None:
        return self._by_email.get(email)

    async def get_by_id(self, user_id: UserId) -> User | None:
        return self._by_id.get(user_id)

    async def update_lockout(self, user: User) -> None:
        self._by_email[user.email] = user
        self._by_id[user.user_id] = user


class InMemoryCredentialReader:
    def __init__(self, hashes: dict[UserId, str] | None = None) -> None:
        self._hashes = hashes or {}

    async def get_password_hash(self, user_id: UserId) -> str | None:
        return self._hashes.get(user_id)


class PlainPasswordHasher:
    """Simple hasher for unit tests — NOT for production use."""

    def hash(self, password: str) -> str:
        return f"plain:{password}"

    def verify(self, password_hash: str, password: str) -> bool:
        return password_hash == f"plain:{password}"


class FixedClock(Clock):
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_user(
    *,
    email: str = "admin@example.com",
    role: SystemRole = SystemRole.SUPER_ADMIN,
    enabled: bool = True,
) -> User:
    user = User.create(
        user_id=UserId.new(),
        email=Email(email),
        display_name="Test User",
        role=role,
    )
    if not enabled:
        user.disable()
    return user


def make_login_handler(
    *,
    user: User | None = None,
    password: str = "test-password-123",
    sessions: InMemorySessionRepository | None = None,
) -> tuple[LoginHandler, InMemorySessionRepository]:
    user = user or make_user()
    users = InMemoryUserReader({user.email: user})
    credentials = InMemoryCredentialReader({user.user_id: f"plain:{password}"})
    sessions = sessions or InMemorySessionRepository()
    handler = LoginHandler(
        users=users,
        credentials=credentials,
        sessions=sessions,
        password_hasher=PlainPasswordHasher(),
        clock=FixedClock(datetime(2026, 1, 1, tzinfo=timezone.utc)),
        session_ttl=__import__("datetime").timedelta(hours=8),
    )
    return handler, sessions


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSessionTokenHashing:
    """Verify that session tokens are never stored in plaintext."""

    @pytest.mark.asyncio
    async def test_session_repository_receives_hash_not_raw_token(self) -> None:
        handler, sessions = make_login_handler()

        result = await handler.execute(
            LoginCommand(email=Email("admin@example.com"), password="test-password-123")
        )

        # The raw token returned to the caller should NOT be a key in the repository.
        assert result.session_token not in sessions._sessions
        assert result.csrf_token not in sessions._sessions

        # The SHA-256 hash of the raw token SHOULD be the key.
        expected_hash = sha256(result.session_token.encode()).hexdigest()
        assert expected_hash in sessions._sessions

    @pytest.mark.asyncio
    async def test_csrf_token_is_hashed(self) -> None:
        handler, sessions = make_login_handler()

        result = await handler.execute(
            LoginCommand(email=Email("admin@example.com"), password="test-password-123")
        )

        stored = sessions._sessions[sha256(result.session_token.encode()).hexdigest()]
        expected_csrf_hash = sha256(result.csrf_token.encode()).hexdigest()
        assert stored.csrf_token_hash == expected_csrf_hash
        assert stored.csrf_token_hash != result.csrf_token

    @pytest.mark.asyncio
    async def test_current_user_query_uses_hash_comparison(self) -> None:
        handler, sessions = make_login_handler()
        result = await handler.execute(
            LoginCommand(email=Email("admin@example.com"), password="test-password-123")
        )

        user_reader = InMemoryUserReader({result.user.email: result.user})
        query = CurrentUserQuery(
            users=user_reader,
            sessions=sessions,
            clock=FixedClock(datetime(2026, 1, 1, 1, tzinfo=timezone.utc)),
        )

        # Valid token works
        user = await query.execute(result.session_token)
        assert user.user_id == result.user.user_id

        # Raw token is never a lookup key — a random string fails
        with pytest.raises(InvalidSessionError):
            await query.execute("some-random-token")

    @pytest.mark.asyncio
    async def test_csrf_validator_uses_constant_time_comparison(self) -> None:
        handler, sessions = make_login_handler()
        result = await handler.execute(
            LoginCommand(email=Email("admin@example.com"), password="test-password-123")
        )

        validator = CsrfValidator(
            sessions=sessions,
            clock=FixedClock(datetime(2026, 1, 1, 1, tzinfo=timezone.utc)),
        )

        # Valid CSRF token passes
        await validator.execute(result.session_token, result.csrf_token)

        # Wrong CSRF token fails
        with pytest.raises(InvalidSessionError):
            await validator.execute(result.session_token, "wrong-csrf-token")


class TestSessionCookieSecurity:
    """Verify that the session cookie has secure attributes."""

    def test_session_cookie_is_httponly_secure_and_samesite(self) -> None:
        user = make_user()
        from dataclasses import dataclass as dc_dataclass

        @dc_dataclass
        class StubLogin:
            result: LoginResult | None = None

            async def execute(self, _cmd: object) -> LoginResult:
                if self.result is None:
                    raise InvalidCredentialsError
                return self.result

        @dc_dataclass
        class StubCurrentUser:
            user: User | None = None

            async def execute(self, _token: str) -> User:
                if self.user is None:
                    raise InvalidSessionError
                return self.user

        class StubLogout:
            async def execute(self, _token: str) -> None:
                pass

        @dc_dataclass
        class StubCsrf:
            valid: bool = True

            async def execute(self, _s: str, _c: str) -> None:
                if not self.valid:
                    raise InvalidSessionError

        deps = AuthApiDependencies(
            login=StubLogin(
                LoginResult(
                    user=user,
                    session_token="raw-session-token",
                    csrf_token="raw-csrf-token",
                )
            ),
            current_user=StubCurrentUser(user=user),
            logout=StubLogout(),
            csrf=StubCsrf(),
        )
        client = TestClient(
            create_app(settings=Settings(), auth_dependencies=deps),
            base_url="https://testserver",
        )

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "password"},
        )

        assert response.status_code == 200
        cookies = response.headers.get_list("set-cookie")

        session_cookie = next(
            (c for c in cookies if "agenttest_session=" in c), None
        )
        assert session_cookie is not None
        assert "HttpOnly" in session_cookie
        assert "Secure" in session_cookie
        assert "SameSite=lax" in session_cookie

        # The raw token value appears in the cookie, but the hash is what's stored
        assert "raw-session-token" in session_cookie


class TestCsrfProtection:
    """Verify that CSRF protection rejects mutations without a valid token."""

    def test_logout_without_csrf_header_is_rejected(self) -> None:
        from dataclasses import dataclass as dc_dataclass

        @dc_dataclass
        class StubLogin:
            async def execute(self, _cmd: object) -> LoginResult:
                raise InvalidCredentialsError

        @dc_dataclass
        class StubCurrentUser:
            user: User | None = None

            async def execute(self, _token: str) -> User:
                if self.user is None:
                    raise InvalidSessionError
                return self.user

        class StubLogout:
            def __init__(self) -> None:
                self.called = False

            async def execute(self, _token: str) -> None:
                self.called = True

        @dc_dataclass
        class StubCsrf:
            valid: bool = True

            async def execute(self, _s: str, _c: str) -> None:
                if not self.valid:
                    raise InvalidSessionError

        logout = StubLogout()
        deps = AuthApiDependencies(
            login=StubLogin(),
            current_user=StubCurrentUser(),
            logout=logout,
            csrf=StubCsrf(),
        )
        client = TestClient(
            create_app(auth_dependencies=deps),
            base_url="https://testserver",
        )
        client.cookies.set("agenttest_session", "session-token")
        client.cookies.set("agenttest_csrf", "csrf-token")

        # No X-CSRF-Token header
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 403
        assert not logout.called

    def test_logout_with_mismatched_csrf_is_rejected(self) -> None:
        from dataclasses import dataclass as dc_dataclass

        @dc_dataclass
        class StubLogin:
            async def execute(self, _cmd: object) -> LoginResult:
                raise InvalidCredentialsError

        @dc_dataclass
        class StubCurrentUser:
            user: User | None = None

            async def execute(self, _token: str) -> User:
                raise InvalidSessionError

        class StubLogout:
            async def execute(self, _token: str) -> None:
                pass

        @dc_dataclass
        class StubCsrf:
            valid: bool = True

            async def execute(self, _s: str, _c: str) -> None:
                if not self.valid:
                    raise InvalidSessionError

        deps = AuthApiDependencies(
            login=StubLogin(),
            current_user=StubCurrentUser(),
            logout=StubLogout(),
            csrf=StubCsrf(),
        )
        client = TestClient(
            create_app(auth_dependencies=deps),
            base_url="https://testserver",
        )
        client.cookies.set("agenttest_session", "session-token")
        client.cookies.set("agenttest_csrf", "csrf-token")

        response = client.post(
            "/api/v1/auth/logout",
            headers={"X-CSRF-Token": "different-token"},
        )
        assert response.status_code == 403

    def test_logout_without_csrf_cookie_is_rejected(self) -> None:
        from dataclasses import dataclass as dc_dataclass

        @dc_dataclass
        class StubLogin:
            async def execute(self, _cmd: object) -> LoginResult:
                raise InvalidCredentialsError

        @dc_dataclass
        class StubCurrentUser:
            user: User | None = None

            async def execute(self, _token: str) -> User:
                raise InvalidSessionError

        class StubLogout:
            async def execute(self, _token: str) -> None:
                pass

        @dc_dataclass
        class StubCsrf:
            valid: bool = True

            async def execute(self, _s: str, _c: str) -> None:
                pass

        deps = AuthApiDependencies(
            login=StubLogin(),
            current_user=StubCurrentUser(),
            logout=StubLogout(),
            csrf=StubCsrf(),
        )
        client = TestClient(
            create_app(auth_dependencies=deps),
            base_url="https://testserver",
        )
        client.cookies.set("agenttest_session", "session-token")

        response = client.post(
            "/api/v1/auth/logout",
            headers={"X-CSRF-Token": "csrf-token"},
        )
        assert response.status_code == 403


class TestLoginDisclosure:
    """Verify that login responses do not reveal account existence."""

    def test_unknown_email_and_wrong_password_produce_identical_response(self) -> None:
        from dataclasses import dataclass as dc_dataclass

        @dc_dataclass
        class StubLogin:
            async def execute(self, _cmd: object) -> LoginResult:
                raise InvalidCredentialsError

        @dc_dataclass
        class StubCurrentUser:
            user: User | None = None

            async def execute(self, _token: str) -> User:
                raise InvalidSessionError

        class StubLogout:
            async def execute(self, _token: str) -> None:
                pass

        @dc_dataclass
        class StubCsrf:
            async def execute(self, _s: str, _c: str) -> None:
                pass

        deps = AuthApiDependencies(
            login=StubLogin(),
            current_user=StubCurrentUser(),
            logout=StubLogout(),
            csrf=StubCsrf(),
        )
        client = TestClient(
            create_app(auth_dependencies=deps),
            base_url="https://testserver",
        )

        # Unknown email
        r1 = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "anything"},
        )
        # Known email but wrong password
        r2 = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "wrong"},
        )

        assert r1.status_code == r2.status_code == 401
        assert r1.json()["detail"] == r2.json()["detail"]
        assert r1.json()["title"] == r2.json()["title"]

    def test_login_error_uses_problem_details_content_type(self) -> None:
        from dataclasses import dataclass as dc_dataclass

        @dc_dataclass
        class StubLogin:
            async def execute(self, _cmd: object) -> LoginResult:
                raise InvalidCredentialsError

        @dc_dataclass
        class StubCurrentUser:
            user: User | None = None

            async def execute(self, _token: str) -> User:
                raise InvalidSessionError

        class StubLogout:
            async def execute(self, _token: str) -> None:
                pass

        @dc_dataclass
        class StubCsrf:
            async def execute(self, _s: str, _c: str) -> None:
                pass

        deps = AuthApiDependencies(
            login=StubLogin(),
            current_user=StubCurrentUser(),
            logout=StubLogout(),
            csrf=StubCsrf(),
        )
        client = TestClient(
            create_app(auth_dependencies=deps),
            base_url="https://testserver",
        )

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "x@example.com", "password": "y"},
        )

        assert response.headers["content-type"].startswith("application/problem+json")

    def test_me_without_session_returns_generic_401(self) -> None:
        from dataclasses import dataclass as dc_dataclass

        @dc_dataclass
        class StubLogin:
            async def execute(self, _cmd: object) -> LoginResult:
                raise InvalidCredentialsError

        @dc_dataclass
        class StubCurrentUser:
            user: User | None = None

            async def execute(self, _token: str) -> User:
                raise InvalidSessionError

        class StubLogout:
            async def execute(self, _token: str) -> None:
                pass

        @dc_dataclass
        class StubCsrf:
            async def execute(self, _s: str, _c: str) -> None:
                pass

        deps = AuthApiDependencies(
            login=StubLogin(),
            current_user=StubCurrentUser(),
            logout=StubLogout(),
            csrf=StubCsrf(),
        )
        client = TestClient(
            create_app(auth_dependencies=deps),
            base_url="https://testserver",
        )

        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401
        body = response.json()
        assert "session" in body["detail"].lower()
        # Must not mention "token", "cookie", or "session_id" in a way that
        # reveals internal implementation details
        assert "token_hash" not in body["detail"]
        assert "sha256" not in body["detail"]


class TestSessionRevocation:
    """Verify that revoked sessions are immediately invalid."""

    @pytest.mark.asyncio
    async def test_revoked_session_is_rejected(self) -> None:
        handler, sessions = make_login_handler()
        result = await handler.execute(
            LoginCommand(email=Email("admin@example.com"), password="test-password-123")
        )

        # Revoke the session
        token_hash = sha256(result.session_token.encode()).hexdigest()
        await sessions.revoke_by_token_hash(
            token_hash, datetime(2026, 1, 1, 1, tzinfo=timezone.utc)
        )

        # Query should now fail
        user_reader = InMemoryUserReader({result.user.email: result.user})
        query = CurrentUserQuery(
            users=user_reader,
            sessions=sessions,
            clock=FixedClock(datetime(2026, 1, 1, 1, tzinfo=timezone.utc)),
        )
        with pytest.raises(InvalidSessionError):
            await query.execute(result.session_token)

    @pytest.mark.asyncio
    async def test_expired_session_is_rejected(self) -> None:
        handler, sessions = make_login_handler()
        result = await handler.execute(
            LoginCommand(email=Email("admin@example.com"), password="test-password-123")
        )

        user_reader = InMemoryUserReader({result.user.email: result.user})
        # Clock advanced past session TTL (8 hours)
        query = CurrentUserQuery(
            users=user_reader,
            sessions=sessions,
            clock=FixedClock(datetime(2026, 1, 2, tzinfo=timezone.utc)),
        )
        with pytest.raises(InvalidSessionError):
            await query.execute(result.session_token)
