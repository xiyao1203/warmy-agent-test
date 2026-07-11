from __future__ import annotations

from uuid import uuid4

from agenttest.modules.environments.api.lease_router import create_credential_lease_router
from fastapi import FastAPI
from fastapi.testclient import TestClient


class Service:
    async def redeem(self, project_id, credential_ids):
        assert credential_ids
        return {"username": "tester", "password": "secret"}


def test_internal_credential_lease_requires_token_and_run_scope() -> None:
    project_id, run_id, case_id, binding_id = (uuid4() for _ in range(4))

    async def scope_check(project, run, case):
        return (project, run, case) == (project_id, run_id, case_id)

    app = FastAPI()
    app.include_router(
        create_credential_lease_router(
            internal_token="internal",
            service=Service(),
            scope_check=scope_check,
        ),
        prefix="/api/v1",
    )
    client = TestClient(app)
    url = f"/api/v1/internal/projects/{project_id}/credential-leases:redeem"
    body = {
        "run_id": str(run_id),
        "run_case_id": str(case_id),
        "binding_ids": [str(binding_id)],
    }

    assert client.post(url, json=body).status_code == 403
    response = client.post(url, headers={"X-Internal-Token": "internal"}, json=body)

    assert response.status_code == 200
    assert response.json() == {"values": {"username": "tester", "password": "secret"}}
