from __future__ import annotations

import httpx
import pytest
import pytest_asyncio

from tests.fake_agent_target.app import create_fake_target_app
from tests.fake_agent_target.state import FakeTargetState


@pytest.fixture
def state() -> FakeTargetState:
    return FakeTargetState()


@pytest_asyncio.fixture
async def client(state: FakeTargetState):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_fake_target_app(state)),
        base_url="http://fake-target.test",
    ) as value:
        yield value


@pytest.mark.asyncio
async def test_transient_failure_is_deterministic(
    client: httpx.AsyncClient, state: FakeTargetState
) -> None:
    configured = await client.post(
        "/control/scenario", json={"name": "transient_failure", "failures": 1}
    )
    assert configured.status_code == 200

    first = await client.post("/api/agent/invoke", json={"input": "hello"})
    second = await client.post("/api/agent/invoke", json={"input": "hello"})

    assert first.status_code == 503
    assert second.status_code == 200
    assert second.json()["evidence"]["scenario"] == "transient_failure"
    assert second.json()["evidence"]["attempt"] == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("scenario", "status", "error_code"),
    [
        ("product_error", 422, "target_product_error"),
        ("protocol_error", 502, "target_protocol_error"),
        ("auth_expired", 401, "auth_expired"),
        ("quota_exceeded", 429, "quota_exceeded"),
        ("incomplete_artifact", 200, None),
        ("prompt_injection", 200, None),
        ("data_leak_attempt", 200, None),
        ("privilege_escalation", 200, None),
    ],
)
async def test_scenarios_have_stable_observations(
    client: httpx.AsyncClient,
    scenario: str,
    status: int,
    error_code: str | None,
) -> None:
    await client.post("/control/scenario", json={"name": scenario})
    response = await client.post("/api/agent/invoke", json={"input": "test request"})

    assert response.status_code == status
    payload = response.json()
    assert payload["evidence"]["scenario"] == scenario
    if error_code is not None:
        assert payload["error"]["code"] == error_code

    observations = (await client.get("/control/observations")).json()
    assert observations["requests"][-1]["scenario"] == scenario


@pytest.mark.asyncio
async def test_browser_chat_preserves_multiturn_state(client: httpx.AsyncClient) -> None:
    page = await client.get("/chat")
    assert page.status_code == 200
    assert "Fake Agent Target" in page.text

    first = await client.post("/chat/messages", json={"message": "first"})
    second = await client.post("/chat/messages", json={"message": "second"})

    assert first.json()["turn"] == 1
    assert second.json()["turn"] == 2
    assert second.json()["history"] == ["first", "second"]


@pytest.mark.asyncio
async def test_root_endpoint_supports_discovered_generic_agent_url(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post("/", json={"input": "hello"})
    assert response.status_code == 200
    assert response.json()["output"] == "Echo: hello"


@pytest.mark.asyncio
async def test_root_endpoint_accepts_structured_platform_case_input(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post("/", json={"input": {"prompt": "hello", "turn": 1}})
    assert response.status_code == 200
    assert "hello" in response.json()["output"]
