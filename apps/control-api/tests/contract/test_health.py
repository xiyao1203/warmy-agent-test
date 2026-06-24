from agenttest.bootstrap.app import create_app
from fastapi.testclient import TestClient


def test_health_returns_service_status() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "control-api",
        "status": "ok",
        "version": "0.1.0",
    }
