from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol
from uuid import UUID

from agenttest.modules.diagnostics.public import DiagnosticModel, DiagnosticService
from agenttest.modules.gates.public import GateMetrics, JointGate
from agenttest.modules.regressions.public import RegressionCandidate
from agenttest.modules.run_postprocessing.domain import PostprocessStage
from agenttest.modules.runs.public import FailureClass, FailureClassifier
from agenttest.modules.scorers.public import CalibrationMetrics


@dataclass(frozen=True, slots=True)
class PostprocessCaseSnapshot:
    run_case_id: UUID
    status: str
    error_code: str
    input_snapshot: dict[str, object]
    tool_chain: tuple[str, ...]
    evidence_view: tuple[dict[str, object], ...]


@dataclass(frozen=True, slots=True)
class PostprocessRunSnapshot:
    project_id: UUID
    run_id: UUID
    cases: tuple[PostprocessCaseSnapshot, ...]
    calibration_predicted: tuple[bool, ...]
    calibration_actual: tuple[bool, ...]
    gate_metrics: GateMetrics


@dataclass(frozen=True, slots=True)
class ReproductionObservation:
    reproduced: bool
    fingerprint: str | None
    evidence_ids: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class StageExecution:
    status: str
    output: dict[str, object]
    warning_code: str | None = None


class PostprocessSnapshotReader(Protocol):
    async def load(self, project_id: UUID, run_id: UUID) -> PostprocessRunSnapshot: ...


class RegressionReproducer(Protocol):
    async def reproduce(
        self, case: PostprocessCaseSnapshot, fingerprint: str
    ) -> tuple[ReproductionObservation, ...]: ...


class PostprocessStageService:
    def __init__(
        self,
        reader: PostprocessSnapshotReader,
        *,
        diagnostic_model: DiagnosticModel | None = None,
        reproducer: RegressionReproducer | None = None,
    ) -> None:
        self._reader = reader
        self._diagnostic_model = diagnostic_model
        self._reproducer = reproducer
        self._classifier = FailureClassifier()

    async def execute(
        self, project_id: UUID, run_id: UUID, stage: PostprocessStage
    ) -> StageExecution:
        snapshot = await self._reader.load(project_id, run_id)
        if snapshot.project_id != project_id or snapshot.run_id != run_id:
            raise LookupError("Run postprocess scope does not match")
        if stage is PostprocessStage.CLASSIFY:
            return self._classify(snapshot)
        if stage is PostprocessStage.DIAGNOSE:
            return await self._diagnose(snapshot)
        if stage is PostprocessStage.REPRODUCE:
            return await self._reproduce(snapshot)
        if stage is PostprocessStage.CALIBRATE:
            return self._calibrate(snapshot)
        if stage is PostprocessStage.EVALUATE_GATE:
            return self._gate(snapshot)
        if stage is PostprocessStage.FINALIZE:
            return StageExecution("completed", {"finalized": True})
        raise ValueError("Unsupported postprocess stage")

    def _classify(self, snapshot: PostprocessRunSnapshot) -> StageExecution:
        items = []
        for case in self._failed_cases(snapshot):
            evidence_ids = _evidence_ids(case.evidence_view)
            classification = self._classifier.classify_code(
                case.error_code, evidence_ids=evidence_ids
            )
            items.append(
                {
                    "run_case_id": str(case.run_case_id),
                    "failure_class": classification.failure_class.value,
                    "code": classification.code,
                    "confidence": classification.confidence,
                    "evidence_ids": [str(item) for item in classification.evidence_ids],
                    "source": classification.source,
                }
            )
        return StageExecution("completed", {"items": items})

    async def _diagnose(self, snapshot: PostprocessRunSnapshot) -> StageExecution:
        failed = self._failed_cases(snapshot)
        if self._diagnostic_model is None:
            return StageExecution(
                "warning",
                {
                    "items": [
                        {
                            "run_case_id": str(case.run_case_id),
                            "status": "inconclusive",
                            "failure_class": self._classifier.classify_code(
                                case.error_code
                            ).failure_class.value,
                            "reason": "Diagnostic model unavailable",
                            "hypotheses": [],
                        }
                        for case in failed
                    ]
                },
                "diagnostic_model_unavailable",
            )
        service = DiagnosticService(self._diagnostic_model)
        items = []
        warning = False
        for case in failed:
            result = await service.diagnose(case.evidence_view)
            warning = warning or result.status != "completed"
            items.append(
                {
                    "run_case_id": str(case.run_case_id),
                    "status": result.status,
                    "failure_class": (
                        result.hypotheses[0].failure_class.value
                        if result.hypotheses
                        else self._classifier.classify_code(case.error_code).failure_class.value
                    ),
                    "reason": result.reason,
                    "hypotheses": [
                        {
                            "summary": hypothesis.summary,
                            "failure_class": hypothesis.failure_class.value,
                            "confidence": hypothesis.confidence,
                            "evidence_ids": [str(item) for item in hypothesis.evidence_ids],
                            "counterevidence": list(hypothesis.counterevidence),
                            "verification_steps": list(hypothesis.verification_steps),
                        }
                        for hypothesis in result.hypotheses
                    ],
                }
            )
        return StageExecution(
            "warning" if warning else "completed",
            {"items": items},
            "diagnosis_inconclusive" if warning else None,
        )

    async def _reproduce(self, snapshot: PostprocessRunSnapshot) -> StageExecution:
        candidates: list[tuple[PostprocessCaseSnapshot, RegressionCandidate]] = []
        for case in self._failed_cases(snapshot):
            classification = self._classifier.classify_code(case.error_code)
            if classification.failure_class not in {FailureClass.TARGET, FailureClass.TEST}:
                continue
            candidate = RegressionCandidate.draft(
                case.run_case_id,
                {
                    "error_code": case.error_code,
                    "tool_chain": list(case.tool_chain),
                    "input": case.input_snapshot,
                },
            )
            candidate.start_reproduction()
            candidates.append((case, candidate))
        if self._reproducer is None:
            for _, candidate in candidates:
                candidate.record_reproduction(
                    reproduced=False,
                    observed_fingerprint=None,
                    evidence_ids=(),
                )
            return StageExecution(
                "warning",
                {
                    "items": [
                        _candidate_dict(candidate, reproduction_count=0)
                        for _, candidate in candidates
                    ]
                },
                "reproducer_unavailable",
            )
        output = []
        for case, candidate in candidates:
            observations = await self._reproducer.reproduce(case, candidate.fingerprint)
            for observation in observations:
                if candidate.state.value != "reproducing":
                    break
                candidate.record_reproduction(
                    reproduced=observation.reproduced,
                    observed_fingerprint=observation.fingerprint,
                    evidence_ids=observation.evidence_ids,
                )
            if candidate.state.value == "verified":
                candidate.publish()
            output.append(
                _candidate_dict(candidate, reproduction_count=len(candidate.reproduction_attempts))
            )
        return StageExecution("completed", {"items": output})

    @staticmethod
    def _calibrate(snapshot: PostprocessRunSnapshot) -> StageExecution:
        try:
            metrics = CalibrationMetrics.from_labels(
                predicted=snapshot.calibration_predicted,
                actual=snapshot.calibration_actual,
            )
        except ValueError:
            return StageExecution(
                "warning",
                {"status": "inconclusive", "metrics": {}},
                "insufficient_calibration_samples",
            )
        return StageExecution(
            "completed",
            {"status": "completed", "metrics": asdict(metrics), "calibrated": metrics.calibrated},
        )

    @staticmethod
    def _gate(snapshot: PostprocessRunSnapshot) -> StageExecution:
        decision = JointGate().evaluate(snapshot.gate_metrics)
        return StageExecution(
            "completed",
            {
                "decision": decision.status,
                "baseline_id": str(decision.baseline_id) if decision.baseline_id else None,
                "rules": [
                    {
                        "code": rule.code,
                        "status": rule.status,
                        "threshold": rule.threshold,
                        "actual": rule.actual,
                        "reason": rule.reason,
                        "evidence_refs": [str(item) for item in rule.evidence_refs],
                    }
                    for rule in decision.rules
                ],
            },
        )

    @staticmethod
    def _failed_cases(snapshot: PostprocessRunSnapshot) -> tuple[PostprocessCaseSnapshot, ...]:
        return tuple(case for case in snapshot.cases if case.status in {"failed", "error"})


def _evidence_ids(evidence_view: tuple[dict[str, object], ...]) -> tuple[UUID, ...]:
    values: list[UUID] = []
    for item in evidence_view:
        try:
            values.append(UUID(str(item["id"])))
        except (KeyError, TypeError, ValueError):
            continue
    return tuple(values)


def _candidate_dict(
    candidate: RegressionCandidate, *, reproduction_count: int
) -> dict[str, object]:
    return {
        "candidate_id": str(candidate.candidate_id),
        "run_case_id": str(candidate.source_run_case_id),
        "fingerprint": candidate.fingerprint,
        "state": candidate.state.value,
        "reproduction_count": reproduction_count,
        "evidence_ids": [str(item) for item in candidate.reproduction_evidence_ids],
        "quarantine_reason": candidate.quarantine_reason,
    }
