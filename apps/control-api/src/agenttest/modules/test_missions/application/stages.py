from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_missions.application.compiler import (
    MissionCompiler,
    ProvisioningPlan,
)
from agenttest.modules.test_missions.domain.value_objects import MissionRevision


@dataclass(frozen=True, slots=True)
class StageReceipt:
    receipt_id: UUID
    project_id: UUID
    revision_id: UUID
    stage: str
    status: str
    output: dict[str, object]
    created_at: datetime


class StageReceiptRepository(Protocol):
    async def get_stage_receipt(
        self, project_id: UUID, revision_id: UUID, stage: str
    ) -> StageReceipt | None: ...

    async def save_stage_receipt(self, receipt: StageReceipt) -> None: ...


class MissionAssetExecutor(Protocol):
    async def execute(
        self,
        *,
        capability: str,
        child_agent: str,
        actor: User,
        project_id: ProjectId,
        session_id: UUID,
        arguments: dict[str, object],
        idempotency_key: str,
    ) -> dict[str, object]: ...


class MissionStageService:
    def __init__(
        self,
        compiler: MissionCompiler,
        executor: MissionAssetExecutor,
        receipts: StageReceiptRepository,
    ) -> None:
        self._compiler = compiler
        self._executor = executor
        self._receipts = receipts

    async def provision(
        self,
        *,
        actor: User,
        project_id: ProjectId,
        session_id: UUID,
        revision: MissionRevision,
    ) -> StageReceipt:
        existing = await self._receipts.get_stage_receipt(
            project_id.value, revision.revision_id, "provision"
        )
        if existing is not None:
            return existing
        plan = self._compiler.compile(revision)
        output = await self._execute_plan(actor, project_id, session_id, revision, plan)
        receipt = StageReceipt(
            receipt_id=UUID(bytes=revision.revision_id.bytes),
            project_id=project_id.value,
            revision_id=revision.revision_id,
            stage="provision",
            status="completed",
            output=output,
            created_at=datetime.now(UTC),
        )
        await self._receipts.save_stage_receipt(receipt)
        return receipt

    async def _execute_plan(
        self,
        actor: User,
        project_id: ProjectId,
        session_id: UUID,
        revision: MissionRevision,
        plan: ProvisioningPlan,
    ) -> dict[str, object]:
        prefix = f"mission:{revision.revision_id}:provision"
        agent_version_id = plan.agent_version_id
        if plan.create_agent:
            agent = await self._call(
                "agents.create",
                "target_agent",
                actor,
                project_id,
                session_id,
                {"name": plan.name, "description": plan.description, "config": {}},
                f"{prefix}:agent",
            )
            agent_id = _artifact_id(agent, "agent")
            version = await self._call(
                "agents.create_version",
                "target_agent",
                actor,
                project_id,
                session_id,
                {
                    "agent_id": agent_id,
                    "config": {
                        "api_url": plan.target_url,
                        "web_url": plan.target_url,
                        "target_config": {
                            "target_url": plan.target_url,
                            "browser_profile_id": plan.browser_profile_id,
                            "safety": {"allowed_actions": list(plan.action_allowlist)},
                        },
                    },
                },
                f"{prefix}:agent-version",
            )
            agent_version_id = _artifact_id(version, "agent_version")
            await self._call(
                "agents.publish_version",
                "target_agent",
                actor,
                project_id,
                session_id,
                {"id": agent_version_id},
                f"{prefix}:publish-agent-version",
            )
        if not agent_version_id:
            raise ValueError("Provisioning requires an Agent version")

        dataset = await self._call(
            "datasets.create_with_cases",
            "test_data",
            actor,
            project_id,
            session_id,
            {
                "name": f"{plan.name} 数据集",
                "description": plan.description,
                "config": {},
                "cases": [case.to_platform_dict() for case in plan.cases],
            },
            f"{prefix}:dataset",
        )
        dataset_version_id = _artifact_id(dataset, "dataset_version")
        await self._call(
            "datasets.publish_version",
            "test_data",
            actor,
            project_id,
            session_id,
            {"id": dataset_version_id},
            f"{prefix}:publish-dataset",
        )
        scorer = await self._call(
            "scorers.create",
            "evaluation",
            actor,
            project_id,
            session_id,
            {
                "name": f"{plan.name} 质量评分",
                "description": "对话任务自动创建的质量评分器",
                "config": {
                    "scorer_type": "deepeval",
                    "metric": "answer_relevancy",
                    "threshold": 0.8,
                },
            },
            f"{prefix}:scorer",
        )
        scorer_id = _artifact_id(scorer, "scorer")
        test_plan = await self._call(
            "test_plans.create_version",
            "test_plan",
            actor,
            project_id,
            session_id,
            {
                "name": plan.name,
                "description": plan.description,
                "agent_version_id": agent_version_id,
                "dataset_version_id": dataset_version_id,
                "config": {
                    "api_browser_ratio": 0.8
                    if {"api", "browser"}.issubset(plan.execution_channels)
                    else (1.0 if "api" in plan.execution_channels else 0.0),
                    "concurrency": 4,
                    "timeout": 300,
                    "max_retries": 1,
                    "pass_threshold": 0.8,
                    "cost_budget": plan.cost_budget,
                    "scorer_ids": [scorer_id],
                    "browser_profile_id": plan.browser_profile_id,
                },
            },
            f"{prefix}:test-plan",
        )
        test_plan_version_id = _artifact_id(test_plan, "test_plan_version")
        await self._call(
            "test_plans.publish_version",
            "test_plan",
            actor,
            project_id,
            session_id,
            {"id": test_plan_version_id},
            f"{prefix}:publish-test-plan",
        )
        return {
            "agent_version_id": agent_version_id,
            "dataset_version_id": dataset_version_id,
            "scorer_id": scorer_id,
            "test_plan_version_id": test_plan_version_id,
            "case_count": len(plan.cases),
        }

    async def _call(
        self,
        capability: str,
        child_agent: str,
        actor: User,
        project_id: ProjectId,
        session_id: UUID,
        arguments: dict[str, object],
        idempotency_key: str,
    ) -> dict[str, object]:
        return await self._executor.execute(
            capability=capability,
            child_agent=child_agent,
            actor=actor,
            project_id=project_id,
            session_id=session_id,
            arguments=arguments,
            idempotency_key=idempotency_key,
        )


def _artifact_id(result: dict[str, object], kind: str) -> str:
    artifacts = result.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValueError(f"Capability did not produce {kind}")
    for item in artifacts:
        if isinstance(item, dict) and item.get("type") == kind and item.get("id"):
            return str(item["id"])
    raise ValueError(f"Capability did not produce {kind}")
