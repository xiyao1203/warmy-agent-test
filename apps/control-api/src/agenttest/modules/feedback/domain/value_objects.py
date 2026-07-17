"""反馈领域值对象。"""

from __future__ import annotations

from enum import StrEnum


class FeedbackType(StrEnum):
    """反馈类型枚举。"""

    BUG = "bug"
    FEATURE = "feature"
    UX = "ux"
    OTHER = "other"
