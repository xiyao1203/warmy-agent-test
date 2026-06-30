from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.model_configs.application.ports import InvocationResult
from agenttest.modules.projects.public import ProjectId


class Models:
    async def resolve_default(self, actor, project_id, purpose):
        return type("Config", (), {"model_name": "model-a"})()


class Invoker:
    def __init__(self) -> None:
        self.messages = []

    async def invoke(self, config, messages, **kwargs):
        self.messages = messages
        return InvocationResult(content="你好，我是项目测试 Agent。你想测试哪个智能体？")


def actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("super-agent@example.com"),
        display_name="Super Agent User",
        role=SystemRole.DEVELOPER,
    )


@pytest.mark.asyncio
async def test_greeting_returns_real_provider_content_without_fabricated_plan() -> None:
    from agenttest.modules.test_agent.application.conversation import SuperAgentConversation

    invoker = Invoker()
    conversation = SuperAgentConversation(Models(), invoker)

    response = await conversation.respond(
        actor(),
        ProjectId(uuid4()),
        history=[("user", "你好")],
    )

    assert response.content == "你好，我是项目测试 Agent。你想测试哪个智能体？"
    assert "已生成测试计划" not in response.content
    assert response.actions == []


@pytest.mark.asyncio
async def test_conversation_sends_complete_history_to_model() -> None:
    from agenttest.modules.test_agent.application.conversation import SuperAgentConversation

    invoker = Invoker()
    conversation = SuperAgentConversation(Models(), invoker)

    await conversation.respond(
        actor(),
        ProjectId(uuid4()),
        history=[
            ("user", "测试登录"),
            ("assistant", "请提供被测 Agent"),
            ("user", "使用 v2.3"),
        ],
    )

    assert [(message.role, message.content) for message in invoker.messages[1:]] == [
        ("user", "测试登录"),
        ("assistant", "请提供被测 Agent"),
        ("user", "使用 v2.3"),
    ]
