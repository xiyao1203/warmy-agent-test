from uuid import uuid4

import pytest
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.errors import DisabledUserError
from agenttest.modules.identity.domain.value_objects import (
    Email,
    SystemRole,
    UserId,
    UserStatus,
)


def create_user(*, role: SystemRole = SystemRole.DEVELOPER) -> User:
    return User.create(
        user_id=UserId(uuid4()),
        email=Email("USER@EXAMPLE.COM"),
        display_name="Test User",
        role=role,
    )


def test_email_is_normalized_to_lowercase() -> None:
    user = create_user()

    assert user.email.value == "user@example.com"


@pytest.mark.parametrize(
    "role",
    [
        SystemRole.SUPER_ADMIN,
        SystemRole.DEVELOPER,
        SystemRole.TESTER,
        SystemRole.REVIEWER,
        SystemRole.VIEWER,
    ],
)
def test_supported_system_roles_can_be_assigned(role: SystemRole) -> None:
    user = create_user(role=role)

    assert user.role is role


def test_disabling_user_revokes_authentication() -> None:
    user = create_user()

    user.disable()

    assert user.status is UserStatus.DISABLED
    assert user.can_authenticate is False
    with pytest.raises(DisabledUserError):
        user.ensure_can_authenticate()


def test_user_can_require_password_change() -> None:
    user = create_user()

    user.require_password_change()

    assert user.must_change_password is True


def test_disabling_an_already_disabled_user_is_idempotent() -> None:
    user = create_user()

    user.disable()
    user.disable()

    assert user.status is UserStatus.DISABLED
