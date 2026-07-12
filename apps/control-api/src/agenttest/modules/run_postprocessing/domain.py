from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class PostprocessStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"

    @property
    def is_terminal(self) -> bool:
        return self in {
            PostprocessStatus.COMPLETED,
            PostprocessStatus.COMPLETED_WITH_WARNINGS,
            PostprocessStatus.FAILED,
        }


class PostprocessStage(StrEnum):
    CLASSIFY = "classify"
    DIAGNOSE = "diagnose"
    REPRODUCE = "reproduce"
    CALIBRATE = "calibrate"
    EVALUATE_GATE = "evaluate_gate"
    FINALIZE = "finalize"


@dataclass(frozen=True, slots=True)
class StageResult:
    stage: PostprocessStage
    status: str
    output: dict[str, object]
    warning_code: str | None
    error_type: str | None
    error_message: str | None
    completed_at: datetime


@dataclass(slots=True)
class RunPostprocessJob:
    job_id: UUID
    project_id: UUID
    run_id: UUID
    pipeline_version: str
    status: PostprocessStatus
    current_stage: PostprocessStage | None
    workflow_id: str | None
    attempt: int
    warning_codes: list[str]
    error_type: str | None
    error_message: str | None
    stage_results: list[StageResult]
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    _active_stage: PostprocessStage | None = field(default=None, repr=False)

    @classmethod
    def create(cls, project_id: UUID, run_id: UUID, pipeline_version: str) -> RunPostprocessJob:
        version = pipeline_version.strip()
        if not version:
            raise ValueError("Pipeline version is required")
        now = datetime.now(UTC)
        return cls(
            job_id=uuid4(),
            project_id=project_id,
            run_id=run_id,
            pipeline_version=version,
            status=PostprocessStatus.PENDING,
            current_stage=None,
            workflow_id=None,
            attempt=0,
            warning_codes=[],
            error_type=None,
            error_message=None,
            stage_results=[],
            created_at=now,
            updated_at=now,
        )

    def start(self, workflow_id: str) -> None:
        if self.status.is_terminal:
            raise ValueError("Postprocess job is terminal")
        workflow = workflow_id.strip()
        if not workflow:
            raise ValueError("Workflow ID is required")
        now = datetime.now(UTC)
        self.workflow_id = workflow
        self.status = PostprocessStatus.RUNNING
        self.attempt += 1
        self.started_at = self.started_at or now
        self.updated_at = now

    def begin_stage(self, stage: PostprocessStage) -> None:
        if self.status.is_terminal:
            raise ValueError("Postprocess job is terminal")
        if self.status is not PostprocessStatus.RUNNING:
            raise ValueError("Postprocess job must be running")
        expected = self._expected_stage()
        if stage is not expected:
            raise ValueError(f"Expected stage {expected.value}")
        if self._active_stage is not None:
            raise ValueError(f"Stage {self._active_stage.value} is already active")
        self.current_stage = stage
        self._active_stage = stage
        self.updated_at = datetime.now(UTC)

    def complete_stage(self, stage: PostprocessStage, output: dict[str, object]) -> None:
        self._require_active(stage)
        now = datetime.now(UTC)
        self.stage_results.append(
            StageResult(stage, "completed", dict(output), None, None, None, now)
        )
        self._active_stage = None
        self.updated_at = now
        if stage is PostprocessStage.FINALIZE:
            self.status = (
                PostprocessStatus.COMPLETED_WITH_WARNINGS
                if self.warning_codes
                else PostprocessStatus.COMPLETED
            )
            self.completed_at = now

    def fail_stage(
        self,
        stage: PostprocessStage,
        error_type: str,
        error_message: str,
        *,
        required: bool,
    ) -> None:
        self._require_active(stage)
        now = datetime.now(UTC)
        warning_code = None if required else error_type
        self.stage_results.append(
            StageResult(
                stage,
                "failed" if required else "warning",
                {},
                warning_code,
                error_type,
                error_message,
                now,
            )
        )
        self._active_stage = None
        self.updated_at = now
        if required:
            self.status = PostprocessStatus.FAILED
            self.error_type = error_type
            self.error_message = error_message
            self.completed_at = now
        elif error_type not in self.warning_codes:
            self.warning_codes.append(error_type)

    def _expected_stage(self) -> PostprocessStage:
        completed = len(self.stage_results)
        stages = list(PostprocessStage)
        if completed >= len(stages):
            raise ValueError("Postprocess job has no remaining stages")
        return stages[completed]

    def _require_active(self, stage: PostprocessStage) -> None:
        if self.status.is_terminal:
            raise ValueError("Postprocess job is terminal")
        if self._active_stage is not stage:
            raise ValueError(f"Stage {stage.value} is not active")
