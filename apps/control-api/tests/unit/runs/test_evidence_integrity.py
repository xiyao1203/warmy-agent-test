from uuid import uuid4

import pytest
from agenttest.modules.runs.application.evidence_service import (
    EvidenceIntegrityError,
    EvidenceService,
)
from agenttest.modules.runs.domain.evidence import EvidenceEnvelope, EvidenceScope


def scope() -> EvidenceScope:
    return EvidenceScope(
        project_id=uuid4(),
        run_id=uuid4(),
        run_case_id=uuid4(),
        attempt=1,
        stage="executing",
    )


def test_evidence_hash_is_stable_for_equivalent_payloads() -> None:
    evidence_scope = scope()
    first = EvidenceEnvelope.create(
        kind="http",
        producer="api-runner@1",
        scope=evidence_scope,
        payload={"status": 200, "headers": {"content-type": "application/json"}},
    )
    second = EvidenceEnvelope.create(
        kind="http",
        producer="api-runner@1",
        scope=evidence_scope,
        payload={"headers": {"content-type": "application/json"}, "status": 200},
        evidence_id=first.evidence_id,
        created_at=first.created_at,
    )

    assert first.content_hash == second.content_hash


def test_evidence_rejects_unredacted_secret() -> None:
    with pytest.raises(ValueError, match="sensitive"):
        EvidenceEnvelope.create(
            kind="http",
            producer="api-runner@1",
            scope=scope(),
            payload={"authorization": "synthetic-secret"},
        )


def test_service_rejects_hash_and_scope_tampering() -> None:
    envelope = EvidenceEnvelope.create(
        kind="browser",
        producer="browser-worker@1",
        scope=scope(),
        payload={"url": "https://target.test/chat", "status": "completed"},
    )
    service = EvidenceService()

    with pytest.raises(EvidenceIntegrityError, match="hash"):
        service.accept(envelope.with_content_hash("0" * 64), expected_scope=envelope.scope)

    with pytest.raises(EvidenceIntegrityError, match="scope"):
        service.accept(envelope, expected_scope=scope())
