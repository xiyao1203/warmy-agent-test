from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from agenttest.modules.projects.domain.entities import Project, ProjectMemberRole


class CreateProjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)


class RenameProjectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)


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


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    archived: bool

    @classmethod
    def from_domain(cls, project: Project) -> "ProjectResponse":
        return cls(
            id=project.project_id.value,
            name=project.name,
            archived=project.is_archived,
        )


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]


class ProjectMembersResponse(BaseModel):
    items: list[ProjectMemberResponse]
