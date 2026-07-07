"""Codex Browser Agent 插件 —— 基于 OpenAI Codex CLI + Playwright。

Codex CLI 负责生成结构化浏览器测试计划；插件再用 Playwright
执行真实页面访问、截图和登录态采集，避免 Worker 依赖桌面交互能力。

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
