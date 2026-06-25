"""Environment 领域值对象。

定义模板类型枚举：BLANK（空）和 PRESET（预设）。
"""

from __future__ import annotations

from enum import StrEnum


class TemplateType(StrEnum):
    """环境模板类型：blank 为空环境，preset 为预设环境。"""
    BLANK = "blank"
    PRESET = "preset"
