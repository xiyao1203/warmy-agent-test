"""Codex Browser 插件数据契约。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CodexBrowserInput:
    """Codex 浏览器探索输入。"""

    test_intent: str
    target_url: str
    headless: bool = True
    timeout_seconds: int = 120
    model: str = "gpt-4o"


@dataclass(frozen=True, slots=True)
class CodexBrowserResult:
    """Codex 浏览器探索结果。"""

    status: str
    screenshots: list[str] = field(default_factory=list)
    execution_log: str = ""
    generated_script: str | None = None
    allure_data: dict[str, object] | None = None
    error_message: str | None = None
