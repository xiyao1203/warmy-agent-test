"""Browser Harness Temporal Activity。

将 browser-use/browser-harness 的浏览器采集能力封装为
Temporal Activity，供 Worker 在执行测试用例时调用。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from temporalio import activity
from temporalio.exceptions import ApplicationError


@dataclass
class CapturePageInput:
    """页面采集输入。"""

    url: str
    run_case_id: str


@dataclass
class PageSnapshot:
    """页面快照输出。"""

    url: str
    title: str
    dom_nodes: int
    html_preview: str
    errors: list[str] = field(default_factory=list)


@activity.defn
async def capture_page_snapshot(inp: CapturePageInput) -> PageSnapshot:
    """打开 URL 并采集页面快照。

    Temporal Activity，心跳上报进度，超时可重试。
    """
    activity.heartbeat({"url": inp.url, "run_case_id": inp.run_case_id})

    try:
        from browser_harness.helpers import goto_url, js, page_info  # type: ignore[import-untyped]
    except ImportError:
        raise_runtime_unavailable()

    errors: list[str] = []
    try:
        await goto_url(inp.url)
    except Exception as exc:
        errors.append(f"导航失败: {exc}")
        return PageSnapshot(
            url=inp.url,
            title="导航失败",
            dom_nodes=0,
            html_preview="",
            errors=errors,
        )

    info = page_info()
    title = str(info.get("title", ""))
    dom_nodes = int(js("return document.querySelectorAll('*').length") or 0)
    html = str(js("return document.documentElement.outerHTML") or "")[:2000]

    return PageSnapshot(
        url=inp.url,
        title=title,
        dom_nodes=dom_nodes,
        html_preview=html,
        errors=errors,
    )


def raise_runtime_unavailable() -> None:
    """将部署依赖缺失标记为不可重试的执行错误。"""
    raise ApplicationError(
        "Browser Harness runtime is not installed",
        type="DependencyUnavailable",
        non_retryable=True,
    )
