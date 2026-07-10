from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from agenttest.modules.identity.public import UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.runs.domain.value_objects import RunCaseStatus, RunStatus
from agenttest.modules.test_plans.public import TestPlanVersionId


@dataclass(frozen=True, slots=True)
class RunId:
    value: UUID

    @classmethod
    def new(cls) -> RunId:
        return cls(uuid4())


@dataclass(frozen=True, slots=True)
class RunCaseId:
    value: UUID

    @classmethod
    def new(cls) -> RunCaseId:
        return cls(uuid4())


@dataclass(slots=True)
class Run:
    run_id: RunId
    project_id: ProjectId
    test_plan_version_id: TestPlanVersionId
    agent_version_id: UUID
    dataset_version_id: UUID
    idempotency_key: str
    created_by: UserId
    config_snapshot: dict[str, object]
    plugin_snapshot: dict[str, object]
    total_cases: int
    status: RunStatus
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    passed_cases: int = 0
    failed_cases: int = 0
    error_cases: int = 0
    cancelled_cases: int = 0
    workflow_id: str | None = None

    @classmethod
    def create(
        cls,
        *,
        run_id: RunId,
        project_id: ProjectId,
        test_plan_version_id: TestPlanVersionId,
        agent_version_id: UUID,
        dataset_version_id: UUID,
        idempotency_key: str,
        created_by: UserId,
        config_snapshot: dict[str, object],
        plugin_snapshot: dict[str, object],
        total_cases: int,
    ) -> Run:
        normalized_key = idempotency_key.strip()
        if not normalized_key:
            raise ValueError("idempotency_key is required")
        if total_cases < 1:
            raise ValueError("total_cases must be >= 1")
        if not config_snapshot or not plugin_snapshot:
            raise ValueError("reproducible config and plugin snapshots are required")
        now = datetime.now(UTC)
        return cls(
            run_id=run_id,
            project_id=project_id,
            test_plan_version_id=test_plan_version_id,
            agent_version_id=agent_version_id,
            dataset_version_id=dataset_version_id,
            idempotency_key=normalized_key,
            created_by=created_by,
            config_snapshot=dict(config_snapshot),
            plugin_snapshot=dict(plugin_snapshot),
            total_cases=total_cases,
            status=RunStatus.QUEUED,
            created_at=now,
            updated_at=now,
        )

    def start(self, workflow_id: str | None = None) -> None:
        if self.status is not RunStatus.QUEUED:
            raise ValueError("Only a queued run can start")
        now = datetime.now(UTC)
        self.status = RunStatus.RUNNING
        self.workflow_id = workflow_id
        self.started_at = now
        self.updated_at = now

    def complete(
        self,
        *,
        passed_cases: int,
        failed_cases: int,
        error_cases: int,
        cancelled_cases: int = 0,
    ) -> None:
        if self.status is not RunStatus.RUNNING:
            raise ValueError("Only a running run can complete")
        if passed_cases + failed_cases + error_cases + cancelled_cases != self.total_cases:
            raise ValueError("case counts must equal total_cases")
        self.passed_cases = passed_cases
        self.failed_cases = failed_cases
        self.error_cases = error_cases
        self.cancelled_cases = cancelled_cases
        if cancelled_cases:
            self.status = RunStatus.CANCELLED
        elif error_cases:
            self.status = RunStatus.ERROR
        elif failed_cases:
            self.status = RunStatus.FAILED
        else:
            self.status = RunStatus.PASSED
        now = datetime.now(UTC)
        self.completed_at = now
        self.updated_at = now

    def cancel(self) -> None:
        if self.status.is_terminal:
            raise ValueError("A terminal run cannot be cancelled")
        now = datetime.now(UTC)
        self.status = RunStatus.CANCELLED
        self.completed_at = now
        self.updated_at = now


@dataclass(slots=True)
class RunCase:
    run_case_id: RunCaseId
    run_id: RunId
    test_case_id: UUID
    name: str
    input_snapshot: dict[str, object]
    assertion_snapshot: list[dict[str, object]]
    execution_mode: str = "api"
    status: RunCaseStatus = RunCaseStatus.QUEUED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    output: dict[str, object] | None = None
    trace: list[dict[str, object]] = field(default_factory=list)
    error_type: str | None = None
    error_message: str | None = None
    duration_ms: int | None = None
    evidence: dict[str, object] = field(default_factory=dict)
    quality_summary: dict[str, object] = field(default_factory=dict)
    security_summary: dict[str, object] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        run_case_id: RunCaseId,
        run_id: RunId,
        test_case_id: UUID,
        name: str,
        input_snapshot: dict[str, object],
        assertion_snapshot: list[dict[str, object]],
        execution_mode: str = "api",
    ) -> RunCase:
        if not name.strip():
            raise ValueError("Run case name is required")
        now = datetime.now(UTC)
        return cls(
            run_case_id=run_case_id,
            run_id=run_id,
            test_case_id=test_case_id,
            name=name.strip(),
            input_snapshot=dict(input_snapshot),
            assertion_snapshot=list(assertion_snapshot),
            execution_mode=execution_mode,
            status=RunCaseStatus.QUEUED,
            created_at=now,
            updated_at=now,
        )

    def start(self) -> None:
        if self.status is not RunCaseStatus.QUEUED:
            raise ValueError("Only a queued run case can start")
        now = datetime.now(UTC)
        self.status = RunCaseStatus.RUNNING
        self.started_at = now
        self.updated_at = now

    def pass_case(
        self,
        *,
        output: dict[str, object],
        trace: list[dict[str, object]],
        duration_ms: int,
    ) -> None:
        self._finish(RunCaseStatus.PASSED, trace=trace)
        self.output = dict(output)
        self.duration_ms = duration_ms

    def fail(
        self,
        *,
        status: RunCaseStatus,
        error_type: str,
        error_message: str,
        trace: list[dict[str, object]],
        duration_ms: int | None = None,
    ) -> None:
        if status not in {
            RunCaseStatus.FAILED,
            RunCaseStatus.ERROR,
            RunCaseStatus.CANCELLED,
        }:
            raise ValueError("Failure status must be failed, error, or cancelled")
        self._finish(status, trace=trace)
        self.error_type = error_type
        self.error_message = error_message
        self.duration_ms = duration_ms

    def _finish(
        self,
        status: RunCaseStatus,
        *,
        trace: list[dict[str, object]],
    ) -> None:
        if self.status is not RunCaseStatus.RUNNING:
            raise ValueError("Only a running run case can finish")
        now = datetime.now(UTC)
        self.status = status
        self.trace = list(trace)
        self.completed_at = now
        self.updated_at = now
