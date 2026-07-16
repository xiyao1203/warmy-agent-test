"""Typed read models used by decision-ready core lists."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, Field

from agenttest.shared.application.resource_reference import ResourceReference


class ProjectSummaryMetrics(BaseModel):
    member_count: int = 0
    agent_count: int = 0
    dataset_count: int = 0
    test_case_count: int = 0
    test_plan_count: int = 0
    active_environment_count: int = 0
    open_review_count: int = 0
    last_run: ResourceReference | None = None
    last_run_status: str | None = None
    last_run_at: datetime | None = None


class AgentSummaryMetrics(BaseModel):
    current_version: ResourceReference | None = None
    version_status: str | None = None
    protocol: str | None = None
    model: str | None = None
    tool_count: int = 0
    credential_binding_count: int = 0
    connection_status: str | None = None
    last_run_status: str | None = None
    pass_rate: float | None = None


class DatasetSummaryMetrics(BaseModel):
    latest_version: ResourceReference | None = None
    version_status: str | None = None
    case_count: int = 0
    ready_count: int = 0
    api_count: int = 0
    browser_count: int = 0
    codex_explore_count: int = 0
    priority_coverage: dict[str, int] = Field(default_factory=dict)
    source_distribution: dict[str, int] = Field(default_factory=dict)
    published_at: datetime | None = None


class TestPlanSummaryMetrics(BaseModel):
    latest_version: ResourceReference | None = None
    version_status: str | None = None
    agent_ref: ResourceReference | None = None
    dataset_ref: ResourceReference | None = None
    environment_ref: ResourceReference | None = None
    case_count: int = 0
    repeat_count: int = 1
    concurrency: int = 1
    timeout_seconds: int | None = None
    retry_count: int = 0
    scorer_count: int = 0
    last_run_status: str | None = None
    pass_rate: float | None = None


class RunSummaryMetrics(BaseModel):
    run_number: str
    plan_ref: ResourceReference | None = None
    agent_ref: ResourceReference | None = None
    dataset_ref: ResourceReference | None = None
    source_case_ref: ResourceReference | None = None
    trigger_type: str = "manual"
    progress: float = 0.0
    duration_ms: int | None = None
    token_usage: dict[str, int] | None = None
    cost: float | None = None
    created_by_ref: ResourceReference | None = None


class EnvironmentSummaryMetrics(BaseModel):
    current_version: ResourceReference | None = None
    version_status: str | None = None
    credential_binding_count: int = 0
    browser_profile_ref: ResourceReference | None = None
    validation_status: str | None = None
    last_validated_at: datetime | None = None
    last_run_at: datetime | None = None


class ScorerSummaryMetrics(BaseModel):
    latest_version: ResourceReference | None = None
    version_status: str | None = None
    usage_count: int = 0
    last_calibrated_at: datetime | None = None


class ExperimentSummaryMetrics(BaseModel):
    baseline_run_ref: ResourceReference | None = None
    candidate_run_ref: ResourceReference | None = None
    case_count: int = 0
    improved_count: int = 0
    regressed_count: int = 0
    pass_rate_delta: float | None = None
    score_delta: float | None = None
    cost_delta: float | None = None


class SecurityScanSummaryMetrics(BaseModel):
    agent_ref: ResourceReference | None = None
    run_ref: ResourceReference | None = None
    profile_ref: ResourceReference | None = None
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    duration_ms: int | None = None
    started_at: datetime | None = None


class ReviewSummaryMetrics(BaseModel):
    run_ref: ResourceReference | None = None
    case_ref: ResourceReference | None = None
    enqueue_reason: str = "low_confidence"
    priority: int = 0
    assignee_ref: ResourceReference | None = None
    age_seconds: int = 0


class GateSummaryMetrics(BaseModel):
    scope: str = "project"
    rule_summary: str = ""
    last_decision: str | None = None
    blocking_count: int = 0
    last_run_ref: ResourceReference | None = None
    evaluated_at: datetime | None = None


class CoreSummaryReader(Protocol):
    async def projects(self, ids: list[UUID]) -> dict[UUID, ProjectSummaryMetrics]: ...

    async def agents(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, AgentSummaryMetrics]: ...

    async def datasets(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, DatasetSummaryMetrics]: ...

    async def test_plans(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, TestPlanSummaryMetrics]: ...

    async def runs(self, project_id: UUID, ids: list[UUID]) -> dict[UUID, RunSummaryMetrics]: ...

    async def environments(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, EnvironmentSummaryMetrics]: ...

    async def scorers(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, ScorerSummaryMetrics]: ...

    async def experiments(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, ExperimentSummaryMetrics]: ...

    async def security_scans(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, SecurityScanSummaryMetrics]: ...

    async def reviews(
        self, project_id: UUID, ids: list[UUID]
    ) -> dict[UUID, ReviewSummaryMetrics]: ...

    async def gates(self, project_id: UUID, ids: list[UUID]) -> dict[UUID, GateSummaryMetrics]: ...
