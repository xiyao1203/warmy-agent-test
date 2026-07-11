from uuid import uuid4

import httpx
import pytest
from agenttest_api_runner.browser_sessions import BrowserSessionLeaseClient


@pytest.mark.asyncio
async def test_browser_session_client_redeems_scoped_storage_state() -> None:
    project_id, run_id, case_id, profile_id = (str(uuid4()) for _ in range(4))

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == (
            f"/api/v1/internal/projects/{project_id}/browser-session-leases:redeem"
        )
        assert request.headers["X-Internal-Token"] == "internal"
        assert b"cookie" not in request.content.lower()
        return httpx.Response(
            200,
            json={
                "storage_state": {
                    "cookies": [{"name": "session", "value": "secret"}],
                    "origins": [],
                },
                "auth_state_version": 2,
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        lease = await BrowserSessionLeaseClient(
            "https://control.test", "internal", client=client
        ).redeem(
            project_id=project_id,
            run_id=run_id,
            run_case_id=case_id,
            browser_profile_id=profile_id,
        )

    assert lease.auth_state_version == 2
    assert lease.storage_state["cookies"][0]["value"] == "secret"


@pytest.mark.asyncio
async def test_browser_session_client_errors_never_echo_auth_state() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, json={"detail": "browser auth state unavailable"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(RuntimeError, match="unavailable") as captured:
            await BrowserSessionLeaseClient(
                "https://control.test", "internal", client=client
            ).redeem(
                project_id=str(uuid4()),
                run_id=str(uuid4()),
                run_case_id=str(uuid4()),
                browser_profile_id=str(uuid4()),
            )

    assert "cookie" not in str(captured.value).lower()

