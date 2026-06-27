"""从失败运行生成测试用例。

扫描指定运行中的失败 RunCase，提取错误信息和输入，
生成对应的测试用例草稿。
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from agenttest.modules.datasets.domain.entities import (
    DatasetVersionId,
    TestCase,
    TestCaseId,
)
from agenttest.modules.datasets.domain.value_objects import (
    ExecutionMode,
    Priority,
    RiskLevel,
)
from agenttest.modules.identity.public import User
from agenttest.modules.projects.public import ProjectId


@dataclass
class GenerateFromRunCommand:
    """从运行生成用例命令。"""

    run_id: UUID
    dataset_version_id: UUID
    priority: Priority | None = Priority.P1
    risk_level: RiskLevel | None = RiskLevel.MEDIUM


@dataclass
class GenerateFromRunResult:
    """生成结果。"""

    generated_cases: list[TestCase]
    total_failed: int
    skipped_existing: int


async def generate_cases_from_failed_run(
    *,
    actor: User,
    project_id: ProjectId,
    command: GenerateFromRunCommand,
) -> GenerateFromRunResult:
    """从失败运行生成测试用例。

    扫描指定运行中的 ERROR/FAILED 状态的 RunCase，
    提取用例名称、输入和错误信息，生成 TestCase 草稿。

    Args:
        actor: 当前操作用户。
        project_id: 所属项目 ID。
        command: 生成命令。

    Returns:
        生成结果，包含生成的用例列表和统计。
    """
    # Note: 实际的数据库查询需要注入仓库，此处为纯领域逻辑演示
    # 在实际使用中，run_repo 和 case_repo 会通过依赖注入传入
    generated: list[TestCase] = []

    # 生成模板用例结构
    for i in range(1):  # placeholder - 实际会遍历失败的 RunCases
        case = TestCase.create(
            case_id=TestCaseId.new(),
            dataset_version_id=DatasetVersionId(command.dataset_version_id),
            name=f"generated-case-{i + 1}",
            input={"generated": True},
            execution_mode=ExecutionMode.API,
            assertions=[],
            scorers=[],
            priority=command.priority,
            risk_level=command.risk_level,
        )
        generated.append(case)

    return GenerateFromRunResult(
        generated_cases=generated,
        total_failed=0,
        skipped_existing=0,
    )
