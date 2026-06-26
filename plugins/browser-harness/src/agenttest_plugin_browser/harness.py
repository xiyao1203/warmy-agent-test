"""Browser Harness 浏览器探索插件。

通过 Playwright 内核驱动浏览器，提供页面内容采集、截图、
DOM 结构抓取和可访问性检查能力。
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


@dataclass
class BrowserHarnessConfig:
    """浏览器 Harness 配置。"""

    headless: bool = True
    viewport_width: int = 1280
    viewport_height: int = 720
    timeout_ms: int = 30000
    navigation_timeout_ms: int = 15000


class BrowserHarness:
    """浏览器探索器。

    作为 Playwright 的轻量包装，提供页面快照采集、截图
    和 DOM 检查的统一接口。
    """

    def __init__(self, config: BrowserHarnessConfig | None = None) -> None:
        self._config = config or BrowserHarnessConfig()

    async def capture(self, url: str) -> BrowserPageSnapshot:
        """打开页面并采集完整快照。

        使用 Playwright 异步 API 加载页面，采集标题、文本、
        DOM 数量，并在 headless 模式下生成截图。

        Args:
            url: 目标页面地址。

        Returns:
            BrowserPageSnapshot 包含完整的页面信息。
        """
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self._config.headless)
            page = await browser.new_page(
                viewport={
                    "width": self._config.viewport_width,
                    "height": self._config.viewport_height,
                }
            )
            errors: list[str] = []

            # 监听控制台错误
            page.on("pageerror", lambda err: errors.append(str(err)))

            try:
                await page.goto(
                    url,
                    timeout=self._config.navigation_timeout_ms,
                    wait_until="domcontentloaded",
                )
            except Exception as exc:
                errors.append(f"导航失败: {exc}")

            title = await page.title()
            html = await page.content()
            text = await page.inner_text("body")
            dom_count = await page.evaluate(
                "() => document.querySelectorAll('*').length"
            )

            screenshot = None
            try:
                screenshot_bytes = await page.screenshot(type="png")
                import base64

                screenshot = base64.b64encode(screenshot_bytes).decode()
            except Exception:
                pass

            await browser.close()

            return BrowserPageSnapshot(
                url=url,
                title=title,
                html_preview=html[:2000],
                text_content=text[:5000],
                screenshot_base64=screenshot,
                dom_nodes_count=dom_count,
                errors=errors,
            )

    async def check_accessibility(self, url: str) -> dict[str, object]:
        """执行可访问性检查。

        返回页面中缺失 alt 的图片数、空链接数和
        表单标签缺失情况。

        Args:
            url: 目标页面地址。

        Returns:
            包含可访问性统计的字典。
        """
        from playwright.async_api import async_playwright

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self._config.headless)
            page = await browser.new_page()
            await page.goto(url, timeout=self._config.navigation_timeout_ms)

            missing_alts = await page.evaluate(
                "() => document.querySelectorAll('img:not([alt])').length"
            )
            empty_links = await page.evaluate(
                "() => document.querySelectorAll('a[href]:empty').length"
            )
            missing_labels = await page.evaluate(
                """() => {
                  const inputs = document.querySelectorAll('input:not([type=hidden])');
                  let count = 0;
                  inputs.forEach((el) => {
                    if (!el.labels || el.labels.length === 0) count++;
                  });
                  return count;
                }"""
            )

            await browser.close()
            return {
                "missing_alt_images": missing_alts,
                "empty_links": empty_links,
                "inputs_without_labels": missing_labels,
            }
