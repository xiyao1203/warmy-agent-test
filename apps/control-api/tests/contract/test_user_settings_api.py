from __future__ import annotations

from dataclasses import dataclass

from agenttest.bootstrap.app import create_app
from agenttest.modules.identity.application.queries.current_user import InvalidSessionError
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email, SystemRole, UserId
from agenttest.modules.user_settings.api.router import UserSettingsApiDependencies
from agenttest.modules.user_settings.domain.entities import UserSettings
from agenttest.modules.user_settings.domain.value_objects import Language, Theme
from fastapi.testclient import TestClient


def create_user() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("user@example.com"),
        display_name="User",
        role=SystemRole.DEVELOPER,
    )


@dataclass
class StubCurrentUser:
    user: User | None

    async def execute(self, _session_token: str) -> User:
        if self.user is None:
            raise InvalidSessionError
        return self.user


@dataclass
class StubGetSettings:
    settings: UserSettings | None

    async def execute(self, _user_id: str) -> UserSettings | None:
        return self.settings


class StubUpdateSettings:
    def __init__(self, user: User) -> None:
        self.user = user
        self.calls = 0

    async def execute(
        self,
        user_id: str,
        *,
        theme: Theme | None = None,
        language: Language | None = None,
        email_notifications: bool | None = None,
        push_notifications: bool | None = None,
        test_complete_notifications: bool | None = None,
    ) -> UserSettings:
        self.calls += 1
        return UserSettings(
            user_id=self.user.user_id.value,
            theme=theme or Theme.SYSTEM,
            language=language or Language.ZH_CN,
            email_notifications=(
                True if email_notifications is None else email_notifications
            ),
            push_notifications=False if push_notifications is None else push_notifications,
            test_complete_notifications=(
                True
                if test_complete_notifications is None
                else test_complete_notifications
            ),
        )


class StubCsrf:
    async def execute(self, _session_token: str, _csrf_token: str) -> None:
        return None


def settings_client() -> tuple[TestClient, StubUpdateSettings]:
    user = create_user()
    updater = StubUpdateSettings(user)
    dependencies = UserSettingsApiDependencies(
        current_user=StubCurrentUser(user),
        get_settings=StubGetSettings(None),
        update_settings=updater,
        csrf=StubCsrf(),
    )
    client = TestClient(
        create_app(user_settings_dependencies=dependencies),
        base_url="https://testserver",
    )
    client.cookies.set("agenttest_session", "session-token")
    client.cookies.set("agenttest_csrf", "csrf-token")
    return client, updater


def test_settings_get_returns_defaults() -> None:
    client, _ = settings_client()

    response = client.get("/api/v1/users/me/settings")

    assert response.status_code == 200
    assert response.json() == {
        "theme": "system",
        "language": "zh-CN",
        "email_notifications": True,
        "push_notifications": False,
        "test_complete_notifications": True,
    }


def test_settings_update_requires_csrf_and_returns_persisted_values() -> None:
    client, updater = settings_client()
    payload = {
        "theme": "light",
        "language": "zh-CN",
        "email_notifications": False,
    }

    missing_csrf = client.patch("/api/v1/users/me/settings", json=payload)
    response = client.patch(
        "/api/v1/users/me/settings",
        json=payload,
        headers={"X-CSRF-Token": "csrf-token"},
    )

    assert missing_csrf.status_code == 403
    assert response.status_code == 200
    assert response.json()["email_notifications"] is False
    assert updater.calls == 1
