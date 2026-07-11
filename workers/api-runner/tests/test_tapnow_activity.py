from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest_api_runner.browser_sessions import BrowserSessionLease
from agenttest_api_runner.tapnow_activity import (
    TapNowTaskInput,
    execute_tapnow_browser,
    execute_tapnow_page,
    redact_network_url,
    tapnow_error_result,
)
from agenttest_plugin_canvas.tapnow import AwaitingConfirmationError, TargetProductError


class Page:
    url = "https://tapnow.test/canvas"

    def on(self, *_args, **_kwargs):
        return None

    async def goto(self, *_args, **_kwargs):
        return None

    async def fill(self, *_args, **_kwargs):
        return None

    async def click(self, *_args, **_kwargs):
        return None

    async def wait_for_selector(self, *_args, **_kwargs):
        return None

    async def evaluate(self, script):
        if "__agenttestTapNowState" in script:
            return "completed"
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
    )

    result = await execute_tapnow_page(
        Page(), task, Uploader(), {"username": "tester", "password": "secret"}
    )

    assert result.status == "passed"
    assert result.evidence["execution_outcome"] == "success"
    assert result.evidence["artifacts"][0]["id"] == "artifact-1"
    assert "secret" not in str(result.evidence)


@pytest.mark.asyncio
async def test_browser_profile_execution_injects_state_skips_form_login_and_uploads_evidence(
    tmp_path,
) -> None:
    uploaded: list[str] = []

    class LeaseClient:
        async def redeem(self, **_kwargs):
            return BrowserSessionLease(
                {
                    "cookies": [{"name": "session", "value": "browser-secret", "domain": ".test"}],
                    "origins": [],
                },
                1,
            )

    class CredentialClient:
        async def redeem(self, **_kwargs):
            raise AssertionError("credential login must not run for browser profile strategy")

    class ArtifactUploader:
        async def upload(self, **kwargs):
            uploaded.append(kwargs["filename"])
            return {"id": kwargs["filename"], "content_type": kwargs["content_type"]}

    class Tracing:
        async def start(self, **kwargs):
            assert kwargs == {"screenshots": True, "snapshots": True, "sources": False}

        async def stop(self, path):
            path.write_bytes(b"trace")

    class Context:
        tracing = Tracing()

        async def new_page(self):
            return Page()

        async def close(self):
            return None

    class Browser:
        async def new_context(self, **kwargs):
            assert kwargs["storage_state"]["cookies"][0]["value"] == "browser-secret"
            assert kwargs["record_video_dir"]
            return Context()

        async def close(self):
            return None

    class Chromium:
        async def launch(self, **kwargs):
            assert kwargs == {"headless": True}
            return Browser()

    class Playwright:
        chromium = Chromium()

    task = TapNowTaskInput(
        project_id=str(uuid4()),
        run_id=str(uuid4()),
        run_case_id=str(uuid4()),
        agent_id=str(uuid4()),
        target_url="https://tapnow.test/canvas",
        intent="只读检查",
        login_strategy="browser_profile",
        browser_profile_id=str(uuid4()),
    )

    result = await execute_tapnow_browser(
        task,
        Playwright(),
        ArtifactUploader(),
        credential_client=CredentialClient(),
        browser_session_client=LeaseClient(),
        artifact_root=tmp_path,
    )

    assert result.status == "passed"
    assert {
        f"{task.run_case_id}-final.png",
        "playwright-trace.zip",
        "network-summary.json",
        "console-errors.json",
        "canvas.json",
    }.issubset(set(uploaded))
    assert "browser-secret" not in repr(result.evidence)


def test_network_url_redaction_keeps_safe_shape_only() -> None:
    assert (
        redact_network_url(
            "https://app.tapnow.ai/api/task?id=42&token=secret&email=user@example.com"
        )
        == "https://app.tapnow.ai/api/task?id=42&token=%5BREDACTED%5D&email=%5BREDACTED%5D"
    )


def test_confirmation_and_target_errors_have_distinct_non_success_evidence() -> None:
    task = TapNowTaskInput(
        project_id=str(uuid4()),
        run_id=str(uuid4()),
        run_case_id=str(uuid4()),
        agent_id=str(uuid4()),
        target_url="https://tapnow.test/canvas",
        intent="inspect",
    )

    confirmation = tapnow_error_result(task, AwaitingConfirmationError("Ask before acting"))
    target = tapnow_error_result(task, TargetProductError("quota exhausted"))

    assert confirmation.status == "failed"
    assert confirmation.evidence["execution_outcome"] == "awaiting_confirmation"
    assert confirmation.evidence["quality_decision"] == "review_required"
    assert target.status == "failed"
    assert target.evidence["execution_outcome"] == "target_product_error"
