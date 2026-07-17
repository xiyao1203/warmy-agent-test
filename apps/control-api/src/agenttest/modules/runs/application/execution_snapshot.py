"""Versioned contract passed from the Control API to execution workers."""

from __future__ import annotations

from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agenttest.modules.agents.public import AgentInvocationConfig
from agenttest.modules.environments.public import EnvironmentRuntimeSnapshot


class PlatformTestCaseSnapshotV1(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["platform-test-case/v1"]
    case_key: str | None = None
    objective: str
    preconditions: list[str] = Field(default_factory=list)
    initial_state: dict[str, object] | None = None
    input: dict[str, object]
    data_bindings: list[dict[str, object]] = Field(default_factory=list)
    steps: list[dict[str, object]] = Field(default_factory=list)
    expected_outcome: dict[str, object] | None = None
    assertions: list[dict[str, object]] = Field(default_factory=list)
    scorers: list[dict[str, object]] = Field(default_factory=list)
    security_policies: list[dict[str, object]] = Field(default_factory=list)
    artifact_requirements: list[dict[str, object]] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    execution_mode: str
    timeout_seconds: int | None = None
    retry_count: int = 0

    @model_validator(mode="after")
    def reject_embedded_secrets(self) -> Self:
        for binding in self.data_bindings:
            if (binding.get("sensitive") or binding.get("source") == "credential") and (
                "value" in binding
            ):
                raise ValueError("credential bindings must not contain values")
        return self


class CaseExecutionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_case_id: UUID
    test_case_id: UUID
    name: str = Field(min_length=1)
    input: dict[str, object]
    assertions: list[dict[str, object]] = Field(default_factory=list)
    expected_output: object | None = None
    tags: list[str] = Field(default_factory=list)
    case_spec: PlatformTestCaseSnapshotV1 | None = None


class ScorerBindingSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    scorer_version_id: UUID
    weight: float = Field(default=1.0, gt=0)
    threshold: float | None = Field(default=None, ge=0, le=1)


class SecurityBindingSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    security_profile_id: UUID
    blocking: bool = True


class EvaluationPolicySnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_only: bool = False
    pass_threshold: float = Field(default=1.0, ge=0, le=1)
    scorers: list[ScorerBindingSnapshot] = Field(default_factory=list)
    security: list[SecurityBindingSnapshot] = Field(default_factory=list)


class RunExecutionSnapshot(BaseModel):
    """All immutable inputs needed to reproduce a Run."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: int = Field(ge=1)
    project_id: UUID
    run_id: UUID
    test_plan_version_id: UUID | None
    run_type: Literal["plan", "case_trial"] = "plan"
    source_test_case_id: UUID | None = None
    agent_version_id: UUID
    dataset_version_id: UUID
    agent: AgentInvocationConfig
    environment: EnvironmentRuntimeSnapshot
    cases: Annotated[list[CaseExecutionSnapshot], Field(min_length=1)]
    evaluation_policy: EvaluationPolicySnapshot

    @model_validator(mode="after")
    def validate_source_by_type(self) -> Self:
        if self.run_type == "plan" and self.test_plan_version_id is None:
            raise ValueError("plan run requires test_plan_version_id")
        if self.run_type == "case_trial" and self.source_test_case_id is None:
            raise ValueError("case_trial requires source_test_case_id")
        return self
