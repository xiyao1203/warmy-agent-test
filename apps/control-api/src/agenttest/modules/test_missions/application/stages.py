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

    async def replace_stage_receipt(self, receipt: StageReceipt) -> None: ...

    async def link_asset(
        self,
        project_id: UUID,
        mission_id: UUID,
        asset_type: str,
        asset_id: UUID,
        relation: str,
        *,
        stage: str | None = None,
    ) -> bool: ...


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


class MissionTrustLoopReader(Protocol):
    async def get_summary(
        self, actor: User, project_id: UUID, run_id: UUID
    ) -> dict[str, object]: ...


class MissionNeedsAttention(RuntimeError):
    def __init__(self, message: str, *, error_type: str = "auth_expired") -> None:
        super().__init__(message)
        self.error_type = error_type


class MissionStageService:
    def __init__(
        self,
        compiler: MissionCompiler,
        executor: MissionAssetExecutor,
        receipts: StageReceiptRepository,
        trust_loop: MissionTrustLoopReader | None = None,
    ) -> None:
        self._compiler = compiler
        self._executor = executor
        self._receipts = receipts
        self._trust_loop = trust_loop

    async def provision(
        self, *, actor: User, project_id: ProjectId, session_id: UUID, revision: MissionRevision
    ) -> StageReceipt:
        existing = await self._existing(project_id.value, revision.revision_id, "provision")
        if existing:
            return existing
        output = await self._execute_plan(
            actor, project_id, session_id, revision, self._compiler.compile(revision)
        )
        await self._link_output(revision, "provision", output)
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
        run_id = _artifact_id(result, "run")
        await self._link_asset(revision, "start_run", "run", run_id)
        return await self._save(
            project_id.value,
            revision.revision_id,
            "start_run",
            {"run_id": run_id, "test_plan_version_id": plan_version_id, "attempt": 0},
        )

    async def await_run(
        self,
        *,
        actor: User,
        project_id: ProjectId,
        session_id: UUID,
        revision: MissionRevision,
        resume_attempt: int = 0,
    ) -> StageReceipt | None:
        existing = await self._existing(project_id.value, revision.revision_id, "await_run")
        if existing:
            return existing
        started = await self._required(project_id.value, revision.revision_id, "start_run")
        run_id = str(started.output["run_id"])
        result = await self._call(
            "runs.get_status",
            "execution",
            actor,
            project_id,
            session_id,
            {"id": run_id},
            f"mission:{revision.revision_id}:read-run",
        )
        status = str(result.get("status") or "")
        if status in {"queued", "running"}:
            return None
        if str(result.get("error_type") or "") == "auth_expired":
            raw_attempt = started.output.get("attempt")
            current_attempt = raw_attempt if isinstance(raw_attempt, int) else 0
            message = str(result.get("error_message") or "Browser login expired")
            if resume_attempt <= current_attempt:
                raise MissionNeedsAttention(message)
            plan_version_id = str(started.output["test_plan_version_id"])
            restarted = await self._call(
                "runs.start",
                "execution",
                actor,
                project_id,
                session_id,
                {"test_plan_version_id": plan_version_id},
                f"mission:{revision.revision_id}:start-run:resume:{resume_attempt}",
            )
            new_run_id = _artifact_id(restarted, "run")
            await self._link_asset(revision, "start_run", "run", new_run_id)
            await self._replace(
                project_id.value,
                revision.revision_id,
                "start_run",
                {
                    "run_id": new_run_id,
                    "test_plan_version_id": plan_version_id,
                    "attempt": resume_attempt,
                },
            )
            return None
        return await self._save(
            project_id.value,
            revision.revision_id,
            "await_run",
            {"run_id": run_id, "run_status": status, "quality_passed": status == "passed"},
        )

    async def close_loop(
        self, *, actor: User, project_id: ProjectId, session_id: UUID, revision: MissionRevision
    ) -> StageReceipt | None:
        existing = await self._existing(project_id.value, revision.revision_id, "close_loop")
        if existing:
            return existing
        completed = await self._required(project_id.value, revision.revision_id, "await_run")
        run_id = str(completed.output["run_id"])
        if self._trust_loop is None:
            raise RuntimeError("Mission trust loop reader is unavailable")
        trust_loop = await self._trust_loop.get_summary(actor, project_id.value, UUID(run_id))
        if str(trust_loop.get("status") or "pending") in {"pending", "running"}:
            return None
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
        await self._link_output(revision, "close_loop", report)
        await self._link_output(revision, "close_loop", reviews)
        return await self._save(
            project_id.value,
            revision.revision_id,
            "close_loop",
            {
                "run_id": run_id,
                "run_status": completed.output.get("run_status"),
                "report": report,
                "reviews": reviews,
                "trust_loop": trust_loop,
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

    async def _replace(
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
        await self._receipts.replace_stage_receipt(receipt)
        return receipt

    async def _link_output(
        self, revision: MissionRevision, stage: str, output: dict[str, object]
    ) -> None:
        for key, asset_type in {
            "agent_version_id": "agent_version",
            "dataset_version_id": "dataset_version",
            "scorer_id": "scorer",
            "test_plan_version_id": "test_plan_version",
            "run_id": "run",
        }.items():
            value = output.get(key)
            if value:
                await self._link_asset(revision, stage, asset_type, str(value))
        artifacts = output.get("artifacts")
        if isinstance(artifacts, list):
            for item in artifacts:
                if not isinstance(item, dict) or not item.get("type") or not item.get("id"):
                    continue
                await self._link_asset(
                    revision,
                    stage,
                    str(item["type"]),
                    str(item["id"]),
                    relation=str(item.get("relation") or "created"),
                )

    async def _link_asset(
        self,
        revision: MissionRevision,
        stage: str,
        asset_type: str,
        asset_id: str,
        *,
        relation: str = "created",
    ) -> None:
        await self._receipts.link_asset(
            revision.project_id,
            revision.mission_id,
            asset_type,
            UUID(asset_id),
            relation,
            stage=stage,
        )


def _artifact_id(result: dict[str, object], kind: str) -> str:
    artifacts = result.get("artifacts")
    if isinstance(artifacts, list):
        for item in artifacts:
            if isinstance(item, dict) and item.get("type") == kind and item.get("id"):
                return str(item["id"])
    raise ValueError(f"Capability did not produce {kind}")
