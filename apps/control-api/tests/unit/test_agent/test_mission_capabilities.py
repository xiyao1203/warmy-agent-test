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
