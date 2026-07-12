from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from agenttest.modules.runs.public import FailureClass


@dataclass(frozen=True, slots=True)
class DiagnosticProposal:
    summary: str
    failure_class: str
    confidence: float
    evidence_ids: tuple[UUID, ...]
    counterevidence: tuple[str, ...]
    verification_steps: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DiagnosticHypothesis:
    summary: str
    failure_class: FailureClass
    confidence: float
    evidence_ids: tuple[UUID, ...]
    counterevidence: tuple[str, ...]
    verification_steps: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DiagnosticResult:
    status: str
    hypotheses: tuple[DiagnosticHypothesis, ...]
    reason: str = ""
