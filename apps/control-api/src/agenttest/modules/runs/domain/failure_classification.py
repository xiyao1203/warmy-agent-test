from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class FailureClass(StrEnum):
    TARGET = "target_failure"
    TEST = "test_failure"
    ENVIRONMENT = "environment_failure"
    PLATFORM = "platform_failure"
    EVALUATION = "evaluation_failure"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class FailureClassification:
    failure_class: FailureClass
    code: str
    confidence: float
    evidence_ids: tuple[UUID, ...] = ()
    source: str = "deterministic_rule"

    @property
    def requires_diagnosis(self) -> bool:
        return self.failure_class is FailureClass.UNKNOWN or self.confidence < 1.0
