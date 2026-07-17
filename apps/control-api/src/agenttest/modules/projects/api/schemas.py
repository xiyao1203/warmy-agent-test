from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from agenttest.modules.projects.domain.entities import Project, ProjectMemberRole
from agenttest.shared.application.core_summaries import ProjectSummaryMetrics


class CreateProjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    key: str | None = Field(default=None, min_length=2, max_length=12)
    description: str | None = Field(default=None, max_length=2000)
    lead_user_id: UUID | None = None


class RenameProjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    lead_user_id: UUID | None = None


class ProjectMemberRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    role: ProjectMemberRole


class ProjectMemberUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: ProjectMemberRole


class ProjectMemberResponse(BaseModel):
    user_id: UUID
    role: ProjectMemberRole


class ProjectResponse(ProjectSummaryMetrics):
    id: UUID
    key: str
    name: str
    description: str | None
    lead_user_id: UUID | None
    status: Literal["active", "archived"]
    archived: bool
    created_by: UUID
    updated_by: UUID
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(
        cls,
        project: Project,
        summary: ProjectSummaryMetrics | None = None,
    ) -> "ProjectResponse":
        return cls(
            id=project.project_id.value,
            key=project.key,
            name=project.name,
            description=project.description,
            lead_user_id=project.lead_user_id.value if project.lead_user_id else None,
            status="archived" if project.is_archived else "active",
            archived=project.is_archived,
            created_by=project.created_by.value,
            updated_by=(project.updated_by or project.created_by).value,
            created_at=project.created_at,
            updated_at=project.updated_at,
            **(summary.model_dump() if summary else {}),
        )


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]


class ProjectMembersResponse(BaseModel):
    items: list[ProjectMemberResponse]
