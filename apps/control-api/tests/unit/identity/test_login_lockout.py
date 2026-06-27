"""Unit tests for login lockout behavior."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from agenttest.modules.identity.domain.entities import (
    LOCKOUT_DURATION,
    MAX_FAILED_LOGINS,
    User,
)
from agenttest.modules.identity.domain.value_objects import (
    Email,
    SystemRole,
    UserId,
)


def _make_user() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("test@example.com"),
        display_name="Test",
        role=SystemRole.DEVELOPER,
    )


def test_user_starts_unlocked() -> None:
    user = _make_user()
    assert user.failed_login_count == 0
    assert user.locked_until is None
    assert user.can_authenticate is True


def test_failed_login_increments_count() -> None:
    user = _make_user()
    user.record_failed_login()
    assert user.failed_login_count == 1
    assert user.locked_until is None
    assert user.can_authenticate is True


def test_lockout_after_max_failures() -> None:
    user = _make_user()
    for _ in range(MAX_FAILED_LOGINS):
        user.record_failed_login()
    assert user.failed_login_count == MAX_FAILED_LOGINS
    assert user.locked_until is not None
    assert user.can_authenticate is False


def test_lockout_duration_is_15_minutes() -> None:
    user = _make_user()
    before = datetime.now(UTC)
    for _ in range(MAX_FAILED_LOGINS):
        user.record_failed_login()
    after = datetime.now(UTC)
    assert user.locked_until is not None
    assert user.locked_until >= before + LOCKOUT_DURATION
    assert user.locked_until <= after + LOCKOUT_DURATION


def test_reset_clears_lockout() -> None:
    user = _make_user()
    for _ in range(MAX_FAILED_LOGINS):
        user.record_failed_login()
    assert user.can_authenticate is False
    user.reset_failed_logins()
    assert user.failed_login_count == 0
    assert user.locked_until is None
    assert user.can_authenticate is True


def test_locked_user_cannot_authenticate() -> None:
    user = _make_user()
    for _ in range(MAX_FAILED_LOGINS):
        user.record_failed_login()
    with pytest.raises(Exception):
        user.ensure_can_authenticate()
