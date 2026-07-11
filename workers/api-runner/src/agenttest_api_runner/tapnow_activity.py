"""Production TapNow browser execution Activity."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import UUID

from agenttest_plugin_canvas.tapnow import TapNowBrowserContract
from temporalio import activity

from .artifact_uploader import ArtifactUploader


@dataclass(frozen=True, slots=True)
class TapNowTaskInput:
    project_id: str
    run_id: str
    run_case_id: str
    agent_id: str
    target_url: str
    intent: str
    binding_ids: list[str] = field(default_factory=list)
    control_api_base_url: str = ""
    internal_token: str = ""
    timeout_ms: int = 120_000


@dataclass(frozen=True, slots=True)
class TapNowResult:
    run_case_id: str
    status: str
    evidence: dict[str, Any]
    error_type: str | None = None
    error_message: str | None = None


async def execute_tapnow_page(
    page, task: TapNowTaskInput, uploader, credentials: dict[str, str]
) -> TapNowResult:
    contract = TapNowBrowserContract(
        run_id=UUID(task.run_id),
        agent_id=UUID(task.agent_id),
        timeout_ms=task.timeout_ms,
    )
    await contract.login(page, credentials)
    await contract.submit(page, task.intent)
    await contract.wait_until_complete(page)
    canvas = await contract.collect(page)
    screenshot = await page.screenshot()
    artifact = await uploader.upload(
        project_id=task.project_id,
        run_id=task.run_id,
        run_case_id=task.run_case_id,
        filename=f"{task.run_case_id}-final.png",
        content_type="image/png",
        content=screenshot,
    )
    evidence: dict[str, object] = {
        "execution_outcome": "success",
        "quality_decision": "review_required",
        "security_decision": "clear",
        "canvas": {
            "nodes": [asdict(node) for node in canvas.nodes],
            "connections": [asdict(item) for item in canvas.connections],
        },
        "artifacts": [artifact, *canvas.artifacts],
        "trace": {"stages": ["authenticating", "executing", "collecting"]},
    }
    return TapNowResult(task.run_case_id, "passed", evidence)


@activity.defn
async def run_tapnow_case(task: TapNowTaskInput) -> TapNowResult:
    try:
        from playwright.async_api import async_playwright

        from .credentials import CredentialLeaseClient
    except ImportError:
        return TapNowResult(
            task.run_case_id,
            "error",
            {"execution_outcome": "error"},
            "EnvironmentError",
            "Playwright runtime is not installed",
        )
    activity.heartbeat({"run_case_id": task.run_case_id, "stage": "preparing"})
    credentials: dict[str, str] = {}
    try:
        credentials = await CredentialLeaseClient(
            task.control_api_base_url, task.internal_token
        ).redeem(
            project_id=task.project_id,
            run_id=task.run_id,
            run_case_id=task.run_case_id,
            binding_ids=task.binding_ids,
        )
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(record_video_dir=".data/videos")
            try:
                page = await context.new_page()
                await page.goto(task.target_url, timeout=task.timeout_ms)
                uploader = ArtifactUploader(task.control_api_base_url, task.internal_token)
                return await execute_tapnow_page(page, task, uploader, credentials)
            finally:
                credentials.clear()
                await context.close()
                await browser.close()
    except Exception as error:
        credentials.clear()
        return TapNowResult(
            task.run_case_id,
            "error",
            {"execution_outcome": "error"},
            type(error).__name__,
            str(error),
        )
