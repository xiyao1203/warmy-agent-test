from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from agenttest.bootstrap.app import create_app
from agenttest.modules.identity.api.admin_router import AdminApiDependencies
from agenttest.modules.identity.api.router import AuthApiDependencies
from agenttest.modules.identity.application.commands.create_user import CreateUserCommand
from agenttest.modules.identity.application.commands.reset_password import ResetPasswordCommand
from agenttest.modules.identity.application.commands.set_user_status import SetUserStatusCommand
from agenttest.modules.identity.application.commands.update_user import UpdateUserCommand
from agenttest.modules.identity.application.errors import PermissionDeniedError
from agenttest.modules.identity.application.queries.list_users import UserPage
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import Email, SystemRole, UserId
from agenttest.shared.application.pagination import PageRequest
from fastapi.testclient import TestClient


def create_user(role: SystemRole, email: str) -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email(email),
        display_name=email.split("@")[0],
        role=role,
    )


class StubCurrentUser:
    def __init__(self, user: User) -> None:
        self.user = user

    async def execute(self, _session_token: str) -> User:
        return self.user


class StubAuthOperation:
    async def execute(self, *_args: object) -> None:
        return None


def auth_dependencies(actor: User) -> AuthApiDependencies:
    operation = StubAuthOperation()
    return AuthApiDependencies(
        login=operation,
        current_user=StubCurrentUser(actor),
        logout=operation,
        csrf=operation,
    )


@dataclass
class StubListUsers:
    users: list[User]

    async def execute(self, actor: User, cursor: UUID | None, limit: int) -> UserPage:
        if actor.role is not SystemRole.SUPER_ADMIN:
            raise PermissionDeniedError
        return UserPage(
            items=self.users[:limit],
            next_cursor=None,
            total=len(self.users),
            page=None,
            page_size=limit,
        )

    async def execute_page(self, actor: User, page_request: PageRequest) -> UserPage:
        if actor.role is not SystemRole.SUPER_ADMIN:
            raise PermissionDeniedError
        start = page_request.offset
        return UserPage(
            items=self.users[start : start + page_request.page_size],
            next_cursor=None,
            total=len(self.users),
            page=page_request.page,
            page_size=page_request.page_size,
        )


class StubCreateUser:
    async def execute(self, actor: User, command: CreateUserCommand) -> User:
        if actor.role is not SystemRole.SUPER_ADMIN:
            raise PermissionDeniedError
        return create_user(command.role, command.email.value)


class StubGetUser:
    def __init__(self, user: User) -> None:
        self.user = user

    async def execute(self, actor: User, user_id: UserId) -> User:
        if actor.role is not SystemRole.SUPER_ADMIN:
            raise PermissionDeniedError
        return self.user


class StubUpdateUser:
    async def execute(self, actor: User, command: UpdateUserCommand) -> User:
        if actor.role is not SystemRole.SUPER_ADMIN:
            raise PermissionDeniedError
        return create_user(command.role or SystemRole.DEVELOPER, command.email.value)


class StubResetPassword:
    async def execute(self, actor: User, command: ResetPasswordCommand) -> None:
        if actor.role is not SystemRole.SUPER_ADMIN:
            raise PermissionDeniedError


class StubSetStatus:
    async def execute(self, actor: User, command: SetUserStatusCommand) -> User:
        if actor.role is not SystemRole.SUPER_ADMIN:
            raise PermissionDeniedError
        return create_user(SystemRole.DEVELOPER, "target@example.com")


class StubDeleteUser:
    async def execute(self, actor: User, user_id: UserId) -> None:
        if actor.role is not SystemRole.SUPER_ADMIN:
            raise PermissionDeniedError


def admin_dependencies(users: list[User]) -> AdminApiDependencies:
    return AdminApiDependencies(
        list_users=StubListUsers(users),
        get_user=StubGetUser(users[0]),
        create_user=StubCreateUser(),
        update_user=StubUpdateUser(),
        reset_password=StubResetPassword(),
        set_status=StubSetStatus(),
        delete_user=StubDeleteUser(),
    )


def client_for(actor: User, users: list[User]) -> TestClient:
    client = TestClient(
        create_app(
            auth_dependencies=auth_dependencies(actor),
            admin_dependencies=admin_dependencies(users),
        ),
        base_url="https://testserver",
    )
    client.cookies.set("agenttest_session", "session-token")
    client.cookies.set("agenttest_csrf", "csrf-token")
    return client


def test_super_admin_lists_users_without_sensitive_fields() -> None:
    actor = create_user(SystemRole.SUPER_ADMIN, "admin@example.com")
    target = create_user(SystemRole.DEVELOPER, "developer@example.com")

    response = client_for(actor, [target]).get("/api/v1/system/users?limit=25")

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["email"] == "developer@example.com"
    assert "password_hash" not in body["items"][0]
    assert "session" not in body["items"][0]
    assert body["next_cursor"] is None


def test_normal_user_cannot_access_user_management_api() -> None:
    actor = create_user(SystemRole.DEVELOPER, "developer@example.com")

    response = client_for(actor, [actor]).get("/api/v1/system/users")

    assert response.status_code == 403
    assert response.json()["title"] == "Permission denied"


def test_super_admin_can_create_update_and_manage_user_status() -> None:
    actor = create_user(SystemRole.SUPER_ADMIN, "admin@example.com")
    target = create_user(SystemRole.DEVELOPER, "target@example.com")
    client = client_for(actor, [target])
    headers = {"X-CSRF-Token": "csrf-token"}

    created = client.post(
        "/api/v1/system/users",
        headers=headers,
        json={
            "email": "new@example.com",
            "display_name": "New User",
            "role": "tester",
            "initial_password": "initial-password",
        },
    )
    updated = client.patch(
        f"/api/v1/system/users/{target.user_id.value}",
        headers=headers,
        json={
            "email": "updated@example.com",
            "display_name": "Updated",
            "role": "reviewer",
        },
    )
    reset = client.post(
        f"/api/v1/system/users/{target.user_id.value}/reset-password",
        headers=headers,
        json={"new_password": "new-password"},
    )
    disabled = client.post(
        f"/api/v1/system/users/{target.user_id.value}/disable",
        headers=headers,
    )
    enabled = client.post(
        f"/api/v1/system/users/{target.user_id.value}/enable",
        headers=headers,
    )
    deleted = client.delete(
        f"/api/v1/system/users/{target.user_id.value}",
        headers=headers,
    )

    assert created.status_code == 201
    assert updated.status_code == 200
    assert reset.status_code == 204
    assert disabled.status_code == 200
    assert enabled.status_code == 200
    assert deleted.status_code == 204


def test_user_list_supports_numbered_page_mode() -> None:
    actor = create_user(SystemRole.SUPER_ADMIN, "admin@example.com")
    users = [
        create_user(SystemRole.DEVELOPER, f"user-{index:02d}@example.com") for index in range(12)
    ]

    response = client_for(actor, users).get(
        "/api/v1/system/users",
        params={"page": 2, "page_size": 10},
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 2
    assert response.json() | {"items": []} == {
        "items": [],
        "next_cursor": None,
        "total": 12,
        "page": 2,
        "page_size": 10,
        "total_pages": 2,
    }
