"""真实模型测试计划生成器测试。"""

import json
from uuid import uuid4

import pytest
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.model_configs.application.ports import InvocationResult
from agenttest.modules.model_configs.domain.errors import ModelDefaultMissingError
from agenttest.modules.projects.public import ProjectId
from agenttest.modules.test_agent.application.model_planner import ModelTestPlanGenerator


class Models:
    async def resolve_default(self, actor, project_id, purpose):
        return type("Config", (), {"model_name": "model-a"})()


class MissingModels:
    async def resolve_default(self, actor, project_id, purpose):
        raise ModelDefaultMissingError


class Invoker:
    async def invoke(self, config, messages, **kwargs):
        return InvocationResult(
            content=json.dumps(
                {
                    "name": "登录回归",
                    "description": "验证登录",
                    "estimated_cases": 5,
                    "estimated_duration_min": 2,
                    "scorers": ["exact_match"],
                    "agent_version_id": None,
                    "dataset_id": None,
                    "environment_id": None,
                }
            )
        )


def actor() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("planner@example.com"),
        display_name="Planner",
        role=SystemRole.DEVELOPER,
    )


@pytest.mark.asyncio
async def test_generates_strict_plan_from_real_invocation_port() -> None:
    result = await ModelTestPlanGenerator(Models(), Invoker()).generate(
        actor(),
        ProjectId(uuid4()),
        "测试登录",
    )
    assert result["name"] == "登录回归"
    assert result["estimated_cases"] == 5


@pytest.mark.asyncio
async def test_missing_project_default_fails_without_fallback() -> None:
    with pytest.raises(ModelDefaultMissingError):
        await ModelTestPlanGenerator(MissingModels(), Invoker()).generate(
            actor(),
            ProjectId(uuid4()),
            "测试登录",
        )
