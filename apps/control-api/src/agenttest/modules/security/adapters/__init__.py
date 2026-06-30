"""安全扫描适配器工厂。"""

from __future__ import annotations

import shutil

from agenttest.modules.security.adapters.promptfoo_adapter import PromptfooScanner
from agenttest.modules.security.adapters.protocol import SecurityScanner


class ScannerUnavailableError(RuntimeError):
    """部署未提供真实安全扫描运行时。"""


def create_scanner(promptfoo_bin: str = "promptfoo") -> SecurityScanner:
    """解析并创建真实 Promptfoo 扫描器。"""
    resolved = shutil.which(promptfoo_bin)
    if resolved is None:
        raise ScannerUnavailableError("Promptfoo runtime is not installed")
    return PromptfooScanner(resolved)


__all__ = ["ScannerUnavailableError", "create_scanner"]
