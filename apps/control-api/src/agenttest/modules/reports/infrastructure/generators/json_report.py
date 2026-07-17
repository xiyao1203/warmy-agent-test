"""JSON 报告生成器。"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from agenttest.modules.reports.application.contracts import ReportFormat, RunReport


class JsonReportGenerator:
    """生成标准化测试结果 JSON。"""

    format: ReportFormat = "json"
    media_type = "application/json"

    def generate(self, run_data: RunReport) -> str:
        """生成 JSON 报告正文。"""

        report = {
            "format_version": "1.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "run_id": run_data.get("run_id"),
            "plan_id": run_data.get("plan_id"),
            "status": run_data.get("status"),
            "started_at": run_data.get("started_at"),
            "completed_at": run_data.get("completed_at"),
            "total_cases": run_data.get("total_cases"),
            "passed_cases": run_data.get("passed_cases"),
            "failed_cases": run_data.get("failed_cases"),
            "cases": run_data.get("cases", []),
        }
        return json.dumps(report, indent=2, ensure_ascii=False)
