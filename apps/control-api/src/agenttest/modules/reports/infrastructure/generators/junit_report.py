"""JUnit XML 报告生成器。"""

from __future__ import annotations

from typing import cast
from xml.dom.minidom import parseString
from xml.etree.ElementTree import Element, SubElement, tostring

from agenttest.modules.reports.application.contracts import ReportFormat, RunReport


class JunitReportGenerator:
    """生成 CI/CD 使用的 JUnit XML 报告。"""

    format: ReportFormat = "junit"
    media_type = "application/xml"

    def generate(self, run_data: RunReport) -> str:
        """生成 JUnit XML 报告正文。"""

        total = int(run_data.get("total_cases", 0))
        failed = int(run_data.get("failed_cases", 0))
        cases = run_data.get("cases", [])
        total_time = sum(float(cast(int, case.get("duration_ms", 0))) / 1000 for case in cases)

        testsuites = Element("testsuites")
        testsuite = SubElement(testsuites, "testsuite")
        testsuite.set("name", str(run_data.get("run_id", "")))
        testsuite.set("tests", str(total))
        testsuite.set("failures", str(failed))
        testsuite.set("time", f"{total_time:.3f}")

        for case in cases:
            testcase = SubElement(testsuite, "testcase")
            testcase.set("name", str(case.get("case_id", "")))
            duration_ms = cast(int, case.get("duration_ms", 0))
            testcase.set("time", f"{float(duration_ms) / 1000:.3f}")
            if case.get("status") == "failed":
                failure = SubElement(testcase, "failure")
                failure.set("message", str(case.get("error", "")))
                failure.text = str(case.get("error", ""))

        rough_string = tostring(testsuites, encoding="unicode")
        return parseString(rough_string).toprettyxml(indent="  ")
