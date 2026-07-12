from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class PostprocessWorkflowTask:
    project_id: str
    run_id: str
    pipeline_version: str
    callback_base_url: str


@dataclass(frozen=True, slots=True)
class PostprocessStageTask:
    workflow: PostprocessWorkflowTask
    stage: str
    attempt: int = 1


@dataclass(frozen=True, slots=True)
class PostprocessStageResponse:
    status: str
    output: dict[str, Any] = field(default_factory=dict)
    warning_code: str | None = None


@dataclass(frozen=True, slots=True)
class PostprocessWorkflowResult:
    run_id: str
    pipeline_version: str
    status: str
    warning_codes: tuple[str, ...] = ()
    error_type: str | None = None
