"""报告 Application 的结构化数据与渲染端口。"""

from __future__ import annotations

from typing import Literal, Protocol, TypedDict


class RunCaseReport(TypedDict):
    """单条运行用例的报告投影。"""

    case_id: str
    name: str
    status: str
    duration_ms: int | None
    error_type: str | None
    error: str | None


class RunReport(TypedDict):
    """运行报告的稳定 Application 投影。"""

    run_id: str
    project_id: str
    plan_id: str | None
    status: str
    started_at: str | None
    completed_at: str | None
    duration_ms: int | None
    total_cases: int
    passed_cases: int
    failed_cases: int
    error_cases: int
    cancelled_cases: int
    cases: list[RunCaseReport]


ReportFormat = Literal["json", "junit", "html"]


class ReportRenderer(Protocol):
    """将结构化报告渲染为外部格式的技术端口。"""

    format: ReportFormat
    media_type: str

    def generate(self, run_data: RunReport) -> str:
        """生成指定格式的报告正文。"""
        ...
