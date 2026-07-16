from types import SimpleNamespace
from uuid import uuid4

import pytest
from agenttest.modules.agents.public import Agent, AgentId, AgentType
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.adapters.platform import HandlerPlatformGateway
from agenttest.modules.test_agent.application.orchestrator import OrchestrationContext
from agenttest.modules.test_agent.application.platform_catalog import QueryInput
from agenttest.shared.application.core_summaries import AgentSummaryMetrics
from agenttest.shared.application.resource_reference import (
    ResourceReference,
    ResourceType,
)


class ListAgents:
    def __init__(self, agent: Agent) -> None:
        self.agent = agent

    async def execute(self, actor: User, project_id: ProjectId):
        return [self.agent], 1


class Summaries:
    def __init__(self, version_ref: ResourceReference) -> None:
        self.version_ref = version_ref

    async def agents(self, project_id, ids):
        assert ids == [self.version_ref.id]
        return {
            ids[0]: AgentSummaryMetrics(
                current_version=self.version_ref,
                version_status="published",
                protocol="generic_http",
                model="gpt-5",
                tool_count=4,
                connection_status="ready",
                pass_rate=0.92,
            )
        }


def _actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("platform-summary@example.com"),
        display_name="Platform Summary",
        role=SystemRole.DEVELOPER,
    )


@pytest.mark.asyncio
async def test_agent_list_uses_shared_summary_and_safe_resource_reference() -> None:
    project_id = ProjectId.new()
    actor = _actor()
    agent = Agent.create(
        agent_id=AgentId.new(),
        project_id=project_id,
        name="Checkout Agent",
        agent_type=AgentType.GENERIC_HTTP,
        created_by=actor.user_id,
    )
    version_ref = ResourceReference.build(
        resource_type=ResourceType.AGENT_VERSION,
        resource_id=agent.agent_id.value,
        project_id=project_id.value,
        parent_id=agent.agent_id.value,
        name="Checkout Agent v3",
        version=3,
        status="published",
    )
    gateway = HandlerPlatformGateway(
        agents=SimpleNamespace(list_agents=ListAgents(agent)),
        datasets=None,
        environments=None,
        plans=None,
        runs=None,
        scorers=None,
        experiments=None,
        reviews=None,
        gates=None,
        security=None,
        accounts=None,
        promptfoo_bin="promptfoo",
        allow_private_security_targets=False,
        gate_evidence=None,
        summaries=Summaries(version_ref),
    )

    result = await gateway.execute(
        "agents.list",
        OrchestrationContext(actor, project_id, uuid4()),
        QueryInput(),
    )

    item = result["items"][0]
    assert item["pass_rate"] == 0.92
    assert item["current_version"]["version"] == 3
    assert item["resource_ref"] == {
        "resource_type": "agent",
        "id": str(agent.agent_id.value),
        "key": None,
        "name": "Checkout Agent",
        "version": None,
        "status": None,
        "href": f"/projects/{project_id.value}/agents/{agent.agent_id.value}",
    }
