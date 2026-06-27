"""安全框架适配器预留。

预留 Garak / PyRIT / AgentDojo 适配器接口。
当前返回空结果，等待各框架集成后填充实现。
"""

from __future__ import annotations


class GarakScanner:
    """NVIDIA Garak 安全扫描器（预留）。"""

    async def run_scan(
        self,
        *,
        agent_endpoint: str | None = None,
        scan_type: str = "full",
    ) -> list[dict]:
        return []


class PyRITScanner:
    """Microsoft PyRIT 安全扫描器（预留）。"""

    async def run_scan(
        self,
        *,
        agent_endpoint: str | None = None,
        scan_type: str = "full",
    ) -> list[dict]:
        return []


class AgentDojoScanner:
    """AgentDojo 安全扫描器（预留）。"""

    async def run_scan(
        self,
        *,
        agent_endpoint: str | None = None,
        scan_type: str = "full",
    ) -> list[dict]:
        return []
