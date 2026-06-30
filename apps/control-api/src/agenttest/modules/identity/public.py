"""Stable public types exposed by the identity module."""

from agenttest.modules.identity.api.router import (
    CsrfExecutor,
    authentication_required,
    problem_response,
    validate_csrf,
)
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
    "CsrfExecutor",
    "InvalidSessionError",
    "SystemRole",
    "User",
    "UserId",
    "UserStatus",
    "authentication_required",
    "problem_response",
    "validate_csrf",
]
