from __future__ import annotations

from datetime import UTC, datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.run_postprocessing.domain import (
    PostprocessStage,
    PostprocessStatus,
    RunPostprocessJob,
    StageResult,
)
from agenttest.modules.run_postprocessing.infrastructure.models import (
    RunCalibrationModel,
    RunDiagnosticModel,
    RunJointGateDecisionModel,
    RunPostprocessJobModel,
    RunPostprocessStageResultModel,
    RunRegressionCandidateModel,
)
from agenttest.shared.infrastructure.database import session_scope, transaction_scope


class SqlAlchemyPostprocessRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create_or_get(self, job: RunPostprocessJob) -> RunPostprocessJob:
        async with transaction_scope(self._session_factory) as session:
            existing = await session.scalar(
                self._job_query(job.project_id, job.run_id, job.pipeline_version)
            )
            if existing is not None:
                return _to_job(existing, [])
            session.add(_job_model(job))
            await session.flush()
        return job

    async def get(
        self, project_id: UUID, run_id: UUID, pipeline_version: str
    ) -> RunPostprocessJob | None:
        async with session_scope(self._session_factory) as session:
            model = await session.scalar(self._job_query(project_id, run_id, pipeline_version))
            if model is None:
                return None
            stages = list(
                (
                    await session.scalars(
                        select(RunPostprocessStageResultModel)
                        .where(
                            RunPostprocessStageResultModel.project_id == project_id,
                            RunPostprocessStageResultModel.job_id == model.id,
                        )
                        .order_by(RunPostprocessStageResultModel.completed_at)
                    )
                ).all()
            )
        return _to_job(model, [_to_stage_result(item) for item in stages])

    async def save(self, job: RunPostprocessJob) -> None:
        async with transaction_scope(self._session_factory) as session:
            await session.execute(
                update(RunPostprocessJobModel)
                .where(
                    RunPostprocessJobModel.project_id == job.project_id,
                    RunPostprocessJobModel.id == job.job_id,
                )
                .values(
                    status=job.status.value,
                    current_stage=job.current_stage.value if job.current_stage else None,
                    workflow_id=job.workflow_id,
                    attempt=job.attempt,
                    warning_codes=job.warning_codes,
                    error_type=job.error_type,
                    error_message=job.error_message,
                    updated_at=job.updated_at,
                    started_at=job.started_at,
                    completed_at=job.completed_at,
                )
            )

    async def save_stage_result(self, job: RunPostprocessJob, result: StageResult) -> None:
        result_id = uuid5(NAMESPACE_URL, f"agenttest:{job.job_id}:{result.stage.value}")
        async with transaction_scope(self._session_factory) as session:
            existing = await session.scalar(
                select(RunPostprocessStageResultModel.id).where(
                    RunPostprocessStageResultModel.project_id == job.project_id,
                    RunPostprocessStageResultModel.job_id == job.job_id,
                    RunPostprocessStageResultModel.stage == result.stage.value,
                )
            )
            if existing is not None:
                return
            session.add(
                RunPostprocessStageResultModel(
                    id=result_id,
                    project_id=job.project_id,
                    job_id=job.job_id,
                    run_id=job.run_id,
                    stage=result.stage.value,
                    status=result.status,
                    output=result.output,
                    warning_code=result.warning_code,
                    error_type=result.error_type,
                    error_message=result.error_message,
                    completed_at=result.completed_at,
                )
            )

    async def save_stage_records(self, job: RunPostprocessJob, result: StageResult) -> None:
        async with transaction_scope(self._session_factory) as session:
            if result.stage is PostprocessStage.DIAGNOSE:
                for item in _items(result.output):
                    run_case_id = UUID(str(item["run_case_id"]))
                    hypotheses = item.get("hypotheses")
                    hypothesis = (
                        hypotheses[0]
                        if isinstance(hypotheses, list)
                        and hypotheses
                        and isinstance(hypotheses[0], dict)
                        else {}
                    )
                    record_id = uuid5(
                        NAMESPACE_URL,
                        f"agenttest:{job.job_id}:diagnostic:{run_case_id}",
                    )
                    if await session.get(RunDiagnosticModel, record_id) is not None:
                        continue
                    session.add(
                        RunDiagnosticModel(
                            id=record_id,
                            project_id=job.project_id,
                            run_id=job.run_id,
                            run_case_id=run_case_id,
                            pipeline_version=job.pipeline_version,
                            status=str(item.get("status") or "inconclusive"),
                            failure_class=str(item.get("failure_class") or "unknown"),
                            confidence=float(hypothesis.get("confidence") or 0.0),
                            evidence_ids=list(hypothesis.get("evidence_ids") or []),
                            summary=str(hypothesis.get("summary") or "") or None,
                            counterevidence=list(hypothesis.get("counterevidence") or []),
                            verification_steps=list(hypothesis.get("verification_steps") or []),
                            model_adapter_version=None,
                            created_at=result.completed_at,
                            updated_at=result.completed_at,
                        )
                    )
            elif result.stage is PostprocessStage.REPRODUCE:
                for item in _items(result.output):
                    candidate_id = UUID(str(item["candidate_id"]))
                    if await session.get(RunRegressionCandidateModel, candidate_id) is not None:
                        continue
                    session.add(
                        RunRegressionCandidateModel(
                            id=candidate_id,
                            project_id=job.project_id,
                            run_id=job.run_id,
                            run_case_id=UUID(str(item["run_case_id"])),
                            pipeline_version=job.pipeline_version,
                            fingerprint=str(item["fingerprint"]),
                            status=str(item["state"]),
                            input_reference={"run_case_id": str(item["run_case_id"])},
                            minimized_input=None,
                            reproduction_run_case_ids=_list(item.get("evidence_ids")),
                            reproduction_count=_int(item.get("reproduction_count")),
                            target_dataset_version_id=None,
                            created_at=result.completed_at,
                            updated_at=result.completed_at,
                        )
                    )
            elif result.stage is PostprocessStage.CALIBRATE:
                record_id = uuid5(NAMESPACE_URL, f"agenttest:{job.job_id}:calibration")
                if await session.get(RunCalibrationModel, record_id) is None:
                    session.add(
                        RunCalibrationModel(
                            id=record_id,
                            project_id=job.project_id,
                            run_id=job.run_id,
                            pipeline_version=job.pipeline_version,
                            status=str(result.output.get("status") or "inconclusive"),
                            sample_set_version=None,
                            metrics=_dict(result.output.get("metrics")),
                            arbitration={},
                            evaluator_version=None,
                            created_at=result.completed_at,
                            updated_at=result.completed_at,
                        )
                    )
            elif result.stage is PostprocessStage.EVALUATE_GATE:
                record_id = uuid5(NAMESPACE_URL, f"agenttest:{job.job_id}:joint-gate")
                if await session.get(RunJointGateDecisionModel, record_id) is None:
                    baseline = result.output.get("baseline_id")
                    session.add(
                        RunJointGateDecisionModel(
                            id=record_id,
                            project_id=job.project_id,
                            run_id=job.run_id,
                            pipeline_version=job.pipeline_version,
                            baseline_run_id=UUID(str(baseline)) if baseline else None,
                            decision=str(result.output.get("decision") or "needs_review"),
                            rules=_list(result.output.get("rules")),
                            input_facts={},
                            explanation="Joint gate evaluated deterministic ordered rules",
                            created_at=result.completed_at,
                        )
                    )

    async def list_stage_results(self, project_id: UUID, job_id: UUID) -> list[StageResult]:
        async with session_scope(self._session_factory) as session:
            models = list(
                (
                    await session.scalars(
                        select(RunPostprocessStageResultModel)
                        .where(
                            RunPostprocessStageResultModel.project_id == project_id,
                            RunPostprocessStageResultModel.job_id == job_id,
                        )
                        .order_by(RunPostprocessStageResultModel.completed_at)
                    )
                ).all()
            )
        return [_to_stage_result(model) for model in models]

    @staticmethod
    def _job_query(project_id: UUID, run_id: UUID, pipeline_version: str):
        return select(RunPostprocessJobModel).where(
            RunPostprocessJobModel.project_id == project_id,
            RunPostprocessJobModel.run_id == run_id,
            RunPostprocessJobModel.pipeline_version == pipeline_version,
        )


def _job_model(job: RunPostprocessJob) -> RunPostprocessJobModel:
    return RunPostprocessJobModel(
        id=job.job_id,
        project_id=job.project_id,
        run_id=job.run_id,
        pipeline_version=job.pipeline_version,
        status=job.status.value,
        current_stage=job.current_stage.value if job.current_stage else None,
        workflow_id=job.workflow_id,
        attempt=job.attempt,
        warning_codes=job.warning_codes,
        error_type=job.error_type,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


def _to_job(model: RunPostprocessJobModel, results: list[StageResult]) -> RunPostprocessJob:
    return RunPostprocessJob(
        job_id=model.id,
        project_id=model.project_id,
        run_id=model.run_id,
        pipeline_version=model.pipeline_version,
        status=PostprocessStatus(model.status),
        current_stage=PostprocessStage(model.current_stage) if model.current_stage else None,
        workflow_id=model.workflow_id,
        attempt=model.attempt,
        warning_codes=list(model.warning_codes or []),
        error_type=model.error_type,
        error_message=model.error_message,
        stage_results=results,
        created_at=_utc(model.created_at),
        updated_at=_utc(model.updated_at),
        started_at=_utc(model.started_at) if model.started_at else None,
        completed_at=_utc(model.completed_at) if model.completed_at else None,
    )


def _to_stage_result(model: RunPostprocessStageResultModel) -> StageResult:
    return StageResult(
        stage=PostprocessStage(model.stage),
        status=model.status,
        output=dict(model.output or {}),
        warning_code=model.warning_code,
        error_type=model.error_type,
        error_message=model.error_message,
        completed_at=_utc(model.completed_at),
    )


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _items(output: dict[str, object]) -> list[dict[str, object]]:
    value = output.get("items")
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _dict(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def _int(value: object) -> int:
    return value if isinstance(value, int) else 0
