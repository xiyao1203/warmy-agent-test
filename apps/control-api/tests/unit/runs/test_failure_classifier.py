import pytest
from agenttest.modules.runs.application.failure_classifier import FailureClassifier
from agenttest.modules.runs.domain.failure_classification import FailureClass


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("auth_expired", FailureClass.ENVIRONMENT),
        ("quota_exceeded", FailureClass.ENVIRONMENT),
        ("assertion_mismatch", FailureClass.TEST),
        ("selector_not_found", FailureClass.TEST),
        ("target_5xx", FailureClass.TARGET),
        ("target_product_error", FailureClass.TARGET),
        ("artifact_upload_failed", FailureClass.PLATFORM),
        ("temporal_unavailable", FailureClass.PLATFORM),
        ("scorer_unavailable", FailureClass.EVALUATION),
        ("evaluation_conflict", FailureClass.EVALUATION),
    ],
)
def test_failure_codes_are_stably_classified(code: str, expected: FailureClass) -> None:
    result = FailureClassifier().classify_code(code)

    assert result.failure_class is expected
    assert result.confidence == 1.0
    assert result.source == "deterministic_rule"


def test_unknown_code_remains_unclassified() -> None:
    result = FailureClassifier().classify_code("new_vendor_failure")

    assert result.failure_class is FailureClass.UNKNOWN
    assert result.confidence == 0.0
    assert result.requires_diagnosis is True
