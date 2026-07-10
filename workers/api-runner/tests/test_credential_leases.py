from __future__ import annotations

import httpx
import pytest
from agenttest_api_runner.credentials import CredentialLeaseClient


@pytest.mark.asyncio
async def test_worker_redeems_scoped_credentials_without_returning_metadata() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Internal-Token"] == "internal"
        assert request.url.path.endswith("/credential-leases:redeem")
        return httpx.Response(200, json={"values": {"username": "tester", "password": "secret"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        client = CredentialLeaseClient("https://control.test", "internal", http)
        values = await client.redeem(
            project_id="project-1",
            run_id="run-1",
            run_case_id="case-1",
            binding_ids=["credential-1"],
        )

    assert values == {"username": "tester", "password": "secret"}
