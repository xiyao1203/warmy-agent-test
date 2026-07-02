"""Codex Browser Agent 插件 —— 基于 OpenAI Codex CLI + Playwright MCP。

Codex CLI 内置 Playwright MCP，可直接操控 Google Chrome：
打开页面、点击、填表、截图、断言，无需单独拼接 Playwright。

支持两种浏览器生命周期模式：
- ephemeral：每次新建 Chrome 实例，执行完销毁
- persistent：连接已有 Chrome 实例（CDP），复用进程和登录态
"""

from agenttest_plugin_codex.adapter import CodexBrowserAdapter
from agenttest_plugin_codex.contracts import (
    BrowserMode,
    CodexBrowserInput,
    CodexBrowserResult,
    StorageStateConfig,
)

__all__ = [
    "BrowserMode",
    "CodexBrowserAdapter",
    "CodexBrowserInput",
    "CodexBrowserResult",
    "StorageStateConfig",
]
