from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agenttest.modules.agents.infrastructure.persistence.models import AgentVersionModel
from agenttest.modules.artifacts.infrastructure.repositories import ArtifactModel
from agenttest.modules.experiments.infrastructure.persistence.models import ExperimentModel
from agenttest.modules.gates.infrastructure.persistence.models import (
    ReleaseDecisionModel,
    ReleaseGateModel,
)
from agenttest.modules.runs.infrastructure.persistence.models import RunModel
from agenttest.modules.security.infrastructure.repositories import SecurityScanModel
from agenttest.modules.test_plans.infrastructure.persistence.models import (
    TestPlanModel,
    TestPlanVersionModel,
)
from agenttest.shared.infrastructure.database import session_scope


class SqlAlchemyAgentRelationshipsReader:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def read(self, project_id: UUID, agent_id: UUID) -> dict[str, object]:
        async with session_scope(self._session_factory) as session:
            version_ids = list(
                await session.scalars(
                    select(AgentVersionModel.id).where(AgentVersionModel.agent_id == agent_id)
                )
            )
            if not version_ids:
                return _empty()
            plans = list(
                (
                    await session.execute(
                        select(TestPlanVersionModel, TestPlanModel)
                        .join(TestPlanModel, TestPlanModel.id == TestPlanVersionModel.test_plan_id)
                        .where(
                            TestPlanModel.project_id == project_id,
                            TestPlanVersionModel.agent_version_id.in_(version_ids),
                        )
                        .order_by(TestPlanVersionModel.updated_at.desc())
                        .limit(20)
                    )
                ).all()
            )
            runs = list(
                await session.scalars(
                    select(RunModel)
                    .where(
                        RunModel.project_id == project_id,
                        RunModel.agent_version_id.in_(version_ids),
                    )
                    .order_by(RunModel.created_at.desc())
                    .limit(20)
                )
            )
            run_ids = [item.id for item in runs]
            artifacts = (
                list(
                    await session.scalars(
                        select(ArtifactModel)
                        .where(
                            ArtifactModel.project_id == project_id,
                            ArtifactModel.run_id.in_(run_ids),
                        )
                        .order_by(ArtifactModel.created_at.desc())
                        .limit(20)
                    )
                )
                if run_ids
                else []
            )
            experiments = (
                list(
                    await session.scalars(
                        select(ExperimentModel)
                        .where(
                            ExperimentModel.project_id == project_id,
                            or_(
                                ExperimentModel.run_a_id.in_(run_ids),
                                ExperimentModel.run_b_id.in_(run_ids),
                            ),
                        )
                        .order_by(ExperimentModel.updated_at.desc())
                        .limit(20)
                    )
                )
                if run_ids
                else []
            )
            scans = list(
                await session.scalars(
                    select(SecurityScanModel)
                    .where(
                        SecurityScanModel.project_id == project_id,
                        SecurityScanModel.agent_version_id.in_(version_ids),
                    )
                    .order_by(SecurityScanModel.created_at.desc())
                    .limit(20)
                )
            )
            experiment_ids = [item.id for item in experiments]
            decisions = (
                list(
                    (
                        await session.execute(
                            select(ReleaseDecisionModel, ReleaseGateModel)
                            .join(
                                ReleaseGateModel,
                                ReleaseGateModel.id == ReleaseDecisionModel.gate_id,
                            )
                            .where(
                                ReleaseDecisionModel.project_id == project_id,
                                or_(
                                    ReleaseDecisionModel.run_id.in_(run_ids),
                                    ReleaseDecisionModel.experiment_id.in_(experiment_ids),
                                ),
                            )
                            .order_by(ReleaseDecisionModel.created_at.desc())
                            .limit(20)
                        )
                    ).all()
                )
                if run_ids or experiment_ids
                else []
            )
        return {
            "plans": [
                {
                    "id": str(plan.id),
                    "plan_id": str(parent.id),
                    "name": parent.name,
                    "version_number": plan.version_number,
                    "status": plan.status,
                }
                for plan, parent in plans
            ],
            "runs": [
                {
                    "id": str(run.id),
                    "status": run.status,
                    "agent_version_id": str(run.agent_version_id),
                    "passed_cases": run.passed_cases,
                    "total_cases": run.total_cases,
                    "created_at": run.created_at.isoformat(),
                }
                for run in runs
            ],
            "artifacts": [
                {
                    "id": str(item.id),
                    "run_id": str(item.run_id),
                    "filename": item.filename,
                    "content_type": item.content_type,
                    "created_at": item.created_at.isoformat(),
                }
                for item in artifacts
            ],
            "experiments": [
                {"id": str(item.id), "name": item.name, "status": item.status}
                for item in experiments
            ],
            "security_scans": [
                {
                    "id": str(item.id),
                    "status": item.status,
                    "scan_type": item.scan_type,
                    "agent_version_id": str(item.agent_version_id),
                }
                for item in scans
            ],
            "gates": [
                {
                    "id": str(decision.id),
                    "gate_id": str(gate.id),
                    "name": gate.name,
                    "status": decision.status,
                    "run_id": str(decision.run_id),
                }
                for decision, gate in decisions
            ],
        }


def _empty() -> dict[str, object]:
    return {
        "plans": [],
        "runs": [],
        "artifacts": [],
        "experiments": [],
        "security_scans": [],
        "gates": [],
    }
