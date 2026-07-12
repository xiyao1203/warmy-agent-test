"""OpenAI-Compatible 真实协议适配器测试。"""

import asyncio
import json
from dataclasses import replace
from types import SimpleNamespace

import httpx
import pytest
from agenttest_model_runner.activities import ModelActivities
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

    assert chunks == [("content", "你"), ("content", "好")]


@pytest.mark.asyncio
async def test_stream_separates_reasoning_from_content() -> None:
    async def handler(http_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text=(
                'data: {"choices":[{"delta":{"reasoning_content":"让我想想"}}]}\n\n'
                'data: {"choices":[{"delta":{"content":"你好"}}]}\n\n'
                "data: [DONE]\n\n"
            ),
        )

    adapter = OpenAICompatibleAdapter(transport=httpx.MockTransport(handler))

    chunks = [chunk async for chunk in adapter.stream(request())]

    assert chunks == [("reasoning", "让我想想"), ("content", "你好")]


@pytest.mark.asyncio
async def test_stream_activity_marks_cancelled_and_preserves_partial(monkeypatch) -> None:
    activities = ModelActivities("unused")

    async def stream(_request):
        yield "content", "partial"
        raise asyncio.CancelledError

    monkeypatch.setattr(activities._adapter, "stream", stream)
    monkeypatch.setattr(
        "agenttest_model_runner.activities.decrypt_credential", lambda *_args: "key"
    )
    monkeypatch.setattr("agenttest_model_runner.activities.activity.heartbeat", lambda *_args: None)
    monkeypatch.setattr(
        "agenttest_model_runner.activities.activity.logger",
        SimpleNamespace(warning=lambda *_args: None),
    )

    result = await activities.stream_model(
        {
            "encrypted_api_key": "encrypted",
            "base_url": "https://model.example/v1",
            "model_name": "model",
            "messages": [{"role": "user", "content": "hi"}],
            "timeout_seconds": 60,
        }
    )

    assert result == {"content": "partial", "cancelled": True}


@pytest.mark.asyncio
async def test_stream_activity_falls_back_to_non_stream_when_provider_returns_only_reasoning(
    monkeypatch,
) -> None:
    activities = ModelActivities("unused")

    async def stream(_request):
        yield "reasoning", "内部推理不应作为最终回复"

    async def invoke(_request):
        return SimpleNamespace(content="你好，我可以帮你测试 Agent。")

    monkeypatch.setattr(activities._adapter, "stream", stream)
    monkeypatch.setattr(activities._adapter, "invoke", invoke)
    monkeypatch.setattr(
        "agenttest_model_runner.activities.decrypt_credential", lambda *_args: "key"
    )
    monkeypatch.setattr("agenttest_model_runner.activities.activity.heartbeat", lambda *_args: None)

    result = await activities.stream_model(
        {
            "encrypted_api_key": "encrypted",
            "base_url": "https://model.example/v1",
            "model_name": "reasoning-model",
            "messages": [{"role": "user", "content": "你好"}],
            "timeout_seconds": 60,
        }
    )

    assert result == {
        "content": "你好，我可以帮你测试 Agent。",
        "cancelled": False,
    }


@pytest.mark.asyncio
async def test_stream_activity_bounds_stream_wait_and_falls_back_on_timeout(
    monkeypatch,
) -> None:
    activities = ModelActivities("unused")
    seen: dict[str, float] = {}

    async def stream(stream_request):
        seen["stream_timeout"] = stream_request.timeout_seconds
        if False:
            yield "content", "unreachable"
        raise ModelTransientError("stream timed out")

    async def invoke(invoke_request):
        seen["invoke_timeout"] = invoke_request.timeout_seconds
        return SimpleNamespace(content="你好，有什么需要测试的？")

    monkeypatch.setattr(activities._adapter, "stream", stream)
    monkeypatch.setattr(activities._adapter, "invoke", invoke)
    monkeypatch.setattr(
        "agenttest_model_runner.activities.decrypt_credential", lambda *_args: "key"
    )
    monkeypatch.setattr("agenttest_model_runner.activities.activity.heartbeat", lambda *_args: None)

    result = await activities.stream_model(
        {
            "encrypted_api_key": "encrypted",
            "base_url": "https://model.example/v1",
            "model_name": "slow-streaming-model",
            "messages": [{"role": "user", "content": "你好"}],
            "timeout_seconds": 60,
        }
    )

    assert seen == {"stream_timeout": 15, "invoke_timeout": 10}
    assert result == {"content": "你好，有什么需要测试的？", "cancelled": False}


@pytest.mark.asyncio
async def test_stream_activity_limits_total_stream_window(monkeypatch) -> None:
    activities = ModelActivities("unused")

    async def stream(_request):
        yield "content", "迟到"
        await asyncio.sleep(0.05)
        yield "content", "的正文"

    async def invoke(_request):
        return SimpleNamespace(content="及时的非流式回复")

    monkeypatch.setattr(activities._adapter, "stream", stream)
    monkeypatch.setattr(activities._adapter, "invoke", invoke)
    monkeypatch.setattr(
        "agenttest_model_runner.activities.decrypt_credential", lambda *_args: "key"
    )
    monkeypatch.setattr("agenttest_model_runner.activities.activity.heartbeat", lambda *_args: None)

    result = await activities.stream_model(
        {
            "encrypted_api_key": "encrypted",
            "base_url": "https://model.example/v1",
            "model_name": "slow-streaming-model",
            "messages": [{"role": "user", "content": "你好"}],
            "timeout_seconds": 0.01,
        }
    )

    assert result == {"content": "及时的非流式回复", "cancelled": False}
