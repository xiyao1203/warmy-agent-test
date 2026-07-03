from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.application.conversation import ActionIntent
from agenttest.modules.test_agent.domain.entities import RiskLevel, TaskStatus
from pydantic import BaseModel


class Input(BaseModel):
    name: str


class Repo:
    def __init__(self) -> None:
        self.tasks = {}
        self.confirmations = {}
        self.events = []
        self.links = []

    async def add_task(self, task):
        self.tasks[task.task_id] = task

    async def get_task(self, project_id, task_id):
        return self.tasks.get(task_id)

    async def save_task(self, task):
        self.tasks[task.task_id] = task

    async def add_confirmation(self, value):
        self.confirmations[value.confirmation_id] = value

    async def get_confirmation(self, project_id, value_id):
        return self.confirmations.get(value_id)

    async def save_confirmation(self, value):
        self.confirmations[value.confirmation_id] = value

    async def append_event(self, project_id, session_id, event_type, payload, generation_id=None):
        self.events.append((event_type, payload, generation_id))

    async def add_artifact_link(self, link):
        self.links.append(link)


def actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("orchestrator@example.com"),
        display_name="Orchestrator",
        role=SystemRole.DEVELOPER,
    )


@pytest.mark.asyncio
async def test_high_impact_action_waits_for_confirmation_then_creates_real_link() -> None:
    from agenttest.modules.test_agent.application.orchestrator import (
        OrchestrationContext,
        SuperAgentOrchestrator,
    )
    from agenttest.modules.test_agent.application.registry import Capability, CapabilityRegistry

    async def execute(context, payload):
        artifact_id = uuid4()
        return {
            "run_id": str(artifact_id),
            "artifacts": [{"type": "run", "id": str(artifact_id), "relation": "created"}],
        }

    repo = Repo()
    registry = CapabilityRegistry(
        [
            Capability(
                name="runs.start",
                version="1",
                child_agent="execution",
                risk=RiskLevel.HIGH_IMPACT,
                input_model=Input,
                execute=execute,
            )
        ]
    )
    orchestrator = SuperAgentOrchestrator(registry, repo)
    generation_id = uuid4()
    context = OrchestrationContext(actor(), ProjectId.new(), uuid4(), generation_id=generation_id)

    task = await orchestrator.delegate(
        context,
        ActionIntent("runs.start", {"name": "regression"}, "start regression"),
        child_agent="execution",
        idempotency_key="run:start:1",
    )

    assert task.status is TaskStatus.WAITING_CONFIRMATION
    confirmation_id = next(iter(repo.confirmations))

    completed = await orchestrator.decide_confirmation(context, confirmation_id, approved=True)

    assert completed.status is TaskStatus.COMPLETED
    assert repo.links[0].artifact_type == "run"
    assert [event[0] for event in repo.events] == [
        "agent.delegated",
        "tool.confirmation_required",
        "agent.progress",
        "asset.created",
        "agent.completed",
    ]
    assert all(event[2] == generation_id for event in repo.events)
    assert repo.events[1][1]["generation_id"] == str(generation_id)
