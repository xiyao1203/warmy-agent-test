from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from agenttest.modules.identity.domain.errors import DisabledUserError
from agenttest.modules.identity.domain.value_objects import (
    Email,
    SystemRole,
    UserId,
    UserStatus,
)

MAX_FAILED_LOGINS = 5
LOCKOUT_DURATION = timedelta(minutes=15)


@dataclass(slots=True)
class User:
    user_id: UserId
    email: Email
    display_name: str
    role: SystemRole
    status: UserStatus
    must_change_password: bool
    failed_login_count: int = 0
    locked_until: datetime | None = None

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
        if self.status is not UserStatus.ACTIVE:
            return False
        if self.locked_until and datetime.now(UTC) < self.locked_until:
            return False
        return True

    def ensure_can_authenticate(self) -> None:
        if not self.can_authenticate:
            raise DisabledUserError

    def record_failed_login(self) -> None:
        """记录登录失败，达到阈值后锁定账号。"""
        self.failed_login_count += 1
        if self.failed_login_count >= MAX_FAILED_LOGINS:
            self.locked_until = datetime.now(UTC) + LOCKOUT_DURATION

    def reset_failed_logins(self) -> None:
        """登录成功后重置失败计数。"""
        self.failed_login_count = 0
        self.locked_until = None

    def disable(self) -> None:
        self.status = UserStatus.DISABLED

    def enable(self) -> None:
        self.status = UserStatus.ACTIVE

    def require_password_change(self) -> None:
        self.must_change_password = True

    def update_profile(
        self,
        *,
        email: Email,
        display_name: str,
        role: SystemRole,
    ) -> None:
        normalized_name = display_name.strip()
        if not normalized_name:
            raise ValueError("Display name is required")
        self.email = email
        self.display_name = normalized_name
        self.role = role
