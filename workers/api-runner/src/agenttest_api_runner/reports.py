from __future__ import annotations

import html
import json
from dataclasses import asdict
from xml.etree.ElementTree import Element, SubElement, tostring

from agenttest_api_runner.contracts import ReportArtifact, RunResult


def build_reports(result: RunResult) -> list[ReportArtifact]:
    summary = _summary(result)
    return [
        ReportArtifact(
            name="run-result.json",
            content_type="application/json",
            content=json.dumps(
                {
                    "run_id": result.run_id,
                    "status": result.status,
                    "summary": summary,
                    "cases": [asdict(case) for case in result.cases],
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        ),
        ReportArtifact(
            name="junit.xml",
            content_type="application/xml",
            content=_junit_xml(result, summary),
        ),
        ReportArtifact(
            name="report.html",
            content_type="text/html; charset=utf-8",
            content=_html_report(result, summary),
        ),
    ]


def _summary(result: RunResult) -> dict[str, int]:
    return {
        "passed": _count(result, "passed"),
        "failed": _count(result, "failed"),
        "error": _count(result, "error"),
        "cancelled": _count(result, "cancelled"),
        "total": len(result.cases),
    }


def _count(result: RunResult, status: str) -> int:
    return sum(1 for case in result.cases if case.status == status)


def _junit_xml(result: RunResult, summary: dict[str, int]) -> str:
    suite = Element(
        "testsuite",
        {
            "name": result.run_id,
            "tests": str(summary["total"]),
            "failures": str(summary["failed"]),
            "errors": str(summary["error"]),
            "skipped": str(summary["cancelled"]),
        },
    )
    for case in result.cases:
        test_case = SubElement(
            suite,
            "testcase",
            {
                "classname": "agenttest.api_runner",
                "name": case.run_case_id,
                "time": f"{(case.duration_ms or 0) / 1000:.3f}",
            },
        )
        if case.status == "failed":
            failure = SubElement(
                test_case,
                "failure",
                {"type": case.error_type or "AssertionError"},
            )
            failure.text = case.error_message or "Assertion failed"
        elif case.status == "error":
            error = SubElement(
                test_case,
                "error",
                {"type": case.error_type or "PlatformError"},
            )
            error.text = case.error_message or "Execution error"
        elif case.status == "cancelled":
            skipped = SubElement(test_case, "skipped")
            skipped.text = case.error_message or "Cancelled"
    return tostring(suite, encoding="unicode", short_empty_elements=True)


def _html_report(result: RunResult, summary: dict[str, int]) -> str:
    rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(case.run_case_id)}</td>"
        f"<td>{html.escape(case.status)}</td>"
        f"<td>{case.duration_ms or 0}</td>"
        f"<td>{html.escape(case.error_message or '')}</td>"
        "</tr>"
        for case in result.cases
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>AgentTest Run {html.escape(result.run_id)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 24px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d9dee8; padding: 8px; text-align: left; }}
    th {{ background: #f6f8fb; }}
  </style>
</head>
<body>
  <h1>Run {html.escape(result.run_id)}</h1>
  <p>状态：{html.escape(result.status)}</p>
  <p>总数：{summary["total"]}；通过：{summary["passed"]}；失败：{summary["failed"]}；错误：{summary["error"]}；取消：{summary["cancelled"]}</p>
  <table>
    <thead><tr><th>RunCase</th><th>状态</th><th>耗时(ms)</th><th>错误</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>"""
