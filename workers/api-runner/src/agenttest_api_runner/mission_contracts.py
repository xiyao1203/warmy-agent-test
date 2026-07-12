from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class MissionWorkflowTask:
    project_id: str
    mission_id: str
    revision_id: str
    revision_hash: str
    callback_base_url: str
    idempotency_key: str = ""


@dataclass(frozen=True, slots=True)
class MissionStageResponse:
    status: str
    output: dict[str, object] = field(default_factory=dict)
    error_type: str | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class MissionWorkflowResult:
    mission_id: str
    revision_id: str
    status: str
    error_type: str | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class MissionStageTask:
    mission: MissionWorkflowTask
    stage: str
    resume_attempt: int = 0
