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


class TestCaseStatus(StrEnum):
    """用例评审状态；与数据集版本的发布状态相互独立。"""

    DRAFT = "draft"
    READY = "ready"
    DEPRECATED = "deprecated"


class TestCaseTemplate(StrEnum):
    """专业测试用例模板。"""

    STEP_BY_STEP = "step_by_step"
    TEXT = "text"
    BDD = "bdd"
    AI_EVAL = "ai_eval"


class TestCaseType(StrEnum):
    """测试用例覆盖的质量类型。"""

    FUNCTIONAL = "functional"
    REGRESSION = "regression"
    SMOKE = "smoke"
    INTEGRATION = "integration"
    E2E = "e2e"
    SECURITY = "security"
    PERFORMANCE = "performance"
    USABILITY = "usability"
    EXPLORATORY = "exploratory"


class AutomationStatus(StrEnum):
    """用例自动化成熟度。"""

    MANUAL = "manual"
    CANDIDATE = "candidate"
    AUTOMATED = "automated"


class TestCaseSource(StrEnum):
    """用例来源，用于审计和列表筛选。"""

    MANUAL = "manual"
    AGENT_GENERATED = "agent_generated"
    IMPORTED = "imported"
    RUN_REGRESSION = "run_regression"


class DataBindingSource(StrEnum):
    """测试数据的受控来源。"""

    LITERAL = "literal"
    ENVIRONMENT = "environment"
    CREDENTIAL = "credential"
    FIXTURE = "fixture"
    GENERATED = "generated"


class DataValueType(StrEnum):
    """表单和执行器共同使用的数据值类型。"""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    JSON = "json"


class ArtifactKind(StrEnum):
    """专业用例可以要求采集的标准证据类型。"""

    RESPONSE = "response"
    SCREENSHOT = "screenshot"
    TRACE = "trace"
    CANVAS_SNAPSHOT = "canvas_snapshot"
    FILE = "file"
