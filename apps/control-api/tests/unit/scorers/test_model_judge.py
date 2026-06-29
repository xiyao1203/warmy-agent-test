"""真实文本和视觉模型裁判测试。"""

import json

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.model_configs.application.ports import InvocationResult
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.scorers.application.model_judge import ModelJudge


class Models:
    async def resolve_default(self, actor, project_id, purpose):
        return type(
            "Config",
            (),
            {
                "model_config_id": type("Id", (), {"value": __import__("uuid").uuid4()})(),
                "provider_type": type("Provider", (), {"value": "openai_compatible"})(),
                "model_name": "judge-a",
            },
        )()


class Invoker:
    def __init__(self) -> None:
        self.messages = []

    async def invoke(self, config, messages, **kwargs):
        self.messages = messages
        return InvocationResult(
            content=json.dumps(
                {
                    "score": 0.9,
                    "passed": True,
                    "explanation": "符合要求",
                    "confidence": 0.8,
                    "evidence": ["关键事实一致"],
                }
            ),
            total_tokens=12,
            latency_ms=30,
        )


def actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("judge@example.com"),
        display_name="Judge",
        role=SystemRole.TESTER,
    )


@pytest.mark.asyncio
async def test_text_judge_returns_score_and_model_snapshot() -> None:
    result = await ModelJudge(Models(), Invoker()).judge_text(
        actor(),
        ProjectId.new(),
        input_text="问题",
        output_text="回答",
        rubric="是否正确",
    )
    assert result.score == 0.9
    assert result.model_name == "judge-a"
    assert result.total_tokens == 12


@pytest.mark.asyncio
async def test_vision_judge_sends_image_content() -> None:
    invoker = Invoker()
    await ModelJudge(Models(), invoker).judge_vision(
        actor(),
        ProjectId.new(),
        prompt="商品图",
        image_data_url="data:image/png;base64,AAAA",
        rubric="主体一致",
    )
    content = invoker.messages[-1].content
    assert isinstance(content, list)
    assert content[1]["type"] == "image_url"


@pytest.mark.asyncio
async def test_vision_judge_rejects_external_image_url() -> None:
    with pytest.raises(ValueError, match="data URL"):
        await ModelJudge(Models(), Invoker()).judge_vision(
            actor(),
            ProjectId.new(),
            prompt="图",
            image_data_url="https://example.com/image.png",
            rubric="质量",
        )
