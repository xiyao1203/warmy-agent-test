"""Agents HTTP API request and response schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from agenttest.modules.agents.domain.entities import Agent, AgentVersion
from agenttest.modules.agents.domain.invocation import InvocationProtocol
from agenttest.modules.agents.domain.value_objects import (
    AgentConfig,
    AgentType,
    VersionStatus,
)
from agenttest.shared.application.core_summaries import AgentSummaryMetrics


def _default_request_template() -> dict[str, object]:
    return {"input": "{{ input }}"}


class CreateAgentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    agent_type: AgentType
    description: str | None = None


class UpdateAgentRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class AgentConfigRequest(BaseModel):
    api_url: str
    code_version: str | None = None
    git_commit: str | None = None
    model: str | None = None
    model_params: dict[str, str | int | float | bool] = Field(default_factory=dict)
    system_prompt: str | None = None
    tools: list[dict[str, Any]] = Field(default_factory=list)
    timeout: int = 30
    protocol: InvocationProtocol = InvocationProtocol.SYNC_JSON
    request_template: dict[str, object] = Field(default_factory=_default_request_template)
    response_path: str = Field(default="output", min_length=1)
    credential_binding_ids: list[UUID] = Field(default_factory=list)
    max_steps: int | None = None
    cost_limit: float | None = None
    system_prompt_version: str | None = None
    knowledge_version: str | None = None
    adapter_version: str | None = None
    web_url: str | None = None
    adapter_id: str | None = None
    plugin_id: str | None = None
    plugin_version: str | None = None
    target_config: dict[str, Any] = Field(default_factory=dict)

    def to_domain(self) -> AgentConfig:
        return AgentConfig(**self.model_dump())


class CreateAgentVersionRequest(BaseModel):
    config: AgentConfigRequest


class UpdateAgentVersionRequest(BaseModel):
    config: AgentConfigRequest


class AgentResponse(AgentSummaryMetrics):
    id: UUID
    project_id: UUID
    name: str
    description: str | None
    agent_type: AgentType
    created_by: UUID
    updated_by: UUID
    created_at: datetime
    updated_at: datetime
    current_version_id: UUID | None = None
    baseline_version_id: UUID | None = None

    @classmethod
    def from_domain(
        cls,
        agent: Agent,
        summary: AgentSummaryMetrics | None = None,
    ) -> "AgentResponse":
        return cls(
            id=agent.agent_id.value,
            project_id=agent.project_id.value,
            name=agent.name,
            description=agent.description,
            agent_type=agent.agent_type,
            created_by=agent.created_by.value,
            updated_by=agent.updated_by.value,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
            current_version_id=agent.current_version_id.value if agent.current_version_id else None,
            baseline_version_id=(
                agent.baseline_version_id.value if agent.baseline_version_id else None
            ),
            **(summary.model_dump() if summary else {}),
        )


class AgentListResponse(BaseModel):
    items: list[AgentResponse]
    next_cursor: str | None = None
    total: int
    page: int | None
    page_size: int
    total_pages: int


class AgentVersionResponse(BaseModel):
    id: UUID
    agent_id: UUID
    version_number: int
    status: VersionStatus
    config: dict[str, Any]
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None

    @classmethod
    def from_domain(cls, version: AgentVersion) -> "AgentVersionResponse":
        return cls(
            id=version.version_id.value,
            agent_id=version.agent_id.value,
            version_number=version.version_number,
            status=version.status,
            config=version.config.to_dict(),
            created_by=version.created_by.value,
            created_at=version.created_at,
            updated_at=version.updated_at,
            published_at=version.published_at,
        )


class AgentVersionListResponse(BaseModel):
    items: list[AgentVersionResponse]
