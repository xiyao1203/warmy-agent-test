"""Browser Harness 插件 — 基于 browser-use/browser-harness。"""

from agenttest_plugin_browser.harness import (
    BrowserPageSnapshot,
    capture,
    check_accessibility,
)

__all__ = ["BrowserPageSnapshot", "capture", "check_accessibility"]
