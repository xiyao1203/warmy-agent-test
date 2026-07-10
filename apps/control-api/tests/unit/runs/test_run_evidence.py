from __future__ import annotations

import pytest
from agenttest.modules.runs.domain.evidence import (
    ExecutionOutcome,
    QualityDecision,
    RunCaseEvidence,
    RunCaseStage,
    RunCaseStageEvent,
    SecurityDecision,
)


def test_evidence_round_trips_safe_payload() -> None:
    evidence = RunCaseEvidence.from_payload(
        {
            "execution_outcome": "success",
            "quality_decision": "pass",
            "security_decision": "clear",
            "canvas": {"nodes": [{"id": "node-1"}], "connections": []},
            "artifacts": [{"key": "projects/p1/runs/r1/screenshot.png"}],
            "trace": {"trace_id": "trace-1"},
        }
    )

    assert evidence.execution_outcome is ExecutionOutcome.SUCCESS
    assert evidence.quality_decision is QualityDecision.PASS
    assert evidence.security_decision is SecurityDecision.CLEAR
    assert evidence.to_dict()["canvas"] == {
        "nodes": [{"id": "node-1"}],
        "connections": [],
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"password": "secret"},
        {"canvas": {"authorization": "Bearer secret"}},
        {"artifacts": [{"cookie": "session=secret"}]},
        {"trace": {"api_key": "secret"}},
    ],
)
def test_evidence_rejects_sensitive_fields(payload: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="sensitive"):
        RunCaseEvidence.from_payload(payload)


def test_stage_event_validates_attempt_and_payload() -> None:
    event = RunCaseStageEvent.create(
        project_id="project-1",
        run_id="run-1",
        run_case_id="case-1",
        attempt=2,
        stage="executing",
        status="running",
        payload={"step": "submit"},
    )

    assert event.stage is RunCaseStage.EXECUTING
    assert event.attempt == 2

    with pytest.raises(ValueError, match="attempt"):
        RunCaseStageEvent.create(
            project_id="project-1",
            run_id="run-1",
            run_case_id="case-1",
            attempt=0,
            stage="executing",
            status="running",
        )
