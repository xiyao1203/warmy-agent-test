from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.application.mission_executor import (
    ConfirmedMissionAssetExecutor,
)
from agenttest.modules.test_agent.application.platform_catalog import capability_specs
from agenttest.modules.test_agent.application.sub_agents import SubAgentName, get_sub_agent
from agenttest.modules.test_agent.domain.entities import RiskLevel


def test_mission_subagent_owns_single_confirmation_full_chain_capabilities() -> None:
    specs = {item.name: item for item in capability_specs()}

    assert specs["test_missions.create_or_update"].child_agent == "mission"
    assert specs["test_missions.create_or_update"].risk is RiskLevel.READ
    assert specs["test_missions.preview"].risk is RiskLevel.READ
    assert specs["test_missions.confirm_and_start"].risk is RiskLevel.HIGH_IMPACT
    assert get_sub_agent(SubAgentName.MISSION).name is SubAgentName.MISSION


@pytest.mark.asyncio
async def test_confirmed_mission_propagates_action_idempotency_key() -> None:
    captured = {}

    class Capability:
        async def execute(self, context, payload):
            captured["key"] = context.idempotency_key
            return {"ok": True}

    class Registry:
        def resolve(self, child_agent, capability, arguments):
            del child_agent, capability
            return Capability(), arguments

    actor = User.create(
        user_id=UserId.new(),
        email=Email("mission-idempotency@example.com"),
        display_name="Mission Idempotency",
        role=SystemRole.DEVELOPER,
    )
    await ConfirmedMissionAssetExecutor(Registry()).execute(
        capability="runs.start",
        child_agent="execution",
        actor=actor,
        project_id=ProjectId.new(),
        session_id=uuid4(),
        arguments={"test_plan_version_id": str(uuid4())},
        idempotency_key="mission:revision:start-run",
    )

    assert captured["key"] == "mission:revision:start-run"
