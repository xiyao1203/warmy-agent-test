"""Codex Browser 插件数据契约。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class BrowserMode(StrEnum):
    """浏览器生命周期模式。"""

    EPHEMERAL = "ephemeral"  # 每次新建 Chrome，执行完销毁（默认）
    PERSISTENT = "persistent"  # 连接已有 Chrome 实例，复用进程


@dataclass(frozen=True, slots=True)
class StorageStateConfig:
    """storageState 登录态复用配置。"""

    enabled: bool = True
    storage_dir: str = "/data/storage-states"
    ttl_hours: int = 24
    auto_refresh: bool = True


@dataclass(frozen=True, slots=True)
class CodexBrowserInput:
    """Codex 浏览器探索输入。"""

    test_intent: str
    target_url: str
    headless: bool = True
    timeout_seconds: int = 120
    model: str = ""  # 空表示使用 Codex CLI 当前配置的默认模型
    model_provider: str = ""  # Codex provider ID，空表示默认 OpenAI
    browser_profile_id: str = ""  # 浏览器实例 ID（从 registry 中选择）
    browser_mode: BrowserMode = BrowserMode.EPHEMERAL
    cdp_endpoint: str = ""
    storage_state: StorageStateConfig = field(default_factory=StorageStateConfig)
    storage_state_key: str = ""
    credentials: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CodexBrowserResult:
    """Codex 浏览器探索结果。"""

    status: str
    screenshots: list[str] = field(default_factory=list)
    execution_log: str = ""
    generated_script: str | None = None
    allure_data: dict[str, object] | None = None
    error_message: str | None = None
    storage_state_updated: bool = False
    storage_state_path: str = ""
