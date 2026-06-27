"""凭证脱敏工具。

识别 config 字典中的敏感字段并替换值为掩码。
"""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

# 敏感字段名模式（不区分大小写匹配）
SENSITIVE_KEY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"passwd", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"api[_-]?key", re.IGNORECASE),
    re.compile(r"access[_-]?key", re.IGNORECASE),
    re.compile(r"private[_-]?key", re.IGNORECASE),
    re.compile(r"credential", re.IGNORECASE),
    re.compile(r"auth", re.IGNORECASE),
]

MASK_VALUE = "••••••••"


def _is_sensitive_key(key: str) -> bool:
    """判断 key 是否为敏感字段名。"""
    return any(pattern.search(key) for pattern in SENSITIVE_KEY_PATTERNS)


def mask_credentials(data: dict[str, Any]) -> dict[str, Any]:
    """对 config 字典中的敏感字段进行脱敏。

    深度遍历嵌套字典，对敏感 key 的字符串值替换为掩码。
    非字符串值（如 dict/list）继续递归。
    """
    result = deepcopy(data)
    _mask_recursive(result)
    return result


def _mask_recursive(data: dict[str, Any]) -> None:
    for key, value in data.items():
        if _is_sensitive_key(key):
            if isinstance(value, str) and not value:
                continue
            data[key] = MASK_VALUE
        elif isinstance(value, dict):
            _mask_recursive(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    _mask_recursive(item)
