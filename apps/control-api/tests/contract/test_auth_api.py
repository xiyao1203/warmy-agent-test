from __future__ import annotations

from dataclasses import dataclass

from agenttest.bootstrap.app import create_app
from agenttest.bootstrap.settings import Settings
from agenttest.modules.identity.api.router import AuthApiDependencies
from agenttest.modules.identity.application.commands.login import (
    InvalidCredentialsError,
    LoginResult,
)
from agenttest.modules.identity.application.queries.current_user import InvalidSessionError
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email, SystemRole, UserId
from fastapi.testclient import TestClient


def create_user() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("user@example.com"),
        display_name="User",
        role=SystemRole.DEVELOPER,
    )


@dataclass
class StubLogin:
    result: LoginResult | None = None

    async def execute(self, _command: object) -> LoginResult:
        if self.result is None:
            raise InvalidCredentialsError
        return self.result


@dataclass
class StubCurrentUser:
    user: User | None = None

    async def execute(self, _session_token: str) -> User:
        if self.user is None:
            raise InvalidSessionError
        return self.user


class StubLogout:
    def __init__(self) -> None:
        self.revoked_token: str | None = None

    async def execute(self, session_token: str) -> None:
        self.revoked_token = session_token


@dataclass
class StubCsrfValidator:
    valid: bool = True

    async def execute(self, _session_token: str, _csrf_token: str) -> None:
        if not self.valid:
            raise InvalidSessionError


class StubUpdateProfile:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def execute(self, user: User, display_name: str, email: Email) -> User:
        self.calls.append((display_name, email.value))
        user.update_profile(email=email, display_name=display_name, role=user.role)
        return user


class StubChangePassword:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def execute(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        del user
        self.calls.append((current_password, new_password))


def auth_dependencies(
    *,
    login: StubLogin | None = None,
    current_user: StubCurrentUser | None = None,
    logout: StubLogout | None = None,
    csrf: StubCsrfValidator | None = None,
    update_profile: StubUpdateProfile | None = None,
    change_password: StubChangePassword | None = None,
) -> AuthApiDependencies:
    return AuthApiDependencies(
        login=login or StubLogin(),
        current_user=current_user or StubCurrentUser(),
        logout=logout or StubLogout(),
        csrf=csrf or StubCsrfValidator(),
        update_profile=update_profile or StubUpdateProfile(),
        change_password=change_password or StubChangePassword(),
    )


def test_login_sets_secure_session_and_csrf_cookies() -> None:
    user = create_user()
    client = TestClient(
        create_app(
            settings=Settings(
                environment="production",
                internal_api_token="test-production-internal-token",
                session_cookie_secure=True,
            ),
            auth_dependencies=auth_dependencies(
                login=StubLogin(
                    LoginResult(
                        user=user,
                        session_token="session-token",
                        csrf_token="csrf-token",
                    )
                )
            ),
        ),
        base_url="https://testserver",
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "USER@EXAMPLE.COM", "password": "password"},
    )

    assert response.status_code == 200
    set_cookies = response.headers.get_list("set-cookie")
    assert any(
        "agenttest_session=session-token" in cookie
        and "HttpOnly" in cookie
        and "Secure" in cookie
        and "SameSite=lax" in cookie
        for cookie in set_cookies
    )
    assert any(
        "agenttest_csrf=csrf-token" in cookie
        and "HttpOnly" not in cookie
        and "Secure" in cookie
        and "SameSite=lax" in cookie
        for cookie in set_cookies
    )


def test_invalid_login_uses_problem_details_without_account_disclosure() -> None:
    client = TestClient(
        create_app(auth_dependencies=auth_dependencies()),
        base_url="https://testserver",
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["detail"] == "Invalid email or password"


def test_me_requires_a_valid_session() -> None:
    client = TestClient(
        create_app(auth_dependencies=auth_dependencies()),
        base_url="https://testserver",
    )

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["title"] == "Authentication required"


def test_logout_requires_csrf_and_clears_cookies() -> None:
    logout = StubLogout()
    client = TestClient(
        create_app(
            auth_dependencies=auth_dependencies(
                logout=logout,
                csrf=StubCsrfValidator(valid=True),
            )
        ),
        base_url="https://testserver",
    )
    client.cookies.set("agenttest_session", "session-token")
    client.cookies.set("agenttest_csrf", "csrf-token")

    missing_csrf = client.post("/api/v1/auth/logout")
    response = client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": "csrf-token"},
    )

    assert missing_csrf.status_code == 403
    assert response.status_code == 204
    assert logout.revoked_token == "session-token"
    set_cookies = response.headers.get_list("set-cookie")
    assert sum("Max-Age=0" in cookie for cookie in set_cookies) == 2


def test_profile_update_requires_csrf_and_returns_updated_user() -> None:
    user = create_user()
    updater = StubUpdateProfile()
    client = TestClient(
        create_app(
            auth_dependencies=auth_dependencies(
                current_user=StubCurrentUser(user),
                update_profile=updater,
            )
        ),
        base_url="https://testserver",
    )
    client.cookies.set("agenttest_session", "session-token")
    client.cookies.set("agenttest_csrf", "csrf-token")
    payload = {"display_name": "Updated User", "email": "updated@example.com"}

    missing_csrf = client.patch("/api/v1/auth/me", json=payload)
    response = client.patch(
        "/api/v1/auth/me",
        json=payload,
        headers={"X-CSRF-Token": "csrf-token"},
    )

    assert missing_csrf.status_code == 403
    assert response.status_code == 200
    assert response.json()["display_name"] == "Updated User"
    assert updater.calls == [("Updated User", "updated@example.com")]


def test_change_password_requires_csrf() -> None:
    user = create_user()
    changer = StubChangePassword()
    client = TestClient(
        create_app(
            auth_dependencies=auth_dependencies(
                current_user=StubCurrentUser(user),
                change_password=changer,
            )
        ),
        base_url="https://testserver",
    )
    client.cookies.set("agenttest_session", "session-token")
    client.cookies.set("agenttest_csrf", "csrf-token")
    payload = {"current_password": "current-password", "new_password": "new-password"}

    missing_csrf = client.post("/api/v1/auth/change-password", json=payload)
    response = client.post(
        "/api/v1/auth/change-password",
        json=payload,
        headers={"X-CSRF-Token": "csrf-token"},
    )

    assert missing_csrf.status_code == 403
    assert response.status_code == 204
    assert changer.calls == [("current-password", "new-password")]
