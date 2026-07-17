"""Datasets HTTP API request and response schemas."""

import json
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from agenttest.modules.datasets.application.contracts import (
    MAX_CUSTOM_FIELDS_BYTES,
    ArtifactRequirementV1,
    DataBindingV1,
    PlatformTestCaseV1,
    TestStepV1,
)
from agenttest.modules.datasets.domain.entities import (
    Dataset,
    DatasetVersion,
    TestCase,
)
from agenttest.modules.datasets.domain.value_objects import (
    AutomationStatus,
    ExecutionMode,
    Priority,
    RiskLevel,
    TestCaseSource,
    TestCaseStatus,
    TestCaseTemplate,
    TestCaseType,
    TestGroup,
    VersionStatus,
)
from agenttest.shared.application.core_summaries import DatasetSummaryMetrics


class CreateDatasetRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class UpdateDatasetRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class TestCaseFields(BaseModel):
    name: str = Field(min_length=1, max_length=500)
    objective: str | None = Field(default=None, min_length=1, max_length=4000)
    template: TestCaseTemplate = TestCaseTemplate.AI_EVAL
    case_type: TestCaseType = TestCaseType.FUNCTIONAL
    automation_status: AutomationStatus = AutomationStatus.CANDIDATE
    source_ref: str | None = Field(default=None, max_length=500)
    component: str | None = Field(default=None, max_length=200)
    requirement_refs: list[str] = Field(default_factory=list, max_length=50)
    owner_id: UUID | None = None
    preconditions: list[str] = Field(default_factory=list, max_length=100)
    input: dict[str, object]
    data_bindings: list[DataBindingV1] = Field(default_factory=list, max_length=100)
    steps: list[TestStepV1] = Field(default_factory=list, max_length=200)
    execution_mode: ExecutionMode
    assertions: list[dict[str, object]] = Field(default_factory=list)
    scorers: list[dict[str, object]] = Field(default_factory=list)
    initial_state: dict[str, object] | None = None
    expected_outcome: dict[str, object] | None = None
    security_policies: list[dict[str, object]] = Field(default_factory=list)
    artifact_requirements: list[ArtifactRequirementV1] = Field(
        default_factory=list,
        max_length=20,
    )
    postconditions: list[str] = Field(default_factory=list, max_length=100)
    estimated_duration_seconds: int | None = Field(default=None, ge=1, le=86_400)
    timeout_seconds: int | None = Field(default=None, ge=1, le=86_400)
    retry_count: int = Field(default=0, ge=0, le=10)
    custom_fields: dict[str, object] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    scenario: str | None = None
    priority: Priority | None = None
    risk_level: RiskLevel | None = None
    difficulty: str | None = None
    test_group: TestGroup | None = None

    @model_validator(mode="after")
    def validate_platform_contract(self) -> "TestCaseFields":
        payload = self.model_dump()
        payload["objective"] = self.objective or self.name
        PlatformTestCaseV1.model_validate(payload)
        return self


class CreateTestCaseRequest(TestCaseFields):
    pass


class UpdateTestCaseRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=500)
    objective: str | None = Field(default=None, min_length=1, max_length=4000)
    template: TestCaseTemplate | None = None
    case_type: TestCaseType | None = None
    automation_status: AutomationStatus | None = None
    source_ref: str | None = Field(default=None, max_length=500)
    component: str | None = Field(default=None, max_length=200)
    requirement_refs: list[str] | None = Field(default=None, max_length=50)
    owner_id: UUID | None = None
    preconditions: list[str] | None = Field(default=None, max_length=100)
    input: dict[str, object] | None = None
    data_bindings: list[DataBindingV1] | None = Field(default=None, max_length=100)
    steps: list[TestStepV1] | None = Field(default=None, max_length=200)
    execution_mode: ExecutionMode | None = None
    assertions: list[dict[str, object]] | None = None
    scorers: list[dict[str, object]] | None = None
    initial_state: dict[str, object] | None = None
    expected_outcome: dict[str, object] | None = None
    security_policies: list[dict[str, object]] | None = None
    artifact_requirements: list[ArtifactRequirementV1] | None = Field(
        default=None,
        max_length=20,
    )
    postconditions: list[str] | None = Field(default=None, max_length=100)
    estimated_duration_seconds: int | None = Field(default=None, ge=1, le=86_400)
    timeout_seconds: int | None = Field(default=None, ge=1, le=86_400)
    retry_count: int | None = Field(default=None, ge=0, le=10)
    custom_fields: dict[str, object] | None = None
    tags: list[str] | None = None
    scenario: str | None = None
    priority: Priority | None = None
    risk_level: RiskLevel | None = None
    difficulty: str | None = None
    test_group: TestGroup | None = None
    sort_order: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_custom_field_size(self) -> "UpdateTestCaseRequest":
        if self.custom_fields is not None:
            encoded = json.dumps(
                self.custom_fields,
                ensure_ascii=False,
                separators=(",", ":"),
                default=str,
            ).encode()
            if len(encoded) > MAX_CUSTOM_FIELDS_BYTES:
                raise ValueError("custom_fields must not exceed 16 KiB")
        return self


class ImportTestCasesRequest(BaseModel):
    format: Literal["json", "jsonl", "csv"]
    content: str


class ImportTestCasesResponse(BaseModel):
    imported_count: int
    items: list["TestCaseResponse"]


class ImportPreviewError(BaseModel):
    line: int
    field: str
    code: str
    message: str


class ImportPreviewResponse(BaseModel):
    valid_count: int
    errors: list[ImportPreviewError]
    preview: list[dict[str, object]]


class ExportTestCasesResponse(BaseModel):
    format: Literal["json", "jsonl", "csv"]
    content: str


class DatasetResponse(DatasetSummaryMetrics):
    id: UUID
    project_id: UUID
    name: str
    description: str | None
    created_by: UUID
    updated_by: UUID
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(
        cls,
        dataset: Dataset,
        summary: DatasetSummaryMetrics | None = None,
    ) -> "DatasetResponse":
        return cls(
            id=dataset.dataset_id.value,
            project_id=dataset.project_id.value,
            name=dataset.name,
            description=dataset.description,
            created_by=dataset.created_by.value,
            updated_by=dataset.updated_by.value,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
            **(summary.model_dump() if summary else {}),
        )


class DatasetListResponse(BaseModel):
    items: list[DatasetResponse]
    next_cursor: str | None = None


class DatasetVersionResponse(BaseModel):
    id: UUID
    dataset_id: UUID
    version_number: int
    status: VersionStatus
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None

    @classmethod
    def from_domain(cls, version: DatasetVersion) -> "DatasetVersionResponse":
        return cls(
            id=version.version_id.value,
            dataset_id=version.dataset_id.value,
            version_number=version.version_number,
            status=version.status,
            created_by=version.created_by.value,
            created_at=version.created_at,
            updated_at=version.updated_at,
            published_at=version.published_at,
        )


class DatasetVersionListResponse(BaseModel):
    items: list[DatasetVersionResponse]


class TestCaseResponse(BaseModel):
    id: UUID
    dataset_version_id: UUID
    case_key: str | None
    name: str
    objective: str
    case_status: TestCaseStatus
    template: TestCaseTemplate
    case_type: TestCaseType
    automation_status: AutomationStatus
    source: TestCaseSource
    source_ref: str | None
    component: str | None
    requirement_refs: list[str]
    owner_id: UUID | None
    preconditions: list[str]
    input: dict[str, object]
    data_bindings: list[dict[str, object]]
    steps: list[TestStepV1]
    execution_mode: ExecutionMode
    assertions: list[dict[str, object]]
    scorers: list[dict[str, object]]
    initial_state: dict[str, object] | None
    expected_outcome: dict[str, object] | None
    security_policies: list[dict[str, object]]
    artifact_requirements: list[dict[str, object]]
    postconditions: list[str]
    estimated_duration_seconds: int | None
    timeout_seconds: int | None
    retry_count: int
    custom_fields: dict[str, object]
    tags: list[str]
    scenario: str | None
    priority: Priority | None
    risk_level: RiskLevel | None
    difficulty: str | None
    test_group: TestGroup | None
    sort_order: int
    created_by: UUID | None
    updated_by: UUID | None
    created_at: datetime | None
    updated_at: datetime | None

    @classmethod
    def from_domain(cls, case: TestCase) -> "TestCaseResponse":
        return cls(
            id=case.case_id.value,
            dataset_version_id=case.dataset_version_id.value,
            case_key=case.case_key,
            name=case.name,
            objective=case.objective or case.name,
            case_status=case.case_status,
            template=case.template,
            case_type=case.case_type,
            automation_status=case.automation_status,
            source=case.source,
            source_ref=case.source_ref,
            component=case.component,
            requirement_refs=case.requirement_refs,
            owner_id=case.owner_id.value if case.owner_id else None,
            preconditions=case.preconditions,
            input=case.input,
            data_bindings=case.data_bindings,
            steps=[TestStepV1.model_validate(step) for step in case.steps],
            execution_mode=case.execution_mode,
            assertions=case.assertions,
            scorers=case.scorers,
            initial_state=case.initial_state,
            expected_outcome=case.expected_outcome,
            security_policies=case.security_policies,
            artifact_requirements=case.artifact_requirements,
            postconditions=case.postconditions,
            estimated_duration_seconds=case.estimated_duration_seconds,
            timeout_seconds=case.timeout_seconds,
            retry_count=case.retry_count,
            custom_fields=case.custom_fields,
            tags=case.tags,
            scenario=case.scenario,
            priority=case.priority,
            risk_level=case.risk_level,
            difficulty=case.difficulty,
            test_group=case.test_group,
            sort_order=case.sort_order,
            created_by=case.created_by.value if case.created_by else None,
            updated_by=case.updated_by.value if case.updated_by else None,
            created_at=case.created_at,
            updated_at=case.updated_at,
        )


class TestCaseListResponse(BaseModel):
    items: list[TestCaseResponse]
    next_cursor: str | None = None


class TestCaseValidationIssue(BaseModel):
    field: str
    code: str
    message: str
    severity: Literal["error", "warning"] = "error"


class TestCaseValidationResponse(BaseModel):
    ready: bool
    issues: list[TestCaseValidationIssue]


class CreateCaseTrialRunRequest(BaseModel):
    agent_version_id: UUID
    environment_template_id: UUID


class CaseTrialRunResponse(BaseModel):
    id: UUID
    project_id: UUID
    run_type: Literal["case_trial"]
    source_test_case_id: UUID
    agent_version_id: UUID
    dataset_version_id: UUID
    status: str
    workflow_id: str | None
    created: bool
    href: str
