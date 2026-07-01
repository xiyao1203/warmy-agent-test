from __future__ import annotations

import json

import httpx
import pytest
from agenttest_api_runner.adapter import (
    AgentRequest,
    GenericHttpAgentAdapter,
    TargetProductError,
)


@pytest.mark.asyncio
async def test_adapter_executes_sync_json_and_redacts_headers() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer secret"
        return httpx.Response(
            200,
            json={
                "output": {"message": "hello world"},
                "tool_calls": [{"name": "search", "arguments": {"q": "hello"}}],
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    adapter = GenericHttpAgentAdapter(client=client)
    result = await adapter.execute(
        AgentRequest(
            url="https://agent.example/run",
            mode="sync",
            headers={"Authorization": "Bearer secret"},
            input={"message": "hello"},
            timeout_seconds=5,
        )
    )

    assert result.output == {"message": "hello world"}
    assert result.tool_calls[0]["name"] == "search"
    assert result.trace[0]["attributes"]["http.request.header.authorization"] == "***"
    await client.aclose()


@pytest.mark.asyncio
async def test_adapter_parses_sse_stream() -> None:
    body = "\n".join(
        [
            f"data: {json.dumps({'type': 'message.delta', 'delta': 'hello '})}",
            "",
            f"data: {json.dumps({'type': 'message.delta', 'delta': 'world'})}",
            "",
            f"data: {json.dumps({'type': 'tool.call', 'name': 'search'})}",
            "",
            "data: [DONE]",
            "",
        ]
    )

    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    result = await GenericHttpAgentAdapter(client=client).execute(
        AgentRequest(
            url="https://agent.example/stream",
            mode="stream",
            input={"message": "hello"},
        )
    )

    assert result.output == {"message": "hello world"}
    assert result.tool_calls == [{"type": "tool.call", "name": "search"}]
    await client.aclose()


@pytest.mark.asyncio
async def test_adapter_classifies_target_error() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"detail": "invalid prompt"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    with pytest.raises(TargetProductError, match="422"):
        await GenericHttpAgentAdapter(client=client).execute(
            AgentRequest(
                url="https://agent.example/run",
                mode="sync",
                input={"message": "bad"},
            )
        )
    await client.aclose()


@pytest.mark.asyncio
async def test_adapter_renders_request_template_and_extracts_response_path() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content) == {
            "messages": [{"role": "user", "content": "hello"}],
            "tenant": "staging",
        }
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "hello world"}}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    result = await GenericHttpAgentAdapter(client=client).execute(
        AgentRequest(
            url="https://agent.example/v1/chat",
            input={"message": "hello"},
            variables={"tenant": "staging"},
            request_template={
                "messages": [{"role": "user", "content": "{{ input.message }}"}],
                "tenant": "{{ env.tenant }}",
            },
            response_path="choices.0.message.content",
        )
    )

    assert result.output == {"value": "hello world"}
    await client.aclose()
