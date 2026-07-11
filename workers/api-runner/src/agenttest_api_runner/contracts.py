from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ResultCallbackConfig:
    base_url: str
    internal_token: str
    project_id: str


@dataclass(frozen=True, slots=True)
class RunCaseTask:
    run_case_id: str
    input: dict[str, Any]
    assertions: list[dict[str, Any]]
    execution_mode: str = "api"


@dataclass(frozen=True, slots=True)
class RunTask:
    run_id: str
    idempotency_key: str
    cases: list[RunCaseTask]
    agent_config: dict[str, Any]
    agent_type: str = "generic_http"
    environment: dict[str, Any] = field(default_factory=dict)
    execution_policy: dict[str, Any] = field(default_factory=dict)
    scorer_configs: list[dict[str, Any]] = field(default_factory=list)
    browser_profile_snapshot: dict[str, Any] = field(default_factory=dict)
    callback: ResultCallbackConfig | None = None


@dataclass(frozen=True, slots=True)
class ReportArtifact:
    name: str
    content_type: str
    content: str


@dataclass(frozen=True, slots=True)
class CaseScore:
    scorer_version_id: str
    scorer_type: str
    score: float
    passed: bool
    explanation: str = ""
    confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class RunCaseResult:
    run_case_id: str
    status: str
    output: dict[str, Any] | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)
    error_type: str | None = None
    error_message: str | None = None
    duration_ms: int | None = None
    scores: list[CaseScore] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RunResult:
    run_id: str
    status: str
    cases: list[RunCaseResult]
    reports: list[ReportArtifact] = field(default_factory=list)
