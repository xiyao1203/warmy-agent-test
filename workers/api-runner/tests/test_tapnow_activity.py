from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest_api_runner.tapnow_activity import TapNowTaskInput, execute_tapnow_page


class Page:
    async def fill(self, *_args, **_kwargs):
        return None

    async def click(self, *_args, **_kwargs):
        return None

    async def wait_for_selector(self, *_args, **_kwargs):
        return None

    async def evaluate(self, _script):
        return {"nodes": [], "connections": [], "artifacts": []}

    async def screenshot(self):
        return b"png"


class Uploader:
    async def upload(self, **kwargs):
        assert kwargs["content"] == b"png"
        return {"id": "artifact-1", "sha256": "hash", "content_type": "image/png"}


@pytest.mark.asyncio
async def test_execute_page_returns_secret_free_evidence() -> None:
    task = TapNowTaskInput(
        project_id=str(uuid4()),
        run_id=str(uuid4()),
        run_case_id=str(uuid4()),
        agent_id=str(uuid4()),
        target_url="https://tapnow.test/canvas",
        intent="生成商品图",
        credentials={"username": "tester", "password": "secret"},
    )

    result = await execute_tapnow_page(Page(), task, Uploader())

    assert result.status == "passed"
    assert result.evidence["execution_outcome"] == "success"
    assert result.evidence["artifacts"][0]["id"] == "artifact-1"
    assert "secret" not in str(result.evidence)
