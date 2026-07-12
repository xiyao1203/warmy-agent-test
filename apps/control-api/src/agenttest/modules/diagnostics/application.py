from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol
from uuid import UUID

from agenttest.modules.diagnostics.domain import (
    DiagnosticHypothesis,
    DiagnosticProposal,
    DiagnosticResult,
)
from agenttest.modules.runs.public import FailureClass


class DiagnosticModel(Protocol):
    async def propose(self, evidence_view: tuple[dict[str, object], ...]) -> DiagnosticProposal: ...


class DiagnosticService:
    def __init__(self, model: DiagnosticModel) -> None:
        self._model = model

    async def diagnose(self, evidence_view: tuple[dict[str, object], ...]) -> DiagnosticResult:
        allowed_ids = {
            UUID(str(item["id"]))
            for item in evidence_view
            if isinstance(item, Mapping) and item.get("id")
        }
        if not allowed_ids:
            return DiagnosticResult("inconclusive", (), "No admissible evidence")
        proposal = await self._model.propose(evidence_view)
        if not proposal.evidence_ids:
            return DiagnosticResult("inconclusive", (), "Diagnosis has no evidence citations")
        if not set(proposal.evidence_ids).issubset(allowed_ids):
            return DiagnosticResult("inconclusive", (), "Diagnosis cites unknown evidence")
        if not 0 <= proposal.confidence <= 1:
            return DiagnosticResult("inconclusive", (), "Diagnosis confidence is invalid")
        try:
            failure_class = FailureClass(proposal.failure_class)
        except ValueError:
            return DiagnosticResult("inconclusive", (), "Diagnosis class is invalid")
        hypothesis = DiagnosticHypothesis(
            summary=proposal.summary.strip(),
            failure_class=failure_class,
            confidence=proposal.confidence,
            evidence_ids=proposal.evidence_ids,
            counterevidence=proposal.counterevidence,
            verification_steps=proposal.verification_steps,
        )
        if not hypothesis.summary or not hypothesis.verification_steps:
            return DiagnosticResult("inconclusive", (), "Diagnosis is incomplete")
        return DiagnosticResult("completed", (hypothesis,))
