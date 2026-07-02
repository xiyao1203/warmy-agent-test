from __future__ import annotations

import html
import json
import subprocess
import tempfile
from dataclasses import asdict
from pathlib import Path
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
        ReportArtifact(
            name="allure-results.json",
            content_type="application/json",
            content=_allure_results_json(result),
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


def _allure_results_json(result: RunResult) -> str:
    """生成 Allure 兼容的 results.json。"""
    results = []
    for case in result.cases:
        test_case = {
            "name": case.run_case_id,
            "status": _allure_status(case.status),
            "statusDetails": {
                "message": case.error_message or "",
            },
            "stage": "finished",
            "start": 0,
            "stop": case.duration_ms or 0,
            "attachments": [],
        }
        # Attach trace as text attachment
        if case.trace:
            trace_text = json.dumps(case.trace, ensure_ascii=False)
            if len(trace_text) > 200000:
                trace_text = trace_text[:200000]
            test_case["attachments"].append({
                "name": "trace.json",
                "type": "application/json",
                "source": trace_text,
            })
        results.append(test_case)
    return json.dumps(
        {"name": result.run_id, "children": results, "status": _allure_status(result.status)},
        ensure_ascii=False,
    )


def _allure_status(status: str) -> str:
    return {
        "passed": "passed",
        "failed": "failed",
        "error": "broken",
        "cancelled": "skipped",
    }.get(status, "broken")


def build_allure_html_report(results_dir: str | Path) -> bytes | None:
    """调用 allure CLI 生成 HTML 报告。

    Args:
        results_dir: Allure results 目录（包含 allure-results.json）。

    Returns:
        生成的 HTML 目录的 tar.gz 字节，或 None（allure 不可用时）。
    """
    import io
    import shutil
    import tarfile

    allure_path = shutil.which("allure")
    if allure_path is None:
        return None
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(
            [allure_path, "generate", str(results_dir), "-o", tmpdir, "--clean"],
            capture_output=True,
            timeout=60,
        )
        report_dir = Path(tmpdir)
        if not report_dir.joinpath("index.html").exists():
            return None
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            tar.add(tmpdir, arcname="allure-report")
        return buf.getvalue()
