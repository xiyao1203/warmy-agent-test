"""使用项目默认真实模型生成结构化测试计划。"""

from __future__ import annotations

import json
from typing import Protocol

from pydantic import BaseModel, Field, ValidationError

from agenttest.modules.identity.public import User
from agenttest.modules.model_configs.public import (
    InvocationMessage,
    ModelConfiguration,
    ModelInvoker,
    ModelPurpose,
)
from agenttest.modules.projects.public import ProjectId


class DefaultModelResolver(Protocol):
    """解析项目默认模型的公开应用能力。"""

    async def resolve_default(
        self,
        actor: User,
        project_id: ProjectId,
        purpose: ModelPurpose,
    ) -> ModelConfiguration: ...


class GeneratedTestPlan(BaseModel):
    """测试 Agent 允许模型生成的严格计划结构。"""

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2000)
    estimated_cases: int = Field(ge=1, le=500)
    estimated_duration_min: int = Field(ge=1, le=1440)
    scorers: list[str] = Field(min_length=1, max_length=20)
    agent_version_id: str | None = None
    dataset_id: str | None = None
    environment_id: str | None = None


class InvalidModelPlanError(Exception):
    """模型输出无法转换为合法测试计划。"""


class ModelTestPlanGenerator:
    """通过 Model Runner 生成并校验测试计划。"""

    def __init__(self, models: DefaultModelResolver, invoker: ModelInvoker) -> None:
        self._models = models
        self._invoker = invoker

    async def generate(
        self,
        actor: User,
        project_id: ProjectId,
        user_message: str,
    ) -> dict[str, object]:
        """调用项目默认 Test Agent 模型，不提供任何静态回退。"""

        config = await self._models.resolve_default(
            actor,
            project_id,
            ModelPurpose.TEST_AGENT_CHAT,
        )
        system_prompt = (
            "你是 Agent 自动化测试平台的测试计划生成器。"
            "只返回 JSON 对象，字段必须为 name、description、estimated_cases、"
            "estimated_duration_min、scorers、agent_version_id、dataset_id、environment_id。\n"
            "estimated_cases 范围 1-500。\n"
            "scorers 必须是字符串数组（如 [\"功能正确性\", \"性能\"]），不能是对象数组。\n"
            "不要输出 Markdown，只输出纯 JSON。"
        )
        result = await self._invoker.invoke(
            config,
            [
                InvocationMessage(role="system", content=system_prompt),
                InvocationMessage(role="user", content=user_message),
            ],
            response_format={"type": "json_object"},
            timeout_seconds=60,
            max_tokens=2048,
        )
        try:
            plan = GeneratedTestPlan.model_validate(json.loads(result.content))
        except (json.JSONDecodeError, ValidationError) as error:
            raise InvalidModelPlanError("模型返回的测试计划结构无效") from error
        return plan.model_dump()
