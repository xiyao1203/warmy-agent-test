from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4


class SystemRole(StrEnum):
    SUPER_ADMIN = "super_admin"
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class UserStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class UserId:
    value: UUID

    @classmethod
    def new(cls) -> "UserId":
        return cls(uuid4())


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        if not normalized or "@" not in normalized:
            raise ValueError("A valid email address is required")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value
