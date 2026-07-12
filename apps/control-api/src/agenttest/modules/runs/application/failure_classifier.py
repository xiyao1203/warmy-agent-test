from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from agenttest.modules.runs.domain.failure_classification import (
    FailureClass,
    FailureClassification,
)


class FailureClassifier:
    _EXACT_RULES: Mapping[str, FailureClass] = {
        "auth_expired": FailureClass.ENVIRONMENT,
        "quota_exceeded": FailureClass.ENVIRONMENT,
        "rate_limited": FailureClass.ENVIRONMENT,
        "network_unavailable": FailureClass.ENVIRONMENT,
        "assertion_mismatch": FailureClass.TEST,
        "selector_not_found": FailureClass.TEST,
        "invalid_test_data": FailureClass.TEST,
        "target_5xx": FailureClass.TARGET,
        "target_product_error": FailureClass.TARGET,
        "target_protocol_error": FailureClass.TARGET,
        "artifact_upload_failed": FailureClass.PLATFORM,
        "temporal_unavailable": FailureClass.PLATFORM,
        "callback_failed": FailureClass.PLATFORM,
        "scorer_unavailable": FailureClass.EVALUATION,
        "evaluation_conflict": FailureClass.EVALUATION,
        "insufficient_evidence": FailureClass.EVALUATION,
    }

    def classify_code(
        self, code: str, *, evidence_ids: tuple[UUID, ...] = ()
    ) -> FailureClassification:
        normalized = code.strip().lower()
        failure_class = self._EXACT_RULES.get(normalized, FailureClass.UNKNOWN)
        return FailureClassification(
            failure_class=failure_class,
            code=normalized,
            confidence=1.0 if failure_class is not FailureClass.UNKNOWN else 0.0,
            evidence_ids=evidence_ids,
            source="deterministic_rule" if failure_class is not FailureClass.UNKNOWN else "none",
        )
