"""Stable public types exposed by the identity module."""

from agenttest.modules.identity.application.queries.current_user import InvalidSessionError
from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import (
    Email,
    SystemRole,
    UserId,
    UserStatus,
)

__all__ = [
    "Email",
    "InvalidSessionError",
    "SystemRole",
    "User",
    "UserId",
    "UserStatus",
]
