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


class UserPageResponse(BaseModel):
    items: list[UserResponse]
    next_cursor: UUID | None


class CreateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    display_name: str = Field(min_length=1, max_length=200)
    role: SystemRole
    initial_password: str = Field(min_length=8, max_length=1024)


class UpdateUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    display_name: str = Field(min_length=1, max_length=200)
    role: SystemRole | None = None


class UpdateProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    display_name: str = Field(min_length=1, max_length=200)


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(min_length=1, max_length=1024)
    new_password: str = Field(min_length=8, max_length=1024)


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    new_password: str = Field(min_length=8, max_length=1024)
