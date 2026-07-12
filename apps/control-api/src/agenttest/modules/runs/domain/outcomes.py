from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Self
from uuid import UUID


class OutcomeStatus(StrEnum):
    NOT_EVALUATED = "not_evaluated"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True, slots=True)
class Outcome:
    status: OutcomeStatus = OutcomeStatus.NOT_EVALUATED
    code: str = ""
    reason: str = ""
    evidence_ids: tuple[UUID, ...] = ()
    evaluated_at: datetime | None = None

    def __post_init__(self) -> None:
        if (
            self.status
            in {
                OutcomeStatus.FAILED,
                OutcomeStatus.ERROR,
                OutcomeStatus.NEEDS_REVIEW,
            }
            and not self.evidence_ids
        ):
            raise ValueError("non-passing outcome requires evidence")
        if self.status is not OutcomeStatus.NOT_EVALUATED and self.evaluated_at is None:
            raise ValueError("evaluated outcome requires evaluated_at")
        if self.status is OutcomeStatus.NOT_EVALUATED and self.evaluated_at is not None:
            raise ValueError("not_evaluated outcome cannot have evaluated_at")

    @classmethod
    def passed(cls, *, evidence_ids: tuple[UUID, ...] = ()) -> Self:
        return cls(
            status=OutcomeStatus.PASSED,
            code="passed",
            evidence_ids=evidence_ids,
            evaluated_at=datetime.now(UTC),
        )

    @classmethod
    def failed(cls, code: str, *, reason: str = "", evidence_ids: tuple[UUID, ...]) -> Self:
        return cls(
            status=OutcomeStatus.FAILED,
            code=code,
            reason=reason,
            evidence_ids=evidence_ids,
            evaluated_at=datetime.now(UTC),
        )

    @classmethod
    def error(cls, code: str, *, reason: str = "", evidence_ids: tuple[UUID, ...]) -> Self:
        return cls(
            status=OutcomeStatus.ERROR,
            code=code,
            reason=reason,
            evidence_ids=evidence_ids,
            evaluated_at=datetime.now(UTC),
        )

    @classmethod
    def needs_review(cls, code: str, *, reason: str = "", evidence_ids: tuple[UUID, ...]) -> Self:
        return cls(
            status=OutcomeStatus.NEEDS_REVIEW,
            code=code,
            reason=reason,
            evidence_ids=evidence_ids,
            evaluated_at=datetime.now(UTC),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "code": self.code,
            "reason": self.reason,
            "evidence_ids": [str(value) for value in self.evidence_ids],
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
        }

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> Self:
        raw_evaluated_at = value.get("evaluated_at")
        raw_evidence_ids = value.get("evidence_ids")
        return cls(
            status=OutcomeStatus(str(value.get("status") or "not_evaluated")),
            code=str(value.get("code") or ""),
            reason=str(value.get("reason") or ""),
            evidence_ids=tuple(UUID(str(item)) for item in raw_evidence_ids)
            if isinstance(raw_evidence_ids, list | tuple)
            else (),
            evaluated_at=(
                datetime.fromisoformat(str(raw_evaluated_at)) if raw_evaluated_at else None
            ),
        )


@dataclass(frozen=True, slots=True)
class RunCaseOutcomes:
    execution: Outcome
    assertion: Outcome
    quality: Outcome
    security: Outcome

    @classmethod
    def started(cls) -> RunCaseOutcomes:
        return cls(Outcome(), Outcome(), Outcome(), Outcome())

    def with_execution(self, value: Outcome) -> RunCaseOutcomes:
        return replace(self, execution=value)

    def with_assertion(self, value: Outcome) -> RunCaseOutcomes:
        return replace(self, assertion=value)

    def with_quality(self, value: Outcome) -> RunCaseOutcomes:
        return replace(self, quality=value)

    def with_security(self, value: Outcome) -> RunCaseOutcomes:
        return replace(self, security=value)

    @property
    def release_eligible(self) -> bool:
        return all(
            value.status
            not in {
                OutcomeStatus.FAILED,
                OutcomeStatus.ERROR,
                OutcomeStatus.NEEDS_REVIEW,
            }
            for value in (self.execution, self.assertion, self.quality, self.security)
        )

    @property
    def blocking_codes(self) -> tuple[str, ...]:
        return tuple(
            value.code
            for value in (self.execution, self.assertion, self.quality, self.security)
            if value.status
            in {OutcomeStatus.FAILED, OutcomeStatus.ERROR, OutcomeStatus.NEEDS_REVIEW}
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "execution": self.execution.to_dict(),
            "assertion": self.assertion.to_dict(),
            "quality": self.quality.to_dict(),
            "security": self.security.to_dict(),
        }

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> RunCaseOutcomes:
        def outcome(key: str) -> Outcome:
            raw = value.get(key)
            return Outcome.from_dict(raw) if isinstance(raw, dict) else Outcome()

        return cls(
            execution=outcome("execution"),
            assertion=outcome("assertion"),
            quality=outcome("quality"),
            security=outcome("security"),
        )
