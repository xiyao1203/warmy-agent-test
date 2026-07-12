from uuid import UUID, uuid4

import pytest
from agenttest.modules.gates.application.joint_gate import GateMetrics
from agenttest.modules.run_postprocessing.domain import PostprocessStage
from agenttest.modules.run_postprocessing.stages import (
    PostprocessCaseSnapshot,
    PostprocessRunSnapshot,
    PostprocessStageService,
    ReproductionObservation,
)


class Reader:
    def __init__(self, snapshot: PostprocessRunSnapshot) -> None:
        self.snapshot = snapshot

    async def load(self, project_id: UUID, run_id: UUID) -> PostprocessRunSnapshot:
        assert project_id == self.snapshot.project_id
        assert run_id == self.snapshot.run_id
        return self.snapshot


class Reproducer:
    async def reproduce(
        self, case: PostprocessCaseSnapshot, fingerprint: str
    ) -> tuple[ReproductionObservation, ...]:
        return (
            ReproductionObservation(True, fingerprint, (uuid4(),)),
            ReproductionObservation(True, fingerprint, (uuid4(),)),
        )


def snapshot(*, evidence_complete: float = 1.0) -> PostprocessRunSnapshot:
    project_id = uuid4()
    run_id = uuid4()
    evidence_id = uuid4()
    return PostprocessRunSnapshot(
        project_id=project_id,
        run_id=run_id,
        cases=(
            PostprocessCaseSnapshot(
                run_case_id=uuid4(),
                status="failed",
                error_code="target_5xx",
                input_snapshot={"prompt": "hello"},
                tool_chain=("http",),
                evidence_view=(
                    {
                        "id": str(evidence_id),
                        "kind": "http",
                        "error_code": "target_5xx",
                    },
                ),
            ),
        ),
        calibration_predicted=(True, False, True, False),
        calibration_actual=(True, False, False, False),
        gate_metrics=GateMetrics(
            critical_success_rate=1.0,
            quality_delta=0.5,
            critical_security_findings=0,
            novel_failure_clusters=0,
            flake_rate=0.0,
            evidence_completeness=evidence_complete,
            calibrated=True,
            latency_delta=0.0,
            cost_delta=0.0,
        ),
    )


@pytest.mark.asyncio
async def test_classify_stage_produces_stable_evidence_bound_failure_class() -> None:
    value = snapshot()
    result = await PostprocessStageService(Reader(value)).execute(
        value.project_id, value.run_id, PostprocessStage.CLASSIFY
    )

    assert result.status == "completed"
    assert result.output["items"][0]["failure_class"] == "target_failure"
    assert result.output["items"][0]["evidence_ids"]


@pytest.mark.asyncio
async def test_diagnose_stage_without_model_is_explicitly_inconclusive() -> None:
    value = snapshot()
    result = await PostprocessStageService(Reader(value)).execute(
        value.project_id, value.run_id, PostprocessStage.DIAGNOSE
    )

    assert result.status == "warning"
    assert result.warning_code == "diagnostic_model_unavailable"
    assert result.output["items"][0]["status"] == "inconclusive"


@pytest.mark.asyncio
async def test_reproduce_stage_quarantines_without_runtime() -> None:
    value = snapshot()
    result = await PostprocessStageService(Reader(value)).execute(
        value.project_id, value.run_id, PostprocessStage.REPRODUCE
    )

    assert result.status == "warning"
    assert result.warning_code == "reproducer_unavailable"
    assert result.output["items"][0]["state"] == "quarantined"


@pytest.mark.asyncio
async def test_reproduce_stage_publishes_only_after_two_independent_matches() -> None:
    value = snapshot()
    result = await PostprocessStageService(Reader(value), reproducer=Reproducer()).execute(
        value.project_id, value.run_id, PostprocessStage.REPRODUCE
    )

    assert result.status == "completed"
    assert result.output["items"][0]["state"] == "published"
    assert result.output["items"][0]["reproduction_count"] == 2


@pytest.mark.asyncio
async def test_calibration_and_gate_remain_non_compensating() -> None:
    value = snapshot(evidence_complete=0.5)
    service = PostprocessStageService(Reader(value))

    calibration = await service.execute(value.project_id, value.run_id, PostprocessStage.CALIBRATE)
    gate = await service.execute(value.project_id, value.run_id, PostprocessStage.EVALUATE_GATE)

    assert calibration.output["metrics"]["accuracy"] == 0.75
    assert gate.output["decision"] == "block"
    assert gate.output["rules"][0]["code"] == "evidence_completeness"
