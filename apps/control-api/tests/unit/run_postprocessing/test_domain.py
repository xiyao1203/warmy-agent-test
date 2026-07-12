from uuid import uuid4

import pytest
from agenttest.modules.run_postprocessing.domain import (
    PostprocessStage,
    PostprocessStatus,
    RunPostprocessJob,
)


def new_job() -> RunPostprocessJob:
    return RunPostprocessJob.create(uuid4(), uuid4(), "trust-loop-v1")


def test_job_advances_through_the_fixed_stage_order() -> None:
    job = new_job()
    job.start("run-trust-loop-workflow")

    for stage in PostprocessStage:
        job.begin_stage(stage)
        job.complete_stage(stage, {"stage": stage.value})

    assert job.status is PostprocessStatus.COMPLETED
    assert job.current_stage is PostprocessStage.FINALIZE
    assert [result.stage for result in job.stage_results] == list(PostprocessStage)


def test_job_rejects_an_out_of_order_stage() -> None:
    job = new_job()
    job.start("run-trust-loop-workflow")

    with pytest.raises(ValueError, match="Expected stage classify"):
        job.begin_stage(PostprocessStage.DIAGNOSE)


def test_optional_stage_failure_records_warning_and_continues() -> None:
    job = new_job()
    job.start("run-trust-loop-workflow")
    job.begin_stage(PostprocessStage.CLASSIFY)
    job.complete_stage(PostprocessStage.CLASSIFY, {})
    job.begin_stage(PostprocessStage.DIAGNOSE)

    job.fail_stage(
        PostprocessStage.DIAGNOSE,
        "model_unavailable",
        "diagnosis unavailable",
        required=False,
    )

    assert job.status is PostprocessStatus.RUNNING
    assert job.warning_codes == ["model_unavailable"]
    job.begin_stage(PostprocessStage.REPRODUCE)


def test_required_stage_failure_is_terminal_without_changing_run() -> None:
    job = new_job()
    job.start("run-trust-loop-workflow")
    job.begin_stage(PostprocessStage.CLASSIFY)

    job.fail_stage(
        PostprocessStage.CLASSIFY,
        "persistence_failed",
        "classification could not be stored",
        required=True,
    )

    assert job.status is PostprocessStatus.FAILED
    assert job.error_type == "persistence_failed"
    with pytest.raises(ValueError, match="terminal"):
        job.begin_stage(PostprocessStage.DIAGNOSE)


def test_job_finishes_with_warnings_after_optional_degradation() -> None:
    job = new_job()
    job.start("run-trust-loop-workflow")
    for stage in PostprocessStage:
        job.begin_stage(stage)
        if stage is PostprocessStage.DIAGNOSE:
            job.fail_stage(stage, "model_unavailable", "no quota", required=False)
        else:
            job.complete_stage(stage, {})

    assert job.status is PostprocessStatus.COMPLETED_WITH_WARNINGS
