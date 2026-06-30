"""OpenAI-Compatible 真实协议适配器测试。"""

import json
from dataclasses import replace

import httpx
import pytest
from agenttest_model_runner.adapter import (
    ModelPermissionError,
    ModelProtocolError,
    ModelTransientError,
    OpenAICompatibleAdapter,
)
from agenttest_model_runner.contracts import ChatMessage, ModelInvocationRequest


def request() -> ModelInvocationRequest:
    return ModelInvocationRequest(
        base_url="https://api.example.com/v1",
        model_name="model-a",
        api_key="sk-real-secret",
        messages=[ChatMessage(role="user", content="hello")],
        response_format={"type": "json_object"},
        timeout_seconds=10,
    )


@pytest.mark.asyncio
async def test_sends_openai_compatible_request_and_returns_usage() -> None:
    seen = {}

    async def handler(http_request: httpx.Request) -> httpx.Response:
        seen["url"] = str(http_request.url)
        seen["authorization"] = http_request.headers["Authorization"]
        seen["body"] = json.loads(http_request.content)
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": '{"name":"plan"}'}}],
                "usage": {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10},
            },
        )

    adapter = OpenAICompatibleAdapter(transport=httpx.MockTransport(handler))
    result = await adapter.invoke(request())

    assert seen["url"] == "https://api.example.com/v1/chat/completions"
    assert seen["authorization"] == "Bearer sk-real-secret"
    assert seen["body"]["model"] == "model-a"
    assert seen["body"]["response_format"] == {"type": "json_object"}
    assert result.content == '{"name":"plan"}'
    assert result.total_tokens == 10


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,error",
    [
        (401, ModelPermissionError),
        (403, ModelPermissionError),
        (429, ModelTransientError),
        (500, ModelTransientError),
    ],
)
async def test_classifies_upstream_status(status: int, error: type[Exception]) -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"error": {"message": "secret must not leak"}})

    adapter = OpenAICompatibleAdapter(transport=httpx.MockTransport(handler))
    with pytest.raises(error) as captured:
        await adapter.invoke(request())
    assert "secret must not leak" not in str(captured.value)


@pytest.mark.asyncio
async def test_rejects_invalid_success_payload_without_fallback() -> None:
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": []})

    adapter = OpenAICompatibleAdapter(transport=httpx.MockTransport(handler))
    with pytest.raises(ModelProtocolError):
        await adapter.invoke(request())


@pytest.mark.asyncio
async def test_rejects_cloud_metadata_and_private_literal_addresses() -> None:
    adapter = OpenAICompatibleAdapter()
    with pytest.raises(ModelProtocolError, match="网络"):
        await adapter.invoke(replace(request(), base_url="http://169.254.169.254/latest"))


@pytest.mark.asyncio
async def test_stream_yields_real_provider_deltas_in_order() -> None:
    async def handler(http_request: httpx.Request) -> httpx.Response:
        assert http_request.url.path.endswith("/chat/completions")
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text=(
                'data: {"choices":[{"delta":{"content":"你"}}]}\n\n'
                'data: {"choices":[{"delta":{"content":"好"}}]}\n\n'
                "data: [DONE]\n\n"
            ),
        )

    adapter = OpenAICompatibleAdapter(transport=httpx.MockTransport(handler))

    chunks = [chunk async for chunk in adapter.stream(request())]

    assert chunks == ["你", "好"]
