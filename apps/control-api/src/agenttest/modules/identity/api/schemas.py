from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from agenttest.modules.identity.domain.entities import User
from agenttest.modules.identity.domain.value_objects import SystemRole, UserStatus


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class UserResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
    role: SystemRole
    status: UserStatus
    must_change_password: bool

    @classmethod
    def from_domain(cls, user: User) -> "UserResponse":
        return cls(
            id=user.user_id.value,
            email=user.email.value,
            display_name=user.display_name,
            role=user.role,
            status=user.status,
            must_change_password=user.must_change_password,
        )
