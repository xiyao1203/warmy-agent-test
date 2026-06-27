"""网络 Mock 与异常注入工具。

为浏览器测试提供网络层 Mock 和异常模拟能力。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class NetworkMockRule:
    """单条网络 Mock 规则。"""
    url_pattern: str
    status: int = 200
    body: Any = None
    headers: dict[str, str] = field(default_factory=dict)
    delay_ms: int = 0


@dataclass(slots=True)
class NetworkFaultRule:
    """单条网络异常注入规则。"""
    url_pattern: str
    fault_type: str = "abort"  # abort | timeout | slow | error
    delay_ms: int = 0
    error_code: int | None = None


class NetworkMockManager:
    """网络 Mock 管理器。"""

    def __init__(self) -> None:
        self._mock_rules: list[NetworkMockRule] = []
        self._fault_rules: list[NetworkFaultRule] = []

    def add_mock(self, url_pattern: str, *, status: int = 200, body: Any = None) -> NetworkMockRule:
        rule = NetworkMockRule(url_pattern=url_pattern, status=status, body=body)
        self._mock_rules.append(rule)
        return rule

    def add_fault(
        self,
        url_pattern: str,
        fault_type: str = "abort",
        *,
        delay_ms: int = 0,
        error_code: int | None = None,
    ) -> NetworkFaultRule:
        rule = NetworkFaultRule(
            url_pattern=url_pattern,
            fault_type=fault_type,
            delay_ms=delay_ms,
            error_code=error_code,
        )
        self._fault_rules.append(rule)
        return rule

    def get_mock_rules(self) -> list[NetworkMockRule]:
        return list(self._mock_rules)

    def get_fault_rules(self) -> list[NetworkFaultRule]:
        return list(self._fault_rules)

    def clear(self) -> None:
        self._mock_rules.clear()
        self._fault_rules.clear()
