from __future__ import annotations

import pytest
from agenttest.modules.model_configs.public import InvocationResult
from agenttest.modules.test_agent.application.super_agent import _make_read_tool
from agenttest.modules.test_agent.application.temporal_model import TemporalModel
from pydantic import BaseModel
from pydantic_ai.messages import ModelRequest, UserPromptPart
from pydantic_ai.models import ModelRequestParameters


class _Invoker:
    async def invoke(self, config, messages, **kwargs):
        return InvocationResult(
            content="ok",
            prompt_tokens=11,
            completion_tokens=7,
            total_tokens=18,
        )


class _ReadInput(BaseModel):
    query: str = ""


@pytest.mark.asyncio
async def test_temporal_model_returns_request_usage_and_provider_metadata() -> None:
    model = TemporalModel(invoker=_Invoker(), config=object(), display_name="model-a")

    response = await model.request(
        [ModelRequest(parts=[UserPromptPart("hello")])],
        None,
        ModelRequestParameters(),
    )

    assert response.usage.input_tokens == 11
    assert response.usage.output_tokens == 7
    assert response.usage.total_tokens == 18
    assert response.provider_name == "temporal"


def test_read_tool_builds_named_function_schema() -> None:
    tool = _make_read_tool("agents.list", _ReadInput)

    assert tool.name == "agents_list"
    assert tool.function_schema.name == "agents_list"
