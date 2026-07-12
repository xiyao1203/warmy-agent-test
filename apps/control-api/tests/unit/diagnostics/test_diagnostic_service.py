from uuid import uuid4

import pytest
from agenttest.modules.diagnostics.application import DiagnosticService
from agenttest.modules.diagnostics.domain import DiagnosticProposal


class Model:
    def __init__(self, proposal: DiagnosticProposal) -> None:
        self.proposal = proposal

    async def propose(self, evidence_view: tuple[dict[str, object], ...]) -> DiagnosticProposal:
        return self.proposal


@pytest.mark.asyncio
async def test_diagnosis_without_citations_is_inconclusive() -> None:
    service = DiagnosticService(
        Model(
            DiagnosticProposal(
                summary="Target failed",
                failure_class="target_failure",
                confidence=0.9,
                evidence_ids=(),
                counterevidence=(),
                verification_steps=("retry",),
            )
        )
    )

    result = await service.diagnose(({"id": str(uuid4()), "kind": "http"},))

    assert result.status == "inconclusive"
    assert result.hypotheses == ()


@pytest.mark.asyncio
async def test_diagnosis_rejects_unknown_evidence_citations() -> None:
    unknown = uuid4()
    service = DiagnosticService(
        Model(
            DiagnosticProposal(
                summary="Platform callback failed",
                failure_class="platform_failure",
                confidence=0.8,
                evidence_ids=(unknown,),
                counterevidence=(),
                verification_steps=("inspect callback",),
            )
        )
    )

    result = await service.diagnose(({"id": str(uuid4()), "kind": "callback"},))

    assert result.status == "inconclusive"


@pytest.mark.asyncio
async def test_diagnosis_accepts_evidence_bounded_hypothesis() -> None:
    evidence_id = uuid4()
    service = DiagnosticService(
        Model(
            DiagnosticProposal(
                summary="Authentication expired",
                failure_class="environment_failure",
                confidence=0.95,
                evidence_ids=(evidence_id,),
                counterevidence=("Target health endpoint is reachable",),
                verification_steps=("renew browser profile",),
            )
        )
    )

    result = await service.diagnose(
        ({"id": str(evidence_id), "kind": "http", "error_code": "auth_expired"},)
    )

    assert result.status == "completed"
    assert result.hypotheses[0].evidence_ids == (evidence_id,)
