"""Versioned contract passed from the Control API to execution workers."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from agenttest.modules.agents.domain.invocation import AgentInvocationConfig
from agenttest.modules.environments.domain.runtime import EnvironmentRuntimeSnapshot


class CaseExecutionSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_case_id: UUID
    test_case_id: UUID
    name: str = Field(min_length=1)
    input: dict[str, object]
    assertions: list[dict[str, object]] = Field(default_factory=list)
    expected_output: object | None = None
    tags: list[str] = Field(default_factory=list)


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
    test_plan_version_id: UUID
    agent_version_id: UUID
    dataset_version_id: UUID
    agent: AgentInvocationConfig
    environment: EnvironmentRuntimeSnapshot
    cases: Annotated[list[CaseExecutionSnapshot], Field(min_length=1)]
    evaluation_policy: EvaluationPolicySnapshot
