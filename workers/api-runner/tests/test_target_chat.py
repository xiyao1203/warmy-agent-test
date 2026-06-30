import httpx
import pytest
from agenttest_api_runner import target_chat
from agenttest_api_runner.adapter import GenericHttpAgentAdapter


@pytest.mark.asyncio
async def test_target_chat_activity_uses_real_adapter_and_redacts_credentials(monkeypatch):
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer secret"
        return httpx.Response(200, json={"output": {"message": "真实回复"}})

    adapter = GenericHttpAgentAdapter(
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    monkeypatch.setattr(target_chat, "GenericHttpAgentAdapter", lambda: adapter)
    monkeypatch.setattr(target_chat.activity, "heartbeat", lambda details: None)

    result = await target_chat.execute_target_chat(
        {
            "url": "https://target.example/chat",
            "mode": "sync",
            "headers": {"Authorization": "Bearer secret"},
            "input": {"message": "你好"},
        }
    )

    assert result["output"] == {"message": "真实回复"}
    assert result["trace"][0]["attributes"]["http.request.header.authorization"] == "***"
