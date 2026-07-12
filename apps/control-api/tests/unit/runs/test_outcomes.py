from datetime import UTC, datetime
from uuid import uuid4

import pytest
from agenttest.modules.runs.domain.outcomes import (
    Outcome,
    OutcomeStatus,
    RunCaseOutcomes,
)


def test_technical_success_does_not_override_security_failure() -> None:
    evidence_id = uuid4()
    outcomes = RunCaseOutcomes.started().with_execution(
        Outcome.passed()
    ).with_security(
        Outcome.failed("critical_finding", evidence_ids=(evidence_id,))
    )

    assert outcomes.execution.status is OutcomeStatus.PASSED
    assert outcomes.security.status is OutcomeStatus.FAILED
    assert outcomes.release_eligible is False
    assert outcomes.blocking_codes == ("critical_finding",)


def test_evaluated_outcome_requires_evidence_for_failure() -> None:
    with pytest.raises(ValueError, match="evidence"):
        Outcome(
            status=OutcomeStatus.FAILED,
            code="assertion_mismatch",
            reason="expected value differs",
            evidence_ids=(),
            evaluated_at=datetime.now(UTC),
        )


def test_outcomes_round_trip_without_losing_independent_statuses() -> None:
    evidence_id = uuid4()
    original = RunCaseOutcomes.started().with_execution(
        Outcome.passed(evidence_ids=(evidence_id,))
    ).with_assertion(
        Outcome.needs_review("insufficient_assertion_evidence", evidence_ids=(evidence_id,))
    )

    restored = RunCaseOutcomes.from_dict(original.to_dict())

    assert restored == original
    assert restored.assertion.status is OutcomeStatus.NEEDS_REVIEW
    assert restored.quality.status is OutcomeStatus.NOT_EVALUATED
