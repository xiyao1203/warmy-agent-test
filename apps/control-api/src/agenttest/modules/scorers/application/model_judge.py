"""使用项目默认真实模型执行文本与视觉裁判。"""

from __future__ import annotations

import json
from dataclasses import dataclass
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
    async def resolve_default(
        self,
        actor: User,
        project_id: ProjectId,
        purpose: ModelPurpose,
    ) -> ModelConfiguration: ...


class JudgePayload(BaseModel):
    """模型裁判必须返回的可解释评分结构。"""

    score: float = Field(ge=0, le=1)
    passed: bool
    explanation: str = Field(min_length=1, max_length=4000)
    confidence: float = Field(ge=0, le=1)
    evidence: list[str] = Field(default_factory=list, max_length=20)


@dataclass(frozen=True, slots=True)
class ModelJudgeResult:
    """包含可复现模型快照的裁判结果。"""

    score: float
    passed: bool
    explanation: str
    confidence: float
    evidence: list[str]
    model_config_id: str
    provider_type: str
    model_name: str
    total_tokens: int
    latency_ms: int


class InvalidJudgeResultError(Exception):
    """模型输出不是合法裁判结果。"""


class ModelJudge:
    """文本和视觉 LLM-as-a-Judge 应用服务。"""

    def __init__(self, models: DefaultModelResolver, invoker: ModelInvoker) -> None:
        self._models = models
        self._invoker = invoker

    async def judge_text(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        input_text: str,
        output_text: str,
        rubric: str,
    ) -> ModelJudgeResult:
        """使用项目文本裁判默认模型评分。"""

        config = await self._models.resolve_default(actor, project_id, ModelPurpose.TEXT_JUDGE)
        content = f"评分标准：{rubric}\n输入：{input_text}\n待评输出：{output_text}"
        result = await self._invoke(config, [InvocationMessage(role="user", content=content)])
        return self._result(config, result)

    async def judge_vision(
        self,
        actor: User,
        project_id: ProjectId,
        *,
        prompt: str,
        image_data_url: str,
        rubric: str,
    ) -> ModelJudgeResult:
        """使用项目视觉裁判默认模型评分内嵌图片。"""

        if not image_data_url.startswith("data:image/"):
            raise ValueError("视觉裁判图片必须使用 data URL")
        config = await self._models.resolve_default(actor, project_id, ModelPurpose.VISION_JUDGE)
        content: list[dict[str, object]] = [
            {"type": "text", "text": f"评分标准：{rubric}\n原始提示：{prompt}"},
            {"type": "image_url", "image_url": {"url": image_data_url}},
        ]
        result = await self._invoke(config, [InvocationMessage(role="user", content=content)])
        return self._result(config, result)

    async def _invoke(self, config: ModelConfiguration, messages: list[InvocationMessage]):
        system = InvocationMessage(
            role="system",
            content=(
                "你是严格的质量裁判。只返回 JSON：score(0-1)、passed、explanation、"
                "confidence(0-1)、evidence(字符串数组)。不要输出 Markdown。"
            ),
        )
        return await self._invoker.invoke(
            config,
            [system, *messages],
            response_format={"type": "json_object"},
            timeout_seconds=60,
            max_tokens=2048,
        )

    @staticmethod
    def _result(config: ModelConfiguration, invocation) -> ModelJudgeResult:
        try:
            payload = JudgePayload.model_validate(json.loads(invocation.content))
        except (json.JSONDecodeError, ValidationError) as error:
            raise InvalidJudgeResultError("模型返回的评分结构无效") from error
        return ModelJudgeResult(
            **payload.model_dump(),
            model_config_id=str(config.model_config_id.value),
            provider_type=config.provider_type.value,
            model_name=config.model_name,
            total_tokens=invocation.total_tokens,
            latency_ms=invocation.latency_ms,
        )
