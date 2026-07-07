"""Dataset 领域值对象和枚举。

定义版本状态、执行模式、优先级、风险等级和数据集分组等枚举。
"""

from __future__ import annotations

from enum import StrEnum


class VersionStatus(StrEnum):
    """版本状态：DRAFT（可编辑）→ PUBLISHED（不可修改）。"""

    DRAFT = "draft"
    PUBLISHED = "published"


class ExecutionMode(StrEnum):
    """测试用例执行模式：API 调用、浏览器操作或 Codex 浏览器探索。"""

    API = "api"
    BROWSER = "browser"
    CODEX_EXPLORE = "codex_explore"


class Priority(StrEnum):
    """用例优先级：P0（最高）→ P3（最低）。"""

    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class RiskLevel(StrEnum):
    """风险评估等级。"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestGroup(StrEnum):
    """数据集分组：训练集 / 验证集 / 测试集。"""

    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"
