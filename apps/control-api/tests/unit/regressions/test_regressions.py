from uuid import uuid4

import pytest
from agenttest.modules.regressions.domain import (
    RegressionCandidate,
    RegressionState,
    ReproductionRequiredError,
)
from agenttest.modules.regressions.fingerprints import fingerprint_failure
from agenttest.modules.regressions.minimizer import FailureMinimizer


def snapshot() -> dict[str, object]:
    return {
        "error_code": "target_product_error",
        "tool_chain": ["open", "submit"],
        "input": {"prompt": "create image", "irrelevant": "remove me"},
    }


def test_fingerprint_ignores_non_semantic_ordering() -> None:
    first = fingerprint_failure(snapshot())
    second = fingerprint_failure(
        {
            "input": {"irrelevant": "remove me", "prompt": "create image"},
            "tool_chain": ["open", "submit"],
            "error_code": "target_product_error",
        }
    )
    assert first == second


def test_candidate_cannot_publish_before_reproduction() -> None:
    candidate = RegressionCandidate.draft(uuid4(), snapshot())
    with pytest.raises(ReproductionRequiredError):
        candidate.publish()


def test_candidate_publishes_only_after_matching_reproduction() -> None:
    candidate = RegressionCandidate.draft(uuid4(), snapshot())
    candidate.start_reproduction()
    first_evidence = uuid4()
    candidate.record_reproduction(
        reproduced=True,
        observed_fingerprint=candidate.fingerprint,
        evidence_ids=(first_evidence,),
    )

    assert candidate.state is RegressionState.REPRODUCING
    with pytest.raises(ReproductionRequiredError):
        candidate.publish()

    candidate.record_reproduction(
        reproduced=True,
        observed_fingerprint=candidate.fingerprint,
        evidence_ids=(uuid4(),),
    )
    candidate.publish()
    assert candidate.state is RegressionState.PUBLISHED


def test_duplicate_reproduction_evidence_does_not_count_as_independent() -> None:
    candidate = RegressionCandidate.draft(uuid4(), snapshot())
    candidate.start_reproduction()
    evidence_id = uuid4()

    candidate.record_reproduction(
        reproduced=True,
        observed_fingerprint=candidate.fingerprint,
        evidence_ids=(evidence_id,),
    )
    candidate.record_reproduction(
        reproduced=True,
        observed_fingerprint=candidate.fingerprint,
        evidence_ids=(evidence_id,),
    )

    assert candidate.state is RegressionState.REPRODUCING
    assert candidate.reproduction_evidence_ids == (evidence_id,)


@pytest.mark.asyncio
async def test_minimizer_removes_irrelevant_fields_within_budget() -> None:
    expected = fingerprint_failure(snapshot())

    async def reproduce(value: dict[str, object]) -> str | None:
        input_value = value.get("input")
        if isinstance(input_value, dict) and input_value.get("prompt") == "create image":
            return expected
        return None

    result = await FailureMinimizer(max_attempts=10).minimize(snapshot(), reproduce)
    assert result["input"] == {"prompt": "create image"}
