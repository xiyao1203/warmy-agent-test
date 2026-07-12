from __future__ import annotations

from agenttest.modules.runs.domain.evidence import EvidenceEnvelope, EvidenceScope


class EvidenceIntegrityError(ValueError):
    pass


class EvidenceService:
    def accept(
        self, envelope: EvidenceEnvelope, *, expected_scope: EvidenceScope
    ) -> EvidenceEnvelope:
        if envelope.scope != expected_scope:
            raise EvidenceIntegrityError("evidence scope does not match expected run case")
        if not envelope.redacted:
            raise EvidenceIntegrityError("evidence is not marked as redacted")
        if not envelope.verify_hash():
            raise EvidenceIntegrityError("evidence content hash is invalid")
        return envelope
