"""Production TapNow browser execution Activity."""

from __future__ import annotations

import asyncio
import json
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import UUID

from agenttest_plugin_canvas.tapnow import (
    AwaitingConfirmationError,
    TapNowAuthExpiredError,
    TapNowBrowserContract,
    TargetProductError,
)
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
    login_strategy: str = "none"
    browser_profile_id: str = ""
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
    page,
    task: TapNowTaskInput,
    uploader,
    credentials: dict[str, str],
    *,
    authenticated: bool = False,
) -> TapNowResult:
    contract = TapNowBrowserContract(
        run_id=UUID(task.run_id),
        agent_id=UUID(task.agent_id),
        timeout_ms=task.timeout_ms,
    )
    if not authenticated:
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


class AuthExpiredError(RuntimeError):
    pass


def tapnow_error_result(task: TapNowTaskInput, error: Exception) -> TapNowResult:
    evidence: dict[str, Any] = {
        "execution_outcome": "error",
        "quality_decision": "review_required",
        "security_decision": "clear",
    }
    status = "error"
    if isinstance(error, AwaitingConfirmationError):
        status = "failed"
        evidence["execution_outcome"] = "awaiting_confirmation"
    elif isinstance(error, TargetProductError):
        status = "failed"
        evidence["execution_outcome"] = "target_product_error"
    elif isinstance(error, (AuthExpiredError, TapNowAuthExpiredError)):
        evidence["execution_outcome"] = "auth_expired"
    return TapNowResult(
        task.run_case_id,
        status,
        evidence,
        type(error).__name__,
        str(error),
    )


def redact_network_url(value: str) -> str:
    parts = urlsplit(value)
    safe_keys = {"id", "task_id", "run_id"}
    query = [
        (key, item if key.lower() in safe_keys else "[REDACTED]")
        for key, item in parse_qsl(parts.query, keep_blank_values=True)
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def _looks_like_login(url: str) -> bool:
    normalized = url.lower()
    return any(marker in normalized for marker in ("/login", "/signin", "/sign-in"))


async def _upload_json_artifact(uploader, task: TapNowTaskInput, filename: str, value) -> dict:
    return await uploader.upload(
        project_id=task.project_id,
        run_id=task.run_id,
        run_case_id=task.run_case_id,
        filename=filename,
        content_type="application/json",
        content=json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8"),
    )


async def execute_tapnow_browser(
    task: TapNowTaskInput,
    playwright,
    uploader,
    *,
    credential_client,
    browser_session_client,
    artifact_root: Path | None = None,
) -> TapNowResult:
    credentials: dict[str, str] = {}
    storage_state: dict | None = None
    if task.login_strategy == "browser_profile":
        if not task.browser_profile_id:
            raise ValueError("browser profile strategy requires a profile id")
        lease = await browser_session_client.redeem(
            project_id=task.project_id,
            run_id=task.run_id,
            run_case_id=task.run_case_id,
            browser_profile_id=task.browser_profile_id,
        )
        storage_state = lease.storage_state
    elif task.binding_ids:
        credentials = await credential_client.redeem(
            project_id=task.project_id,
            run_id=task.run_id,
            run_case_id=task.run_case_id,
            binding_ids=task.binding_ids,
        )

    temporary = tempfile.TemporaryDirectory(prefix=f"tapnow-{task.run_case_id}-")
    root = artifact_root or Path(temporary.name)
    video_dir = root / "video"
    await asyncio.to_thread(video_dir.mkdir, parents=True, exist_ok=True)
    trace_path = root / "playwright-trace.zip"
    console_errors: list[dict[str, str]] = []
    network_summary: list[dict[str, object]] = []
    browser = await playwright.chromium.launch(headless=True)
    context_kwargs: dict[str, object] = {"record_video_dir": str(video_dir)}
    if storage_state is not None:
        context_kwargs["storage_state"] = storage_state
    context = await browser.new_context(**context_kwargs)
    result: TapNowResult | None = None
    trace_started = False
    try:
        await context.tracing.start(screenshots=True, snapshots=True, sources=False)
        trace_started = True
        page = await context.new_page()

        def on_console(message) -> None:
            message_type = str(getattr(message, "type", ""))
            if message_type in {"error", "warning"}:
                console_errors.append(
                    {"type": message_type, "text": str(getattr(message, "text", ""))[:1000]}
                )

        def on_response(response) -> None:
            request = getattr(response, "request", None)
            network_summary.append(
                {
                    "method": str(getattr(request, "method", "GET")),
                    "url": redact_network_url(str(getattr(response, "url", ""))),
                    "status": int(getattr(response, "status", 0) or 0),
                    "resource_type": str(getattr(request, "resource_type", "")),
                }
            )

        if hasattr(page, "on"):
            page.on("console", on_console)
            page.on("response", on_response)
        await page.goto(task.target_url, timeout=task.timeout_ms, wait_until="domcontentloaded")
        if task.login_strategy == "browser_profile" and _looks_like_login(str(page.url)):
            raise AuthExpiredError("saved browser login state has expired")
        result = await execute_tapnow_page(
            page,
            task,
            uploader,
            credentials,
            authenticated=task.login_strategy == "browser_profile",
        )
    finally:
        credentials.clear()
        if trace_started:
            await context.tracing.stop(path=trace_path)
        await context.close()
        await browser.close()

    if result is None:
        raise RuntimeError("TapNow execution did not produce a result")
    artifacts = list(result.evidence.get("artifacts", []))
    artifacts.append(
        await _upload_json_artifact(uploader, task, "network-summary.json", network_summary)
    )
    artifacts.append(
        await _upload_json_artifact(uploader, task, "console-errors.json", console_errors)
    )
    artifacts.append(
        await _upload_json_artifact(
            uploader,
            task,
            "canvas.json",
            result.evidence.get("canvas", {}),
        )
    )
    trace_content = await asyncio.to_thread(trace_path.read_bytes)
    artifacts.append(
        await uploader.upload(
            project_id=task.project_id,
            run_id=task.run_id,
            run_case_id=task.run_case_id,
            filename="playwright-trace.zip",
            content_type="application/zip",
            content=trace_content,
        )
    )
    video_paths = await asyncio.to_thread(lambda: list(video_dir.glob("*.webm")))
    for index, video_path in enumerate(video_paths, start=1):
        artifacts.append(
            await uploader.upload(
                project_id=task.project_id,
                run_id=task.run_id,
                run_case_id=task.run_case_id,
                filename=f"video-{index}.webm",
                content_type="video/webm",
                content=await asyncio.to_thread(video_path.read_bytes),
            )
        )
    result.evidence["artifacts"] = artifacts
    result.evidence["trace"] = {
        "stages": [
            "preparing",
            "credential_lease" if task.binding_ids else "browser_session_lease",
            "authenticating",
            "executing",
            "waiting",
            "collecting",
            "cleanup",
        ]
    }
    temporary.cleanup()
    return result


@activity.defn
async def run_tapnow_case(task: TapNowTaskInput) -> TapNowResult:
    try:
        from playwright.async_api import async_playwright

        from .browser_sessions import BrowserSessionLeaseClient
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
    try:
        async with async_playwright() as playwright:
            return await execute_tapnow_browser(
                task,
                playwright,
                ArtifactUploader(task.control_api_base_url, task.internal_token),
                credential_client=CredentialLeaseClient(
                    task.control_api_base_url, task.internal_token
                ),
                browser_session_client=BrowserSessionLeaseClient(
                    task.control_api_base_url, task.internal_token
                ),
            )
    except Exception as error:
        return tapnow_error_result(task, error)
