"""Secret-free execution evidence for a run case."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from uuid import UUID, uuid4


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
class EvidenceScope:
    project_id: UUID
    run_id: UUID
    run_case_id: UUID
    attempt: int
    stage: str

    def __post_init__(self) -> None:
        if self.attempt < 1:
            raise ValueError("evidence attempt must be >= 1")
        if not self.stage.strip():
            raise ValueError("evidence stage is required")

    def to_dict(self) -> dict[str, object]:
        return {
            "project_id": str(self.project_id),
            "run_id": str(self.run_id),
            "run_case_id": str(self.run_case_id),
            "attempt": self.attempt,
            "stage": self.stage,
        }


@dataclass(frozen=True, slots=True)
class EvidenceEnvelope:
    evidence_id: UUID
    kind: str
    producer: str
    scope: EvidenceScope
    payload: dict[str, object]
    artifact_refs: tuple[dict[str, object], ...]
    redacted: bool
    created_at: datetime
    content_hash: str

    @classmethod
    def create(
        cls,
        *,
        kind: str,
        producer: str,
        scope: EvidenceScope,
        payload: Mapping[str, object],
        artifact_refs: tuple[dict[str, object], ...] = (),
        evidence_id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> EvidenceEnvelope:
        safe_payload = dict(payload)
        safe_artifacts = tuple(dict(item) for item in artifact_refs)
        if _contains_sensitive_key(safe_payload) or _contains_sensitive_key(safe_artifacts):
            raise ValueError("evidence contains sensitive fields")
        if not kind.strip() or not producer.strip():
            raise ValueError("evidence kind and producer are required")
        identity = evidence_id or uuid4()
        timestamp = created_at or datetime.now(UTC)
        unsigned = {
            "evidence_id": str(identity),
            "kind": kind,
            "producer": producer,
            "scope": scope.to_dict(),
            "payload": safe_payload,
            "artifact_refs": list(safe_artifacts),
            "redacted": True,
            "created_at": timestamp.isoformat(),
        }
        return cls(
            evidence_id=identity,
            kind=kind,
            producer=producer,
            scope=scope,
            payload=safe_payload,
            artifact_refs=safe_artifacts,
            redacted=True,
            created_at=timestamp,
            content_hash=_canonical_hash(unsigned),
        )

    def unsigned_dict(self) -> dict[str, object]:
        return {
            "evidence_id": str(self.evidence_id),
            "kind": self.kind,
            "producer": self.producer,
            "scope": self.scope.to_dict(),
            "payload": dict(self.payload),
            "artifact_refs": [dict(item) for item in self.artifact_refs],
            "redacted": self.redacted,
            "created_at": self.created_at.isoformat(),
        }

    def with_content_hash(self, value: str) -> EvidenceEnvelope:
        return replace(self, content_hash=value)

    def verify_hash(self) -> bool:
        return self.content_hash == _canonical_hash(self.unsigned_dict())


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
            artifacts=tuple(dict(item) for item in artifacts if isinstance(item, Mapping))
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


def _canonical_hash(value: Mapping[str, object]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()
