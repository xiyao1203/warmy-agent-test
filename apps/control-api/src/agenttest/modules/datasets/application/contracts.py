"""人工、Agent、导入和执行共享的专业测试用例契约。"""

from __future__ import annotations

import json
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agenttest.modules.datasets.domain.value_objects import (
    ArtifactKind,
    AutomationStatus,
    DataBindingSource,
    DataValueType,
    ExecutionMode,
    Priority,
    RiskLevel,
    TestCaseSource,
    TestCaseStatus,
    TestCaseTemplate,
    TestCaseType,
    TestGroup,
)

MAX_CUSTOM_FIELDS_BYTES = 16 * 1024


class ArtifactRequirementV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: ArtifactKind
    required: bool = True
    label: str | None = Field(default=None, max_length=200)


class DataBindingV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    source: DataBindingSource = DataBindingSource.LITERAL
    value: object | None = None
    reference: str | None = Field(default=None, min_length=1, max_length=500)
    value_type: DataValueType = DataValueType.STRING
    sensitive: bool = False
    description: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def protect_sensitive_values(self) -> Self:
        if self.sensitive or self.source is DataBindingSource.CREDENTIAL:
            if not self.reference or self.value is not None:
                raise ValueError(
                    "Sensitive data binding requires reference and forbids literal value"
                )
        return self


class TestStepV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_no: int = Field(ge=1)
    action: str = Field(min_length=1, max_length=4000)
    test_data: dict[str, object] = Field(default_factory=dict)
    expected_result: str = Field(min_length=1, max_length=4000)
    assertions: list[dict[str, object]] = Field(default_factory=list, max_length=50)
    artifact_requirements: list[ArtifactRequirementV1] = Field(
        default_factory=list,
        max_length=20,
    )


class PlatformTestCaseV1(BaseModel):
    """平台唯一的可编辑、可生成和可执行测试用例格式。"""

    model_config = ConfigDict(extra="forbid")

    case_key: str | None = Field(default=None, min_length=3, max_length=40)
    name: str = Field(min_length=1, max_length=500)
    objective: str = Field(min_length=1, max_length=4000)
    case_status: TestCaseStatus = TestCaseStatus.DRAFT
    template: TestCaseTemplate = TestCaseTemplate.AI_EVAL
    case_type: TestCaseType = TestCaseType.FUNCTIONAL
    automation_status: AutomationStatus = AutomationStatus.CANDIDATE
    source: TestCaseSource = TestCaseSource.MANUAL
    source_ref: str | None = Field(default=None, max_length=500)
    component: str | None = Field(default=None, max_length=200)
    requirement_refs: list[str] = Field(default_factory=list, max_length=50)
    owner_id: UUID | None = None
    priority: Priority | None = None
    risk_level: RiskLevel | None = None
    difficulty: str | None = Field(default=None, max_length=32)
    tags: list[str] = Field(default_factory=list, max_length=100)
    test_group: TestGroup | None = None
    scenario: str | None = Field(default=None, max_length=200)

    preconditions: list[str] = Field(default_factory=list, max_length=100)
    initial_state: dict[str, object] | None = None
    input: dict[str, object]
    data_bindings: list[DataBindingV1] = Field(default_factory=list, max_length=100)
    steps: list[TestStepV1] = Field(default_factory=list, max_length=200)

    expected_outcome: dict[str, object] | None = None
    assertions: list[dict[str, object]] = Field(default_factory=list, max_length=100)
    scorers: list[dict[str, object]] = Field(default_factory=list, max_length=100)
    security_policies: list[dict[str, object]] = Field(default_factory=list, max_length=100)
    artifact_requirements: list[ArtifactRequirementV1] = Field(
        default_factory=list,
        max_length=20,
    )
    postconditions: list[str] = Field(default_factory=list, max_length=100)
    estimated_duration_seconds: int | None = Field(default=None, ge=1, le=86_400)
    execution_mode: ExecutionMode
    timeout_seconds: int | None = Field(default=None, ge=1, le=86_400)
    retry_count: int = Field(default=0, ge=0, le=10)
    custom_fields: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_professional_contract(self) -> Self:
        self.steps = [
            step.model_copy(update={"step_no": index})
            for index, step in enumerate(self.steps, start=1)
        ]
        if self.template is TestCaseTemplate.STEP_BY_STEP and not self.steps:
            raise ValueError("step_by_step template requires at least one step")
        if self.case_status is TestCaseStatus.READY and not self._has_oracle:
            raise ValueError("Ready test case requires at least one executable oracle")
        try:
            encoded = json.dumps(
                self.custom_fields,
                ensure_ascii=False,
                separators=(",", ":"),
                default=str,
            ).encode()
        except (TypeError, ValueError) as error:
            raise ValueError("custom_fields must be JSON serializable") from error
        if len(encoded) > MAX_CUSTOM_FIELDS_BYTES:
            raise ValueError("custom_fields must not exceed 16 KiB")
        return self

    @property
    def _has_oracle(self) -> bool:
        return bool(
            self.assertions
            or self.scorers
            or self.security_policies
            or any(step.assertions for step in self.steps)
        )

    def secret_free_dump(self) -> dict[str, object]:
        """Return an execution-safe representation without credential values."""
        return self.model_dump(mode="json")
