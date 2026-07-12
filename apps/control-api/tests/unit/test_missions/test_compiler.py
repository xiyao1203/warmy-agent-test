from datetime import UTC, datetime
from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_missions.application.compiler import MissionCompiler
from agenttest.modules.test_missions.application.stages import (
    MissionNeedsAttention,
    MissionStageService,
    StageReceipt,
)
from agenttest.modules.test_missions.domain.value_objects import MissionRevision


def revision(*, agent_version_id: str | None = None) -> MissionRevision:
    facts = {
        "target": {
            "value": {
                "url": "https://agent.example/chat",
                **({"agent_version_id": agent_version_id} if agent_version_id else {}),
            },
            "source": "user_provided",
            "confidence": 1,
            "verified": True,
        },
        "test_goal": {
            "value": "验证客服多轮问答",
            "source": "user_provided",
            "confidence": 1,
            "verified": True,
        },
        "scenario_hints": {
            "value": ["正常咨询", "退款边界"],
            "source": "system_inferred",
            "confidence": 0.75,
            "verified": False,
        },
        "safety_scope": {
            "value": "read_only",
            "source": "user_provided",
            "confidence": 1,
            "verified": True,
        },
        "access": {
            "value": {"strategy": "none"},
            "source": "user_provided",
            "confidence": 1,
            "verified": True,
        },
    }
    return MissionRevision(
        revision_id=uuid4(),
        project_id=uuid4(),
        mission_id=uuid4(),
        revision_number=1,
        snapshot={
            "facts": facts,
            "execution": {"channels": ["api", "browser", "security"]},
            "budget": {"max_cases": 50, "hard_cost": 20},
            "action_allowlist": ["read"],
        },
        content_hash="a" * 64,
        confirmed_by=uuid4(),
        confirmed_at=datetime.now(UTC),
    )


def test_compiler_reuses_agent_and_builds_api_browser_security_cases() -> None:
    agent_version_id = str(uuid4())

    plan = MissionCompiler().compile(revision(agent_version_id=agent_version_id))

    assert plan.agent_version_id == agent_version_id
    assert plan.create_agent is False
    assert {case.execution_mode for case in plan.cases} == {"api", "browser"}
    assert any("security-baseline" in case.tags for case in plan.cases)
    assert all(case.provenance in {"user_provided", "system_inferred"} for case in plan.cases)
    assert len(plan.cases) <= 50


class Receipts:
    def __init__(self) -> None:
        self.items = {}
        self.assets = []

    async def get_stage_receipt(self, project_id, revision_id, stage):
        return self.items.get((project_id, revision_id, stage))

    async def save_stage_receipt(self, receipt):
        self.items[(receipt.project_id, receipt.revision_id, receipt.stage)] = receipt

    async def replace_stage_receipt(self, receipt):
        self.items[(receipt.project_id, receipt.revision_id, receipt.stage)] = receipt

    async def link_asset(
        self, project_id, mission_id, asset_type, asset_id, relation, *, stage=None
    ):
        item = (project_id, mission_id, asset_type, asset_id, relation, stage)
        if item in self.assets:
            return False
        self.assets.append(item)
        return True


class Executor:
    def __init__(self) -> None:
        self.calls = []

    async def execute(
        self, *, capability, child_agent, actor, project_id, session_id, arguments, idempotency_key
    ):
        self.calls.append((capability, idempotency_key, arguments))
        ids = {
            "agents.create": ("agent", uuid4()),
            "agents.create_version": ("agent_version", uuid4()),
            "agents.publish_version": ("agent_version", uuid4()),
            "datasets.create_with_cases": ("dataset_version", uuid4()),
            "datasets.publish_version": ("dataset_version", uuid4()),
            "scorers.create": ("scorer", uuid4()),
            "test_plans.create_version": ("test_plan_version", uuid4()),
            "test_plans.publish_version": ("test_plan_version", uuid4()),
            "runs.start": ("run", uuid4()),
        }
        if capability == "runs.get_status":
            return {
                "id": str(arguments["id"]),
                "status": "error",
                "error_type": "auth_expired",
                "error_message": "Browser login expired",
            }
        kind, value = ids[capability]
        return {"artifacts": [{"type": kind, "id": str(value), "relation": "created"}]}


class CloseLoopExecutor(Executor):
    async def execute(
        self, *, capability, child_agent, actor, project_id, session_id, arguments, idempotency_key
    ):
        if capability == "reports.generate":
            return {"artifacts": [{"type": "report", "id": str(uuid4())}]}
        if capability == "reviews.enqueue":
            return {"artifacts": [{"type": "review_task", "id": str(uuid4())}]}
        return await super().execute(
            capability=capability,
            child_agent=child_agent,
            actor=actor,
            project_id=project_id,
            session_id=session_id,
            arguments=arguments,
            idempotency_key=idempotency_key,
        )


class TrustLoopReader:
    def __init__(self, status: str = "completed_with_warnings") -> None:
        self.status = status
        self.calls = []

    async def get_summary(self, actor, project_id, run_id):
        self.calls.append((actor, project_id, run_id))
        return {
            "status": self.status,
            "warning_codes": ["diagnostic_model_unavailable"],
            "regressions": [{"candidate_id": str(uuid4()), "state": "published"}],
            "joint_gate": {"decision": "quarantine", "rules": []},
        }


def actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("compiler@example.com"),
        display_name="Compiler",
        role=SystemRole.DEVELOPER,
    )


@pytest.mark.asyncio
async def test_replaying_provision_stage_returns_same_receipt_without_duplicate_assets() -> None:
    receipts = Receipts()
    executor = Executor()
    service = MissionStageService(MissionCompiler(), executor, receipts)
    item = revision()

    first = await service.provision(
        actor=actor(), project_id=ProjectId(item.project_id), session_id=uuid4(), revision=item
    )
    second = await service.provision(
        actor=actor(), project_id=ProjectId(item.project_id), session_id=uuid4(), revision=item
    )

    assert isinstance(first, StageReceipt)
    assert first == second
    assert first.status == "completed"
    assert len(executor.calls) == 8
    assert len({key for _, key, _ in executor.calls}) == 8
    assert {asset[2] for asset in receipts.assets} == {
        "agent_version",
        "dataset_version",
        "scorer",
        "test_plan_version",
    }


@pytest.mark.asyncio
async def test_auth_expiry_pauses_and_resume_attempt_starts_new_idempotent_run() -> None:
    receipts = Receipts()
    executor = Executor()
    service = MissionStageService(MissionCompiler(), executor, receipts)
    item = revision(agent_version_id=str(uuid4()))
    await receipts.save_stage_receipt(
        StageReceipt(
            receipt_id=uuid4(),
            project_id=item.project_id,
            revision_id=item.revision_id,
            stage="provision",
            status="completed",
            output={"test_plan_version_id": str(uuid4())},
            created_at=datetime.now(UTC),
        )
    )
    await service.start_run(
        actor=actor(), project_id=ProjectId(item.project_id), session_id=uuid4(), revision=item
    )

    with pytest.raises(MissionNeedsAttention, match="Browser login expired"):
        await service.await_run(
            actor=actor(),
            project_id=ProjectId(item.project_id),
            session_id=uuid4(),
            revision=item,
        )
    assert (
        await service.await_run(
            actor=actor(),
            project_id=ProjectId(item.project_id),
            session_id=uuid4(),
            revision=item,
            resume_attempt=1,
        )
        is None
    )
    start_calls = [call for call in executor.calls if call[0] == "runs.start"]
    assert len(start_calls) == 2
    assert start_calls[-1][1].endswith(":resume:1")


@pytest.mark.asyncio
async def test_close_loop_consumes_shared_trust_loop_without_duplicate_writes() -> None:
    receipts = Receipts()
    executor = CloseLoopExecutor()
    trust_loop = TrustLoopReader()
    service = MissionStageService(MissionCompiler(), executor, receipts, trust_loop)
    item = revision(agent_version_id=str(uuid4()))
    run_id = uuid4()
    await receipts.save_stage_receipt(
        StageReceipt(
            receipt_id=uuid4(),
            project_id=item.project_id,
            revision_id=item.revision_id,
            stage="await_run",
            status="completed",
            output={"run_id": str(run_id), "run_status": "failed"},
            created_at=datetime.now(UTC),
        )
    )

    receipt = await service.close_loop(
        actor=actor(),
        project_id=ProjectId(item.project_id),
        session_id=uuid4(),
        revision=item,
    )

    assert receipt is not None
    assert receipt.output["trust_loop"]["status"] == "completed_with_warnings"
    assert receipt.output["trust_loop"]["joint_gate"]["decision"] == "quarantine"
    assert not {
        "datasets.create_with_cases",
        "datasets.publish_version",
        "release_gates.list",
        "release_gates.evaluate",
    }.intersection(capability for capability, _, _ in executor.calls)
    assert {asset[2] for asset in receipts.assets} >= {
        "report",
        "review_task",
    }


@pytest.mark.asyncio
async def test_close_loop_waits_while_shared_trust_loop_is_processing() -> None:
    receipts = Receipts()
    executor = CloseLoopExecutor()
    service = MissionStageService(
        MissionCompiler(), executor, receipts, TrustLoopReader(status="running")
    )
    item = revision(agent_version_id=str(uuid4()))
    await receipts.save_stage_receipt(
        StageReceipt(
            receipt_id=uuid4(),
            project_id=item.project_id,
            revision_id=item.revision_id,
            stage="await_run",
            status="completed",
            output={"run_id": str(uuid4()), "run_status": "failed"},
            created_at=datetime.now(UTC),
        )
    )

    receipt = await service.close_loop(
        actor=actor(),
        project_id=ProjectId(item.project_id),
        session_id=uuid4(),
        revision=item,
    )

    assert receipt is None
    assert executor.calls == []
