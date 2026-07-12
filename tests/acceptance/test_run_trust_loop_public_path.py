from __future__ import annotations

import runpy
from pathlib import Path

import pytest

validate_trust_loop_payload = runpy.run_path(
    Path(__file__).parents[2] / "scripts" / "run_mission_acceptance.py",
    run_name="trust_loop_acceptance_test",
)["validate_trust_loop_payload"]


@pytest.mark.parametrize(
    ("scenario", "failure_class", "gate_decision"),
    [
        ("success", None, "needs_review"),
        ("product_error", "target_failure", "block"),
        ("protocol_error", "target_failure", "block"),
        ("auth_expired", "environment_failure", "block"),
        ("quota_exceeded", "environment_failure", "block"),
        ("timeout", "environment_failure", "block"),
        ("transient_failure", None, "needs_review"),
        ("incomplete_artifact", None, "block"),
        ("prompt_injection", None, "block"),
    ],
)
def test_public_projection_matrix(
    scenario: str,
    failure_class: str | None,
    gate_decision: str,
) -> None:
    classifications = (
        [] if failure_class is None else [{"failure_class": failure_class, "code": "stable-code"}]
    )
    case_items = []
    if scenario == "transient_failure":
        case_items = [{"status": "passed"}]
    elif scenario == "prompt_injection":
        case_items = [{"status": "passed", "security_summary": {"decision": "blocked"}}]
    validate_trust_loop_payload(
        scenario=scenario,
        run={"id": "run-1", "status": "passed" if failure_class is None else "error"},
        cases={"items": case_items},
        summary={
            "job_id": "job-1",
            "run_id": "run-1",
            "status": "completed_with_warnings",
            "classifications": classifications,
            "warning_codes": ["diagnostic_model_unavailable"],
        },
        diagnostics={"items": [], "total": 0},
        regressions={
            "items": [
                {
                    "status": "quarantined",
                    "reproduction_count": 0,
                }
            ]
            if failure_class == "target_failure"
            else [],
            "total": 1 if failure_class == "target_failure" else 0,
        },
        calibration={"status": "inconclusive", "metrics": {}},
        gate={"status": "completed", "decision": gate_decision, "rules": []},
    )


def test_public_projection_rejects_unreproduced_publication() -> None:
    with pytest.raises(AssertionError, match="two independent reproductions"):
        validate_trust_loop_payload(
            scenario="product_error",
            run={"id": "run-1", "status": "error"},
            cases={"items": []},
            summary={
                "job_id": "job-1",
                "run_id": "run-1",
                "status": "completed",
                "classifications": [{"failure_class": "target_failure"}],
                "warning_codes": [],
            },
            diagnostics={"items": [], "total": 0},
            regressions={
                "items": [{"status": "published", "reproduction_count": 1}],
                "total": 1,
            },
            calibration={"status": "inconclusive", "metrics": {}},
            gate={"status": "completed", "decision": "block", "rules": []},
        )
