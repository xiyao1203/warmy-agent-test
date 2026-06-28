"""报告生成器。

支持 JSON、JUnit XML 和 HTML 格式的测试报告生成。
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class RunReport:
    """运行报告数据结构。"""
    run_id: str
    project_id: str
    test_plan_name: str
    status: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    error_cases: int
    duration_ms: int | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cases: list[dict[str, Any]] | None = None


class ReportGenerator:
    """报告生成器。"""

    def generate_json(self, report: RunReport) -> str:
        """生成 JSON 格式报告。"""
        data = {
            "run_id": report.run_id,
            "project_id": report.project_id,
            "test_plan_name": report.test_plan_name,
            "status": report.status,
            "summary": {
                "total": report.total_cases,
                "passed": report.passed_cases,
                "failed": report.failed_cases,
                "error": report.error_cases,
                "pass_rate": round(report.passed_cases / max(report.total_cases, 1) * 100, 2),
            },
            "duration_ms": report.duration_ms,
            "started_at": report.started_at.isoformat() if report.started_at else None,
            "completed_at": report.completed_at.isoformat() if report.completed_at else None,
            "generated_at": datetime.now().isoformat(),
        }
        if report.cases:
            data["cases"] = report.cases
        return json.dumps(data, indent=2, ensure_ascii=False)

    def generate_junit_xml(self, report: RunReport) -> str:
        """生成 JUnit XML 格式报告。"""
        testsuites = ET.Element("testsuites")
        testsuite = ET.SubElement(testsuites, "testsuite")
        testsuite.set("name", report.test_plan_name)
        testsuite.set("tests", str(report.total_cases))
        testsuite.set("failures", str(report.failed_cases))
        testsuite.set("errors", str(report.error_cases))
        testsuite.set("timestamp", (report.started_at or datetime.now()).isoformat())

        if report.duration_ms:
            testsuite.set("time", str(report.duration_ms / 1000))

        if report.cases:
            for case in report.cases:
                testcase = ET.SubElement(testsuite, "testcase")
                testcase.set("name", case.get("name", "unknown"))
                testcase.set("classname", case.get("test_plan_name", report.test_plan_name))

                if case.get("duration_ms"):
                    testcase.set("time", str(case["duration_ms"] / 1000))

                status = case.get("status", "")
                if status == "failed":
                    failure = ET.SubElement(testcase, "failure")
                    failure.set("message", case.get("error_message", "Test failed"))
                    failure.text = case.get("error_details", "")
                elif status == "error":
                    error = ET.SubElement(testcase, "error")
                    error.set("message", case.get("error_message", "Test error"))
                    error.text = case.get("error_details", "")

        return ET.tostring(testsuites, encoding="unicode", xml_declaration=True)

    def generate_html(self, report: RunReport) -> str:
        """生成 HTML 格式报告。"""
        pass_rate = round(report.passed_cases / max(report.total_cases, 1) * 100, 2)
        status_color = "#10b981" if report.status == "passed" else "#ef4444"

        cases_html = ""
        if report.cases:
            for case in report.cases:
                case_status = case.get("status", "unknown")
                case_color = "#10b981" if case_status == "passed" else "#ef4444"
                cases_html += f"""
                <tr>
                    <td>{case.get('name', 'N/A')}</td>
                    <td style="color: {case_color}; font-weight: bold;">{case_status}</td>
                    <td>{case.get('duration_ms', 'N/A')}ms</td>
                    <td>{case.get('error_message', '-')}</td>
                </tr>"""

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>测试报告 - {report.test_plan_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #e5e5e5; padding-bottom: 10px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ padding: 15px; background: #f9f9f9; border-radius: 6px; flex: 1; text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; }}
        .stat-label {{ color: #666; font-size: 14px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #e5e5e5; }}
        th {{ background: #f5f5f5; font-weight: 600; }}
        .status {{ color: {status_color}; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>测试报告：{report.test_plan_name}</h1>
        <p>运行 ID: {report.run_id}</p>
        <p>状态: <span class="status">{report.status}</span></p>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary">
            <div class="stat">
                <div class="stat-value">{report.total_cases}</div>
                <div class="stat-label">总用例</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: #10b981;">{report.passed_cases}</div>
                <div class="stat-label">通过</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: #ef4444;">{report.failed_cases}</div>
                <div class="stat-label">失败</div>
            </div>
            <div class="stat">
                <div class="stat-value">{pass_rate}%</div>
                <div class="stat-label">通过率</div>
            </div>
        </div>

        <h2>用例详情</h2>
        <table>
            <thead>
                <tr>
                    <th>名称</th>
                    <th>状态</th>
                    <th>耗时</th>
                    <th>错误信息</th>
                </tr>
            </thead>
            <tbody>
                {cases_html if cases_html else '<tr><td colspan="4">暂无用例数据</td></tr>'}
            </tbody>
        </table>
    </div>
</body>
</html>"""
