from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from agenttest.modules.identity.public import UserId


@dataclass(frozen=True, slots=True)
class ProjectId:
    value: UUID

    @classmethod
    def new(cls) -> "ProjectId":
        return cls(uuid4())


class ProjectMemberRole(StrEnum):
    DEVELOPER = "developer"
    TESTER = "tester"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


@dataclass(slots=True)
class Project:
    project_id: ProjectId
    name: str
    created_by: UserId
    archived_at: datetime | None = None
    _members: dict[UserId, ProjectMemberRole] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        project_id: ProjectId,
        name: str,
        created_by: UserId,
    ) -> "Project":
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Project name is required")
        return cls(
            project_id=project_id,
            name=normalized_name,
            created_by=created_by,
        )

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None

    def rename(self, name: str) -> None:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Project name is required")
        self.name = normalized_name

    def archive(self, archived_at: datetime | None = None) -> None:
        if self.archived_at is None:
            self.archived_at = archived_at or datetime.now(UTC)

    def add_member(self, user_id: UserId, role: ProjectMemberRole) -> None:
        self._members[user_id] = role

    def change_member_role(self, user_id: UserId, role: ProjectMemberRole) -> None:
        if user_id not in self._members:
            raise KeyError("Project member not found")
        self._members[user_id] = role

    def remove_member(self, user_id: UserId) -> None:
        self._members.pop(user_id, None)

    def member_role(self, user_id: UserId) -> ProjectMemberRole | None:
        return self._members.get(user_id)

    def members(self) -> dict[UserId, ProjectMemberRole]:
        return dict(self._members)
