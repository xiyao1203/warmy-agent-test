"""Datasets HTTP API request and response schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from agenttest.modules.datasets.domain.entities import (
    Dataset,
    DatasetVersion,
    TestCase,
)
from agenttest.modules.datasets.domain.value_objects import (
    ExecutionMode,
    Priority,
    RiskLevel,
    TestGroup,
    VersionStatus,
)


class CreateDatasetRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None


class UpdateDatasetRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class TestCaseFields(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    input: dict[str, object]
    execution_mode: ExecutionMode
    assertions: list[dict[str, object]] = Field(default_factory=list)
    scorers: list[dict[str, object]] = Field(default_factory=list)
    initial_state: dict[str, object] | None = None
    expected_outcome: dict[str, object] | None = None
    security_policies: list[dict[str, object]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    scenario: str | None = None
    priority: Priority | None = None
    risk_level: RiskLevel | None = None
    difficulty: str | None = None
    test_group: TestGroup | None = None


class CreateTestCaseRequest(TestCaseFields):
    pass


class UpdateTestCaseRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    input: dict[str, object] | None = None
    execution_mode: ExecutionMode | None = None
    assertions: list[dict[str, object]] | None = None
    scorers: list[dict[str, object]] | None = None
    initial_state: dict[str, object] | None = None
    expected_outcome: dict[str, object] | None = None
    security_policies: list[dict[str, object]] | None = None
    tags: list[str] | None = None
    scenario: str | None = None
    priority: Priority | None = None
    risk_level: RiskLevel | None = None
    difficulty: str | None = None
    test_group: TestGroup | None = None
    sort_order: int | None = Field(default=None, ge=0)


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


class DatasetResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: str | None
    created_by: UUID
    updated_by: UUID
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, dataset: Dataset) -> "DatasetResponse":
        return cls(
            id=dataset.dataset_id.value,
            project_id=dataset.project_id.value,
            name=dataset.name,
            description=dataset.description,
            created_by=dataset.created_by.value,
            updated_by=dataset.updated_by.value,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
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
    name: str
    input: dict[str, object]
    execution_mode: ExecutionMode
    assertions: list[dict[str, object]]
    scorers: list[dict[str, object]]
    initial_state: dict[str, object] | None
    expected_outcome: dict[str, object] | None
    security_policies: list[dict[str, object]]
    tags: list[str]
    scenario: str | None
    priority: Priority | None
    risk_level: RiskLevel | None
    difficulty: str | None
    test_group: TestGroup | None
    sort_order: int
    created_at: datetime | None
    updated_at: datetime | None

    @classmethod
    def from_domain(cls, case: TestCase) -> "TestCaseResponse":
        return cls(
            id=case.case_id.value,
            dataset_version_id=case.dataset_version_id.value,
            name=case.name,
            input=case.input,
            execution_mode=case.execution_mode,
            assertions=case.assertions,
            scorers=case.scorers,
            initial_state=case.initial_state,
            expected_outcome=case.expected_outcome,
            security_policies=case.security_policies,
            tags=case.tags,
            scenario=case.scenario,
            priority=case.priority,
            risk_level=case.risk_level,
            difficulty=case.difficulty,
            test_group=case.test_group,
            sort_order=case.sort_order,
            created_at=case.created_at,
            updated_at=case.updated_at,
        )


class TestCaseListResponse(BaseModel):
    items: list[TestCaseResponse]
    next_cursor: str | None = None
