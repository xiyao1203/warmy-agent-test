"""安全扫描适配器协议。"""

from __future__ import annotations

from typing import Protocol


class SecurityScanner(Protocol):
    """安全扫描器协议。"""

    async def run_scan(
        self,
        *,
        agent_endpoint: str,
        scan_type: str = "full",
    ) -> list[dict[str, object]]:
        """执行安全扫描，返回 findings 列表。"""
        ...
