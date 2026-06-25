from dataclasses import dataclass

from agenttest.modules.identity.domain.errors import DisabledUserError
from agenttest.modules.identity.domain.value_objects import (
    Email,
    SystemRole,
    UserId,
    UserStatus,
)


@dataclass(slots=True)
class User:
    user_id: UserId
    email: Email
    display_name: str
    role: SystemRole
    status: UserStatus
    must_change_password: bool

    @classmethod
    def create(
        cls,
        *,
        user_id: UserId,
        email: Email,
        display_name: str,
        role: SystemRole,
    ) -> "User":
        normalized_name = display_name.strip()
        if not normalized_name:
            raise ValueError("Display name is required")
        return cls(
            user_id=user_id,
            email=email,
            display_name=normalized_name,
            role=role,
            status=UserStatus.ACTIVE,
            must_change_password=False,
        )

    @property
    def can_authenticate(self) -> bool:
        return self.status is UserStatus.ACTIVE

    def ensure_can_authenticate(self) -> None:
        if not self.can_authenticate:
            raise DisabledUserError

    def disable(self) -> None:
        self.status = UserStatus.DISABLED

    def enable(self) -> None:
        self.status = UserStatus.ACTIVE

    def require_password_change(self) -> None:
        self.must_change_password = True
