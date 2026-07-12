from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4

from agenttest.modules.regressions.fingerprints import fingerprint_failure


class RegressionState(StrEnum):
    DRAFT = "draft"
    REPRODUCING = "reproducing"
    VERIFIED = "verified"
    PUBLISHED = "published"
    QUARANTINED = "quarantined"


class ReproductionRequiredError(ValueError):
    pass


@dataclass(slots=True)
class RegressionCandidate:
    candidate_id: UUID
    source_run_case_id: UUID
    failure_snapshot: dict[str, object]
    fingerprint: str
    state: RegressionState = RegressionState.DRAFT
    reproduction_evidence_ids: tuple[UUID, ...] = ()
    reproduction_attempts: tuple[tuple[UUID, ...], ...] = ()
    quarantine_reason: str = ""

    @classmethod
    def draft(
        cls, source_run_case_id: UUID, failure_snapshot: dict[str, object]
    ) -> RegressionCandidate:
        return cls(
            candidate_id=uuid4(),
            source_run_case_id=source_run_case_id,
            failure_snapshot=dict(failure_snapshot),
            fingerprint=fingerprint_failure(failure_snapshot),
        )

    def start_reproduction(self) -> None:
        if self.state is not RegressionState.DRAFT:
            raise ValueError("only draft regression candidates can reproduce")
        self.state = RegressionState.REPRODUCING

    def record_reproduction(
        self,
        *,
        reproduced: bool,
        observed_fingerprint: str | None,
        evidence_ids: tuple[UUID, ...],
    ) -> None:
        if self.state is not RegressionState.REPRODUCING:
            raise ValueError("candidate is not reproducing")
        if reproduced and observed_fingerprint == self.fingerprint and evidence_ids:
            known = set(self.reproduction_evidence_ids)
            if known.intersection(evidence_ids):
                return
            self.reproduction_attempts += (evidence_ids,)
            self.reproduction_evidence_ids += evidence_ids
            if len(self.reproduction_attempts) >= 2:
                self.state = RegressionState.VERIFIED
            return
        self.state = RegressionState.QUARANTINED
        self.quarantine_reason = "failure could not be reproduced with the same fingerprint"

    def publish(self) -> None:
        if self.state is not RegressionState.VERIFIED:
            raise ReproductionRequiredError("regression must reproduce before publication")
        self.state = RegressionState.PUBLISHED
