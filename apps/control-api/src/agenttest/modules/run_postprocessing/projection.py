from __future__ import annotations

from agenttest.modules.run_postprocessing.domain import (
    PostprocessStage,
    RunPostprocessJob,
)


class TrustLoopProjection:
    @staticmethod
    def build(job: RunPostprocessJob) -> dict[str, object]:
        results = {result.stage: result for result in job.stage_results}
        outputs = {stage: result.output for stage, result in results.items()}
        diagnostics = outputs.get(PostprocessStage.DIAGNOSE)
        diagnostic_result = results.get(PostprocessStage.DIAGNOSE)
        if diagnostics is None or (
            diagnostic_result is not None and diagnostic_result.status != "completed"
        ):
            diagnostics = {"status": "inconclusive", "items": []}
        elif isinstance(diagnostics, dict) and "status" not in diagnostics:
            diagnostics = {"status": "completed", **diagnostics}
        regressions = outputs.get(PostprocessStage.REPRODUCE, {}).get("items", [])
        calibration = outputs.get(
            PostprocessStage.CALIBRATE, {"status": "inconclusive", "metrics": {}}
        )
        gate = outputs.get(PostprocessStage.EVALUATE_GATE)
        return {
            "job_id": str(job.job_id),
            "project_id": str(job.project_id),
            "run_id": str(job.run_id),
            "pipeline_version": job.pipeline_version,
            "status": job.status.value,
            "current_stage": job.current_stage.value if job.current_stage else None,
            "classifications": outputs.get(PostprocessStage.CLASSIFY, {}).get("items", []),
            "diagnostics": diagnostics,
            "regressions": regressions,
            "calibration": calibration,
            "joint_gate": gate,
            "warning_codes": list(job.warning_codes),
            "error_type": job.error_type,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
