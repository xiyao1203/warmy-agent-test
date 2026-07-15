from uuid import uuid4

from agenttest.bootstrap.settings import Settings
from agenttest.modules.runs.api.trace_diff import (
    TraceDiffApiDependencies,
    create_trace_diff_router,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


async def actor_for(_request):
    return object()


class FailingComparison:
    async def compare(self, *args, **kwargs):
        raise RuntimeError("project database unavailable")


def test_trace_diff_does_not_hide_project_infrastructure_failure_as_404() -> None:
    app = FastAPI()
    app.include_router(
        create_trace_diff_router(
            TraceDiffApiDependencies(
                compare=FailingComparison(),  # type: ignore[arg-type]
                actor_for=actor_for,  # type: ignore[arg-type]
                settings=Settings(),
            )
        ),
        prefix="/api/v1",
    )
    client = TestClient(app, raise_server_exceptions=False)
    client.cookies.set("agenttest_session", "session")

    response = client.get(f"/api/v1/projects/{uuid4()}/runs/{uuid4()}/diff/{uuid4()}")

    assert response.status_code == 500
