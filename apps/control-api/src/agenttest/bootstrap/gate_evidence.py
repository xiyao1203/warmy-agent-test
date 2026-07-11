from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.gates.application.evaluate import GateEvidence
from agenttest.modules.gates.infrastructure.persistence.models import ReleaseDecisionModel
from agenttest.modules.reviews.infrastructure.persistence.models import ReviewTaskModel
from agenttest.modules.runs.infrastructure.persistence.models import (
    RunCaseModel,
    RunEvaluationModel,
    RunModel,
)
from agenttest.modules.security.infrastructure.repositories import SecurityScanModel


class SqlAlchemyGateEvidence:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def load(self, project_id: UUID, run_id: UUID) -> GateEvidence | None:
        async with self._session_factory() as session:
            run = await session.scalar(
                select(RunModel).where(RunModel.id == run_id, RunModel.project_id == project_id)
            )
            if run is None:
                return None
            evaluation = await session.scalar(
                select(RunEvaluationModel).where(
                    RunEvaluationModel.project_id == project_id,
                    RunEvaluationModel.run_id == run_id,
                )
            )
            pending_reviews = await session.scalar(
                select(func.count())
                .select_from(ReviewTaskModel)
                .join(RunCaseModel, RunCaseModel.id == ReviewTaskModel.run_case_id)
                .where(
                    ReviewTaskModel.project_id == project_id,
                    RunCaseModel.run_id == run_id,
                    ReviewTaskModel.status == "pending",
                )
            )
            scan = await session.scalar(
                select(SecurityScanModel)
                .where(
                    SecurityScanModel.project_id == project_id,
                    SecurityScanModel.run_id == run_id,
                    SecurityScanModel.status == "completed",
                )
                .order_by(SecurityScanModel.completed_at.desc())
                .limit(1)
            )
            security_score = None
            blocking_findings = 0
            if scan is not None:
                raw_score = scan.summary.get("score")
                if isinstance(raw_score, int | float):
                    security_score = float(raw_score)
                findings: list[object] = (
                    list(scan.findings) if isinstance(scan.findings, list) else []
                )
                for item in findings:
                    if isinstance(item, dict) and str(item.get("severity", "")).lower() in {
                        "high",
                        "critical",
                    }:
                        blocking_findings += 1
            return GateEvidence(
                run_id=run_id,
                pass_rate=evaluation.pass_rate if evaluation else None,
                critical_passed=run.failed_cases == 0 and run.error_cases == 0,
                total_cost=evaluation.total_cost if evaluation else None,
                security_score=security_score,
                pending_reviews=int(pending_reviews or 0),
                blocking_findings=blocking_findings,
            )

    async def record(
        self,
        *,
        project_id: UUID,
        gate_id: UUID,
        actor_id: UUID,
        evidence: GateEvidence,
        passed: bool,
        failures: list[str],
        experiment_id: UUID | None,
    ) -> UUID:
        decision_id = uuid4()
        now = datetime.now(UTC)
        async with self._session_factory() as session:
            session.add(
                ReleaseDecisionModel(
                    id=decision_id,
                    project_id=project_id,
                    gate_id=gate_id,
                    run_id=evidence.run_id,
                    experiment_id=experiment_id,
                    status="passed" if passed else "blocked",
                    facts={
                        "pass_rate": evidence.pass_rate,
                        "critical_passed": evidence.critical_passed,
                        "total_cost": evidence.total_cost,
                        "security_score": evidence.security_score,
                        "pending_reviews": evidence.pending_reviews,
                        "blocking_findings": evidence.blocking_findings,
                    },
                    failures=failures,
                    evidence={"run_id": str(evidence.run_id)},
                    evaluated_by=actor_id,
                    created_at=now,
                    updated_at=now,
                )
            )
            await session.commit()
        return decision_id
