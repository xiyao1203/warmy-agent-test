"""Codex Browser Agent 插件 —— 基于 OpenAI Codex CLI + Playwright MCP。

Codex CLI 内置 Playwright MCP，可直接操控 Google Chrome：
打开页面、点击、填表、截图、断言，无需单独拼接 Playwright。
"""

from agenttest_plugin_codex.adapter import CodexBrowserAdapter
from agenttest_plugin_codex.contracts import CodexBrowserInput, CodexBrowserResult

__all__ = ["CodexBrowserAdapter", "CodexBrowserInput", "CodexBrowserResult"]
