"""人工、Agent、导入和执行共享的专业测试用例契约。"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Literal, Self, cast
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agenttest.modules.datasets.domain.entities import TestCase
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
REDACTED_SECRET = "[REDACTED]"
_SENSITIVE_KEYS = frozenset(
    {
        "api_key",
        "authorization",
        "cookie",
        "credentials",
        "password",
        "passwd",
        "proxy_authorization",
        "secret",
        "secret_key",
        "set_cookie",
        "token",
        "x_api_key",
    }
)
_SENSITIVE_SUFFIXES = (
    "_api_key",
    "_cookie",
    "_credential",
    "_password",
    "_passwd",
    "_secret",
    "_token",
)
_SENSITIVE_COLLAPSED_KEYS = frozenset(key.replace("_", "") for key in _SENSITIVE_KEYS)
_SENSITIVE_COLLAPSED_SUFFIXES = tuple(
    suffix.removeprefix("_").replace("_", "") for suffix in _SENSITIVE_SUFFIXES
)


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


class BrowserOperationV1(BaseModel):
    """Deterministic browser instruction kept separate from the human test step."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["goto", "click", "fill", "wait", "screenshot"]
    target: str | None = Field(default=None, max_length=2000)
    value: str | None = Field(default=None, max_length=10000)

    @model_validator(mode="after")
    def require_action_target(self) -> Self:
        if self.action != "screenshot" and not (self.target or "").strip():
            raise ValueError(f"browser operation {self.action} requires target")
        return self


class TestStepV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_no: int = Field(ge=1)
    action: str = Field(min_length=1, max_length=4000)
    operation: BrowserOperationV1 | None = None
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

    @classmethod
    def from_domain(cls, case: TestCase) -> Self:
        return cls.model_validate(
            {
                "case_key": case.case_key,
                "name": case.name,
                "objective": case.objective or case.name,
                "case_status": case.case_status,
                "template": case.template,
                "case_type": case.case_type,
                "automation_status": case.automation_status,
                "source": case.source,
                "source_ref": case.source_ref,
                "component": case.component,
                "requirement_refs": case.requirement_refs,
                "owner_id": case.owner_id.value if case.owner_id else None,
                "priority": case.priority,
                "risk_level": case.risk_level,
                "difficulty": case.difficulty,
                "tags": case.tags,
                "test_group": case.test_group,
                "scenario": case.scenario,
                "preconditions": case.preconditions,
                "initial_state": case.initial_state,
                "input": case.input,
                "data_bindings": case.data_bindings,
                "steps": case.steps,
                "expected_outcome": case.expected_outcome,
                "assertions": case.assertions,
                "scorers": case.scorers,
                "security_policies": case.security_policies,
                "artifact_requirements": case.artifact_requirements,
                "postconditions": case.postconditions,
                "estimated_duration_seconds": case.estimated_duration_seconds,
                "execution_mode": case.execution_mode,
                "timeout_seconds": case.timeout_seconds,
                "retry_count": case.retry_count,
                "custom_fields": case.custom_fields,
            }
        )

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
        if (
            self.case_status is TestCaseStatus.READY
            and self.execution_mode is ExecutionMode.BROWSER
            and any(step.operation is None for step in self.steps)
        ):
            raise ValueError(
                "Ready browser test case requires a typed browser operation for every step"
            )
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
        return cast(
            dict[str, object],
            sanitize_secret_values(self.model_dump(mode="json")),
        )


def build_case_spec_snapshot(case: TestCase) -> dict[str, object]:
    """Compile the immutable worker projection of a professional case."""
    bindings: list[dict[str, object]] = []
    for raw in case.data_bindings:
        binding = dict(raw)
        if binding.get("sensitive") or binding.get("source") == "credential":
            binding.pop("value", None)
        bindings.append(binding)
    snapshot = {
        "schema_version": "platform-test-case/v1",
        "case_key": case.case_key,
        "objective": case.objective,
        "preconditions": list(case.preconditions),
        "initial_state": dict(case.initial_state) if case.initial_state else None,
        "input": dict(case.input),
        "data_bindings": bindings,
        "steps": [dict(step) for step in case.steps],
        "expected_outcome": (
            dict(case.expected_outcome) if case.expected_outcome is not None else None
        ),
        "assertions": [dict(item) for item in case.assertions],
        "scorers": [dict(item) for item in case.scorers],
        "security_policies": [dict(item) for item in case.security_policies],
        "artifact_requirements": [dict(item) for item in case.artifact_requirements],
        "postconditions": list(case.postconditions),
        "execution_mode": case.execution_mode.value,
        "timeout_seconds": case.timeout_seconds,
        "retry_count": case.retry_count,
    }
    return cast(dict[str, object], sanitize_secret_values(snapshot))


def sanitize_secret_values(value: object) -> object:
    """Recursively redact secret-bearing keys without changing safe metric names."""
    if isinstance(value, Mapping):
        return {
            str(key): (
                REDACTED_SECRET if _is_sensitive_key(str(key)) else sanitize_secret_values(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list | tuple):
        return [sanitize_secret_values(item) for item in value]
    return value


def _is_sensitive_key(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")
    collapsed = normalized.replace("_", "")
    return (
        normalized in _SENSITIVE_KEYS
        or normalized.endswith(_SENSITIVE_SUFFIXES)
        or collapsed in _SENSITIVE_COLLAPSED_KEYS
        or collapsed.endswith(_SENSITIVE_COLLAPSED_SUFFIXES)
    )
