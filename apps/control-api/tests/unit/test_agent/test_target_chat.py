from datetime import UTC, datetime

import pytest
from agenttest.modules.agents.public import (
    AgentConfig,
    AgentId,
    AgentVersion,
    AgentVersionId,
    VersionStatus,
)
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.application.target_chat import (
    TargetChatService,
    TargetInvocationResult,
)


class Repository:
    def __init__(self):
        self.sessions = []
        self.turns = []

    async def add_session(self, session):
        self.sessions.append(session)

    async def add_turn(self, turn):
        self.turns.append(turn)


class Runtime:
    def __init__(self):
        self.inputs = []

    async def invoke(self, **payload):
        self.inputs.append(payload)
        return TargetInvocationResult(
            output={"message": "真实回复"},
            trace=[{"name": "http.request"}],
            duration_ms=12,
        )


def actor():
    return User.create(
        user_id=UserId.new(),
        email=Email("target@example.com"),
        display_name="Target Tester",
        role=SystemRole.DEVELOPER,
    )


def version(status=VersionStatus.PUBLISHED):
    now = datetime.now(UTC)
    return AgentVersion(
        version_id=AgentVersionId.new(),
        agent_id=AgentId.new(),
        version_number=1,
        status=status,
        config=AgentConfig(api_url="https://target.example/chat"),
        created_by=UserId.new(),
        created_at=now,
        updated_at=now,
        published_at=now if status is VersionStatus.PUBLISHED else None,
    )


@pytest.mark.asyncio
async def test_target_chat_requires_published_version_and_persists_real_turns():
    repository = Repository()
    runtime = Runtime()
    service = TargetChatService(repository, runtime)
    project_id = ProjectId.new()
    user = actor()

    with pytest.raises(ValueError, match="已发布"):
        await service.create(
            actor=user,
            project_id=project_id,
            version=version(VersionStatus.DRAFT),
            version_project_id=project_id,
            environment=None,
        )

    published = version()
    session = await service.create(
        actor=user,
        project_id=project_id,
        version=published,
        version_project_id=project_id,
        environment=None,
    )
    first = await service.send(
        project_id=project_id,
        session=session,
        version=published,
        environment=None,
        message="你好",
    )
    second = await service.send(
        project_id=project_id,
        session=session,
        version=published,
        environment=None,
        message="继续",
    )

    assert first.output == {"message": "真实回复"}
    assert first.duration_ms == 12
    assert second.sequence == 2
    assert runtime.inputs[1]["input"]["history"] == [
        {"input": {"message": "你好", "history": []}, "output": {"message": "真实回复"}}
    ]
    assert repository.turns == [first, second]
