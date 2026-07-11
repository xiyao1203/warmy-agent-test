from datetime import UTC, datetime
from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_missions.application.compiler import MissionCompiler
from agenttest.modules.test_missions.application.stages import MissionStageService, StageReceipt
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

    async def get_stage_receipt(self, project_id, revision_id, stage):
        return self.items.get((project_id, revision_id, stage))

    async def save_stage_receipt(self, receipt):
        self.items[(receipt.project_id, receipt.revision_id, receipt.stage)] = receipt


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
        }
        kind, value = ids[capability]
        return {"artifacts": [{"type": kind, "id": str(value), "relation": "created"}]}


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
