from uuid import uuid4

import pytest
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.application.generations import GenerationCoordinator
from agenttest.modules.test_agent.domain.entities import (
    ChatGeneration,
    ChatSessionId,
    GenerationStatus,
)


class Generations:
    def __init__(self) -> None:
        self.items: dict[object, ChatGeneration] = {}

    async def add(self, generation: ChatGeneration) -> None:
        if generation.generation_id in self.items:
            raise ValueError("duplicate")
        self.items[generation.generation_id] = generation

    async def get(self, project_id, generation_id):
        item = self.items.get(generation_id)
        return item if item and item.project_id == project_id.value else None

    async def get_active(self, project_id, session_id):
        return next(
            (
                item
                for item in self.items.values()
                if item.project_id == project_id.value
                and item.session_id == session_id.value
                and item.status
                in {
                    GenerationStatus.PENDING,
                    GenerationStatus.RUNNING,
                    GenerationStatus.CANCELLING,
                }
            ),
            None,
        )

    async def save(self, generation):
        self.items[generation.generation_id] = generation


class Events:
    def __init__(self) -> None:
        self.types: list[str] = []

    async def append_event(self, _project, _session, event_type, _payload, **_kwargs):
        self.types.append(event_type)


class Invoker:
    def __init__(self) -> None:
        self.cancelled: list[str] = []

    async def cancel_workflow(self, workflow_id: str) -> None:
        self.cancelled.append(workflow_id)


@pytest.mark.asyncio
async def test_begin_is_idempotent_and_rejects_parallel_generation() -> None:
    repository = Generations()
    coordinator = GenerationCoordinator(repository, Events(), Invoker())
    project_id = ProjectId.new()
    session_id = ChatSessionId.new()
    generation_id = uuid4()

    first = await coordinator.begin(project_id, session_id, generation_id)
    second = await coordinator.begin(project_id, session_id, generation_id)

    assert first.generation_id == second.generation_id
    with pytest.raises(ValueError, match="already active"):
        await coordinator.begin(project_id, session_id, uuid4())


@pytest.mark.asyncio
async def test_cancel_requests_temporal_and_converges_idempotently() -> None:
    repository = Generations()
    events = Events()
    invoker = Invoker()
    coordinator = GenerationCoordinator(repository, events, invoker)
    project_id = ProjectId.new()
    session_id = ChatSessionId.new()
    generation = await coordinator.begin(project_id, session_id, uuid4())
    await coordinator.start(generation)

    first = await coordinator.cancel(project_id, session_id, generation.generation_id)
    second = await coordinator.cancel(project_id, session_id, generation.generation_id)

    assert first.status is second.status is GenerationStatus.CANCELLING
    assert invoker.cancelled == [generation.workflow_id]
    assert events.types[-1] == "generation.cancelling"
