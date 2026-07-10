"""Secret-free execution evidence for a run case."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4


class ExecutionOutcome(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


class QualityDecision(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    REVIEW_REQUIRED = "review_required"


class SecurityDecision(StrEnum):
    CLEAR = "clear"
    FINDING = "finding"
    BLOCKED = "blocked"


class RunCaseStage(StrEnum):
    PREPARING = "preparing"
    CREDENTIAL_LEASE = "credential_lease"
    AUTHENTICATING = "authenticating"
    EXECUTING = "executing"
    WAITING = "waiting"
    COLLECTING = "collecting"
    EVALUATING = "evaluating"
    AWAITING_REVIEW = "awaiting_review"
    CLEANUP = "cleanup"


@dataclass(frozen=True, slots=True)
class RunCaseStageEvent:
    event_id: str
    project_id: str
    run_id: str
    run_case_id: str
    attempt: int
    stage: RunCaseStage
    status: str
    payload: dict[str, object]
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        project_id: str,
        run_id: str,
        run_case_id: str,
        attempt: int,
        stage: str,
        status: str,
        payload: Mapping[str, object] | None = None,
    ) -> RunCaseStageEvent:
        if attempt < 1:
            raise ValueError("attempt must be >= 1")
        safe_payload = dict(payload or {})
        if _contains_sensitive_key(safe_payload):
            raise ValueError("stage event contains sensitive fields")
        return cls(
            event_id=str(uuid4()),
            project_id=project_id,
            run_id=run_id,
            run_case_id=run_case_id,
            attempt=attempt,
            stage=RunCaseStage(stage),
            status=status,
            payload=safe_payload,
            created_at=datetime.now(UTC),
        )


_SENSITIVE_KEYS = frozenset(
    {
        "api_key",
        "authorization",
        "cookie",
        "credentials",
        "password",
        "secret",
        "secret_key",
        "token",
    }
)


@dataclass(frozen=True, slots=True)
class RunCaseEvidence:
    execution_outcome: ExecutionOutcome = ExecutionOutcome.ERROR
    quality_decision: QualityDecision = QualityDecision.REVIEW_REQUIRED
    security_decision: SecurityDecision = SecurityDecision.CLEAR
    canvas: dict[str, object] = field(default_factory=dict)
    artifacts: tuple[dict[str, object], ...] = ()
    trace: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: Mapping[str, object]) -> RunCaseEvidence:
        if _contains_sensitive_key(payload):
            raise ValueError("execution evidence contains sensitive fields")
        artifacts = payload.get("artifacts", [])
        return cls(
            execution_outcome=ExecutionOutcome(
                str(payload.get("execution_outcome", ExecutionOutcome.ERROR.value))
            ),
            quality_decision=QualityDecision(
                str(payload.get("quality_decision", QualityDecision.REVIEW_REQUIRED.value))
            ),
            security_decision=SecurityDecision(
                str(payload.get("security_decision", SecurityDecision.CLEAR.value))
            ),
            canvas=dict(_mapping(payload.get("canvas"))),
            artifacts=tuple(
                dict(item) for item in artifacts if isinstance(item, Mapping)
            )
            if isinstance(artifacts, list | tuple)
            else (),
            trace=dict(_mapping(payload.get("trace"))),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "execution_outcome": self.execution_outcome.value,
            "quality_decision": self.quality_decision.value,
            "security_decision": self.security_decision.value,
            "canvas": dict(self.canvas),
            "artifacts": [dict(item) for item in self.artifacts],
            "trace": dict(self.trace),
        }


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _contains_sensitive_key(value: object) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in _SENSITIVE_KEYS:
                return True
            if _contains_sensitive_key(item):
                return True
        return False
    if isinstance(value, list | tuple):
        return any(_contains_sensitive_key(item) for item in value)
    return False
