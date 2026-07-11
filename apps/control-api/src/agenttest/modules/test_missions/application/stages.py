from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_missions.application.compiler import MissionCompiler, ProvisioningPlan
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
        self, *, actor: User, project_id: ProjectId, session_id: UUID, revision: MissionRevision
    ) -> StageReceipt:
        existing = await self._existing(project_id.value, revision.revision_id, "provision")
        if existing:
            return existing
        output = await self._execute_plan(
            actor, project_id, session_id, revision, self._compiler.compile(revision)
        )
        return await self._save(project_id.value, revision.revision_id, "provision", output)

    async def start_run(
        self, *, actor: User, project_id: ProjectId, session_id: UUID, revision: MissionRevision
    ) -> StageReceipt:
        existing = await self._existing(project_id.value, revision.revision_id, "start_run")
        if existing:
            return existing
        provision = await self._required(project_id.value, revision.revision_id, "provision")
        plan_version_id = str(provision.output["test_plan_version_id"])
        result = await self._call(
            "runs.start",
            "execution",
            actor,
            project_id,
            session_id,
            {"test_plan_version_id": plan_version_id},
            f"mission:{revision.revision_id}:start-run",
        )
        return await self._save(
            project_id.value,
            revision.revision_id,
            "start_run",
            {"run_id": _artifact_id(result, "run"), "test_plan_version_id": plan_version_id},
        )

    async def await_run(
        self, *, actor: User, project_id: ProjectId, session_id: UUID, revision: MissionRevision
    ) -> StageReceipt | None:
        existing = await self._existing(project_id.value, revision.revision_id, "await_run")
        if existing:
            return existing
        started = await self._required(project_id.value, revision.revision_id, "start_run")
        run_id = str(started.output["run_id"])
        result = await self._call(
            "runs.list",
            "execution",
            actor,
            project_id,
            session_id,
            {},
            f"mission:{revision.revision_id}:read-run",
        )
        items = result.get("items")
        run = (
            next(
                (
                    item
                    for item in items
                    if isinstance(item, dict) and str(item.get("id")) == run_id
                ),
                None,
            )
            if isinstance(items, list)
            else None
        )
        if run is None:
            raise ValueError("Mission Run does not exist in project")
        status = str(run.get("status") or "")
        if status in {"queued", "running"}:
            return None
        return await self._save(
            project_id.value,
            revision.revision_id,
            "await_run",
            {"run_id": run_id, "run_status": status, "quality_passed": status == "passed"},
        )

    async def close_loop(
        self, *, actor: User, project_id: ProjectId, session_id: UUID, revision: MissionRevision
    ) -> StageReceipt:
        existing = await self._existing(project_id.value, revision.revision_id, "close_loop")
        if existing:
            return existing
        completed = await self._required(project_id.value, revision.revision_id, "await_run")
        run_id = str(completed.output["run_id"])
        report = await self._call(
            "reports.generate",
            "execution",
            actor,
            project_id,
            session_id,
            {"run_id": run_id},
            f"mission:{revision.revision_id}:report",
        )
        reviews = await self._call(
            "reviews.enqueue",
            "review_gate",
            actor,
            project_id,
            session_id,
            {"run_id": run_id, "confidence_threshold": 0.5},
            f"mission:{revision.revision_id}:reviews",
        )
        return await self._save(
            project_id.value,
            revision.revision_id,
            "close_loop",
            {
                "run_id": run_id,
                "run_status": completed.output.get("run_status"),
                "report": report,
                "reviews": reviews,
            },
        )

    async def cancel_run(
        self, *, actor: User, project_id: ProjectId, session_id: UUID, revision: MissionRevision
    ) -> dict[str, object]:
        started = await self._existing(project_id.value, revision.revision_id, "start_run")
        if started is None:
            return {"cancelled": True}
        return await self._call(
            "runs.cancel",
            "execution",
            actor,
            project_id,
            session_id,
            {"id": str(started.output["run_id"])},
            f"mission:{revision.revision_id}:cancel",
        )

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
            version = await self._call(
                "agents.create_version",
                "target_agent",
                actor,
                project_id,
                session_id,
                {
                    "agent_id": _artifact_id(agent, "agent"),
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

    async def _existing(self, project_id: UUID, revision_id: UUID, stage: str):
        return await self._receipts.get_stage_receipt(project_id, revision_id, stage)

    async def _required(self, project_id: UUID, revision_id: UUID, stage: str) -> StageReceipt:
        receipt = await self._existing(project_id, revision_id, stage)
        if receipt is None:
            raise ValueError(f"Mission stage {stage} has not completed")
        return receipt

    async def _save(
        self, project_id: UUID, revision_id: UUID, stage: str, output: dict[str, object]
    ) -> StageReceipt:
        receipt = StageReceipt(
            receipt_id=uuid5(NAMESPACE_URL, f"agenttest:{revision_id}:{stage}"),
            project_id=project_id,
            revision_id=revision_id,
            stage=stage,
            status="completed",
            output=output,
            created_at=datetime.now(UTC),
        )
        await self._receipts.save_stage_receipt(receipt)
        return receipt


def _artifact_id(result: dict[str, object], kind: str) -> str:
    artifacts = result.get("artifacts")
    if isinstance(artifacts, list):
        for item in artifacts:
            if isinstance(item, dict) and item.get("type") == kind and item.get("id"):
                return str(item["id"])
    raise ValueError(f"Capability did not produce {kind}")
