"""安全扫描适配器工厂。"""

from __future__ import annotations

import shutil

from agenttest.modules.security.adapters.mock_scanner import MockScanner
from agenttest.modules.security.adapters.promptfoo_adapter import PromptfooScanner
from agenttest.modules.security.adapters.protocol import SecurityScanner


def create_scanner(promptfoo_bin: str = "promptfoo") -> SecurityScanner:
    """创建安全扫描器实例。

    如果 Promptfoo 可用则使用真实扫描器，否则回退到 Mock。
    """
    if shutil.which(promptfoo_bin):
        return PromptfooScanner(promptfoo_bin)
    return MockScanner()
