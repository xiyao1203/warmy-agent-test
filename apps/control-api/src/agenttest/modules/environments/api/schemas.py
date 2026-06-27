"""Environment template HTTP API request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from agenttest.modules.environments.api.credential_mask import mask_credentials
from agenttest.modules.environments.domain.entities import EnvironmentTemplate
from agenttest.modules.environments.domain.value_objects import TemplateType


class CreateEnvironmentTemplateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    template_type: TemplateType
    config: dict[str, object] = Field(default_factory=dict)
    description: str | None = None


class UpdateEnvironmentTemplateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    config: dict[str, object] | None = None
    description: str | None = None


class EnvironmentTemplateResponse(BaseModel):
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
        )


class EnvironmentTemplateListResponse(BaseModel):
    items: list[EnvironmentTemplateResponse]
    next_cursor: str | None = None
