from uuid import uuid4

from agenttest.modules.run_postprocessing.domain import PostprocessStage, RunPostprocessJob
from agenttest.modules.run_postprocessing.projection import TrustLoopProjection


def test_projection_keeps_missing_optional_results_explicit() -> None:
    job = RunPostprocessJob.create(uuid4(), uuid4(), "trust-loop-v1")
    job.start("workflow-1")
    job.begin_stage(PostprocessStage.CLASSIFY)
    job.complete_stage(
        PostprocessStage.CLASSIFY,
        {"items": [{"run_case_id": str(uuid4()), "failure_class": "target_failure"}]},
    )
    job.begin_stage(PostprocessStage.DIAGNOSE)
    job.fail_stage(
        PostprocessStage.DIAGNOSE,
        "diagnostic_model_unavailable",
        "model unavailable",
        required=False,
    )

    result = TrustLoopProjection.build(job)

    assert result["status"] == "running"
    assert result["current_stage"] == "diagnose"
    assert result["diagnostics"]["status"] == "inconclusive"
    assert result["regressions"] == []
    assert result["warning_codes"] == ["diagnostic_model_unavailable"]
