import re
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
    key: str = ""
    description: str | None = None
    lead_user_id: UserId | None = None
    updated_by: UserId | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    archived_at: datetime | None = None
    _members: dict[UserId, ProjectMemberRole] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        project_id: ProjectId,
        name: str,
        created_by: UserId,
        key: str | None = None,
        description: str | None = None,
        lead_user_id: UserId | None = None,
    ) -> "Project":
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Project name is required")
        normalized_key = (key or f"P{project_id.value.hex[:8]}").strip().upper()
        if not re.fullmatch(r"[A-Z][A-Z0-9-]{1,11}", normalized_key):
            raise ValueError("Project key must be 2-12 uppercase letters, numbers or hyphens")
        now = datetime.now(UTC)
        project = cls(
            project_id=project_id,
            name=normalized_name,
            created_by=created_by,
            key=normalized_key,
            description=description.strip() if description and description.strip() else None,
            lead_user_id=lead_user_id,
            updated_by=created_by,
            created_at=now,
            updated_at=now,
        )
        project.add_member(created_by, ProjectMemberRole.DEVELOPER)
        if lead_user_id is not None:
            project.add_member(lead_user_id, ProjectMemberRole.DEVELOPER)
        return project

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None

    def rename(self, name: str) -> None:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Project name is required")
        self.name = normalized_name
        self.updated_at = datetime.now(UTC)

    def update_details(
        self,
        *,
        description: str | None = None,
        lead_user_id: UserId | None = None,
    ) -> None:
        if lead_user_id is not None and lead_user_id not in self._members:
            raise ValueError("Project lead must be a current member")
        self.description = description.strip() if description and description.strip() else None
        self.lead_user_id = lead_user_id
        self.updated_at = datetime.now(UTC)

    def archive(self, archived_at: datetime | None = None) -> None:
        if self.archived_at is None:
            self.archived_at = archived_at or datetime.now(UTC)
            self.updated_at = self.archived_at

    def add_member(self, user_id: UserId, role: ProjectMemberRole) -> None:
        self._members[user_id] = role

    def change_member_role(self, user_id: UserId, role: ProjectMemberRole) -> None:
        if user_id not in self._members:
            raise KeyError("Project member not found")
        self._members[user_id] = role

    def remove_member(self, user_id: UserId) -> None:
        if user_id == self.lead_user_id:
            raise ValueError("Cannot remove the active project lead")
        self._members.pop(user_id, None)

    def member_role(self, user_id: UserId) -> ProjectMemberRole | None:
        return self._members.get(user_id)

    def members(self) -> dict[UserId, ProjectMemberRole]:
        return dict(self._members)
