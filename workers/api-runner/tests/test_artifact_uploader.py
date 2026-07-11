from __future__ import annotations

import httpx
import pytest
from agenttest_api_runner.artifact_uploader import ArtifactUploader


@pytest.mark.asyncio
async def test_uploader_returns_descriptor_with_hash_and_no_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Internal-Token"] == "internal"
        return httpx.Response(
            201,
            json={
                "id": "artifact-1",
                "filename": "step.png",
                "content_type": "image/png",
                "size_bytes": 3,
                "storage_path": "aa/bb/step.png",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        descriptor = await ArtifactUploader("https://control.test", "internal", http).upload(
            project_id="project-1",
            run_id="run-1",
            run_case_id="case-1",
            filename="step.png",
            content_type="image/png",
            content=b"png",
        )

    assert descriptor["id"] == "artifact-1"
    assert descriptor["sha256"]
    assert "content" not in descriptor
