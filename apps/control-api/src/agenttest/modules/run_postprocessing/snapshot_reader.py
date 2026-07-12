from __future__ import annotations

from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from agenttest.modules.gates.public import GateMetrics
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.run_postprocessing.stages import (
    PostprocessCaseSnapshot,
    PostprocessRunSnapshot,
)
from agenttest.modules.runs.public import Run, RunCase, RunId


class RunsReader(Protocol):
    async def get_by_id(self, project_id: ProjectId, run_id: RunId) -> Run | None: ...

    async def list_cases(self, project_id: ProjectId, run_id: RunId) -> list[RunCase]: ...


class RunPostprocessSnapshotReader:
    def __init__(self, runs: RunsReader) -> None:
        self._runs = runs

    async def load(self, project_id: UUID, run_id: UUID) -> PostprocessRunSnapshot:
        project = ProjectId(project_id)
        run_identifier = RunId(run_id)
        run = await self._runs.get_by_id(project, run_identifier)
        if run is None:
            raise LookupError("Run does not exist in project")
        cases = await self._runs.list_cases(project, run_identifier)
        snapshots = tuple(_case_snapshot(case) for case in cases)
        total = len(cases)
        passed = sum(case.status.value == "passed" for case in cases)
        evidence_complete = sum(bool(case.evidence) for case in cases)
        security_findings = sum(
            case.outcomes.security.status.value in {"failed", "error"} for case in cases
        )
        return PostprocessRunSnapshot(
            project_id=project_id,
            run_id=run_id,
            cases=snapshots,
            calibration_predicted=(),
            calibration_actual=(),
            gate_metrics=GateMetrics(
                critical_success_rate=passed / total if total else 0.0,
                quality_delta=0.0,
                critical_security_findings=security_findings,
                novel_failure_clusters=0,
                flake_rate=0.0,
                evidence_completeness=evidence_complete / total if total else 0.0,
                calibrated=False,
                latency_delta=0.0,
                cost_delta=0.0,
            ),
        )


def _case_snapshot(case: RunCase) -> PostprocessCaseSnapshot:
    evidence_id = uuid5(NAMESPACE_URL, f"agenttest:run-case-evidence:{case.run_case_id.value}")
    error_code = next(iter(case.outcomes.blocking_codes), None)
    if not error_code:
        error_code = _normalize_error_type(case.error_type)
    tool_chain = tuple(
        str(item.get("name")) for item in case.trace if isinstance(item, dict) and item.get("name")
    )
    return PostprocessCaseSnapshot(
        run_case_id=case.run_case_id.value,
        status=case.status.value,
        error_code=error_code,
        input_snapshot=dict(case.input_snapshot),
        tool_chain=tool_chain,
        evidence_view=(
            {
                "id": str(evidence_id),
                "kind": "run_case_evidence",
                "run_case_id": str(case.run_case_id.value),
                "status": case.status.value,
                "error_code": error_code,
                "outcomes": case.outcomes.to_dict(),
            },
        )
        if case.evidence
        else (),
    )


def _normalize_error_type(value: str | None) -> str:
    if not value:
        return "insufficient_evidence"
    normalized = value.strip().lower()
    aliases = {
        "assertionerror": "assertion_mismatch",
        "activityerror": "temporal_unavailable",
        "timeouterror": "network_unavailable",
    }
    return aliases.get(normalized, normalized)
