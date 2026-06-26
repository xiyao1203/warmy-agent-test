"""Browser Harness 插件 — 基于 browser-use/browser-harness 官方库。

通过 Chrome DevTools Protocol (CDP) 控制真实浏览器，
提供页面截图、DOM 采集和可访问性检查能力。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BrowserPageSnapshot:
    """浏览器页面快照。"""

    url: str
    title: str
    html_preview: str
    text_content: str
    screenshot_base64: str | None = None
    dom_nodes_count: int = 0
    errors: list[str] = field(default_factory=list)


async def capture(url: str) -> BrowserPageSnapshot:
    """打开页面并采集完整快照。

    Args:
        url: 目标页面地址。

    Returns:
        BrowserPageSnapshot 包含完整的页面信息。
    """
    import base64

    from browser_harness.helpers import (  # type: ignore[import-untyped]
        capture_screenshot,
        goto_url,
        js,
        page_info,
    )

    errors: list[str] = []

    await goto_url(url)
    info = page_info()

    html = js("return document.documentElement.outerHTML")
    text = js("return document.body.innerText || ''")
    dom_count = js("return document.querySelectorAll('*').length")

    screenshot_b64 = None
    try:
        raw = capture_screenshot()
        screenshot_b64 = base64.b64encode(raw).decode()
    except Exception:
        pass

    return BrowserPageSnapshot(
        url=info.get("url", url),
        title=info.get("title", ""),
        html_preview=str(html)[:2000],
        text_content=str(text)[:5000],
        screenshot_base64=screenshot_b64,
        dom_nodes_count=int(dom_count) if dom_count else 0,
        errors=errors,
    )


async def check_accessibility(url: str) -> dict[str, object]:
    """执行可访问性检查。

    返回页面中缺失 alt 的图片数、空链接数和
    表单标签缺失情况。
    """
    from browser_harness.helpers import goto_url, js  # type: ignore[import-untyped]

    await goto_url(url)

    missing_alts = js("return document.querySelectorAll('img:not([alt])').length")
    empty_links = js("return document.querySelectorAll('a[href]:empty').length")
    missing_labels = js("""
        const inputs = document.querySelectorAll('input:not([type=hidden])');
        let count = 0;
        inputs.forEach((el) => {
            if (!el.labels || el.labels.length === 0) count++;
        });
        return count;
    """)

    return {
        "missing_alt_images": int(missing_alts) if missing_alts else 0,
        "empty_links": int(empty_links) if empty_links else 0,
        "inputs_without_labels": int(missing_labels) if missing_labels else 0,
    }
