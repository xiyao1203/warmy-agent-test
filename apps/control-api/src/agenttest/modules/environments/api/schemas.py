"""Environment template HTTP API request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from agenttest.modules.environments.api.credential_mask import mask_credentials
from agenttest.modules.environments.domain.entities import EnvironmentTemplate
from agenttest.modules.environments.domain.value_objects import TemplateType
from agenttest.shared.application.core_summaries import EnvironmentSummaryMetrics


class CreateEnvironmentTemplateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    template_type: TemplateType
    config: dict[str, object] = Field(default_factory=dict)
    description: str | None = None


class UpdateEnvironmentTemplateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    config: dict[str, object] | None = None
    description: str | None = None


class EnvironmentTemplateResponse(EnvironmentSummaryMetrics):
    id: UUID
    project_id: UUID
    name: str
    template_type: TemplateType
    config: dict[str, object]
    description: str | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(
        cls,
        template: EnvironmentTemplate,
        summary: EnvironmentSummaryMetrics | None = None,
    ) -> "EnvironmentTemplateResponse":
        return cls(
            id=template.template_id.value,
            project_id=template.project_id.value,
            name=template.name,
            template_type=template.template_type,
            config=mask_credentials(template.config),
            description=template.description,
            created_by=template.created_by.value,
            created_at=template.created_at,
            updated_at=template.updated_at,
            **(summary.model_dump() if summary else {}),
        )


class EnvironmentTemplateListResponse(BaseModel):
    items: list[EnvironmentTemplateResponse]
    next_cursor: str | None = None


# ── Environment Version schemas ──────────────────────────────────────────


class CreateEnvironmentVersionRequest(BaseModel):
    """Request body for creating a new environment version."""

    config: dict[str, object] = Field(default_factory=dict)


class UpdateEnvironmentVersionRequest(BaseModel):
    """Request body for updating a draft environment version."""

    config: dict[str, object] | None = None


class EnvironmentVersionResponse(BaseModel):
    """Public response for an environment version (never includes secrets)."""

    id: UUID
    project_id: UUID
    environment_template_id: UUID
    version_number: int
    status: str
    config: dict[str, object]
    published_at: datetime | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class EnvironmentVersionListResponse(BaseModel):
    items: list[EnvironmentVersionResponse]
    next_cursor: str | None = None
