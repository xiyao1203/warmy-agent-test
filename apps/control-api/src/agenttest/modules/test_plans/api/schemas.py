"""Test plans HTTP API request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from agenttest.modules.test_plans.domain.entities import TestPlan, TestPlanVersion
from agenttest.modules.test_plans.domain.value_objects import (
    TestPlanConfig,
    VersionStatus,
)


class CreateTestPlanRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class UpdateTestPlanRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class TestPlanConfigRequest(BaseModel):
    api_browser_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    runs_per_case: int = Field(default=1, ge=1)
    concurrency: int = Field(default=1, ge=1)
    timeout: int = Field(default=300, gt=0)
    max_retries: int = Field(default=0, ge=0)
    retry_policy: dict[str, object] = Field(default_factory=dict)
    scorers: list[dict[str, object]] = Field(default_factory=list)
    pass_threshold: float = Field(default=1.0, ge=0.0, le=1.0)
    cost_budget: float | None = Field(default=None, ge=0.0)
    baseline_run_id: str | None = None
    release_gate: dict[str, object] = Field(default_factory=dict)

    def to_domain(self) -> TestPlanConfig:
        return TestPlanConfig(**self.model_dump())


class CreateTestPlanVersionRequest(BaseModel):
    config: TestPlanConfigRequest
    agent_version_id: UUID | None = None
    dataset_version_id: UUID | None = None
    environment_template_id: UUID | None = None


class UpdateTestPlanVersionRequest(BaseModel):
    config: TestPlanConfigRequest | None = None
    agent_version_id: UUID | None = None
    dataset_version_id: UUID | None = None
    environment_template_id: UUID | None = None


class TestPlanResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str | None
    created_by: UUID
    updated_by: UUID
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, plan: TestPlan) -> "TestPlanResponse":
        return cls(
            id=plan.test_plan_id.value,
            project_id=plan.project_id.value,
            name=plan.name,
            description=plan.description,
            created_by=plan.created_by.value,
            updated_by=plan.updated_by.value,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )


class TestPlanListResponse(BaseModel):
    items: list[TestPlanResponse]
    next_cursor: str | None = None


class TestPlanVersionResponse(BaseModel):
    id: UUID
    test_plan_id: UUID
    version_number: int
    status: VersionStatus
    config: dict[str, object]
    agent_version_id: UUID | None
    dataset_version_id: UUID | None
    environment_template_id: UUID | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None

    @classmethod
    def from_domain(cls, version: TestPlanVersion) -> "TestPlanVersionResponse":
        return cls(
            id=version.version_id.value,
            test_plan_id=version.test_plan_id.value,
            version_number=version.version_number,
            status=version.status,
            config=version.config.to_dict(),
            agent_version_id=(version.agent_version_id.value if version.agent_version_id else None),
            dataset_version_id=(
                version.dataset_version_id.value if version.dataset_version_id else None
            ),
            environment_template_id=(
                version.environment_template_id.value if version.environment_template_id else None
            ),
            created_by=version.created_by.value,
            created_at=version.created_at,
            updated_at=version.updated_at,
            published_at=version.published_at,
        )


class TestPlanVersionListResponse(BaseModel):
    items: list[TestPlanVersionResponse]
