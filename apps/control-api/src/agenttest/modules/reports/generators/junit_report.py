"""JUnit XML 报告生成器。"""

from __future__ import annotations

from typing import Any
from xml.dom.minidom import parseString
from xml.etree.ElementTree import Element, SubElement, tostring


class JunitReportGenerator:
    """JUnit XML 格式报告生成器。

    生成 CI/CD 集成的 JUnit XML 格式。
    """

    def generate(self, run_data: dict[str, Any]) -> str:
        """生成 JUnit XML 报告。

        Args:
            run_data: 运行数据。

        Returns:
            JUnit XML 字符串。
        """
        total = int(run_data.get("total_cases", 0))  # type: ignore[arg-type]
        failed = int(run_data.get("failed_cases", 0))  # type: ignore[arg-type]
        cases = run_data.get("cases", [])  # type: ignore[assignment]

        # 计算总时间
        total_time = sum(
            float(case.get("duration_ms", 0)) / 1000  # type: ignore[union-attr]
            for case in cases
        )

        # 创建根元素
        testsuites = Element("testsuites")
        testsuite = SubElement(testsuites, "testsuite")
        testsuite.set("name", str(run_data.get("run_id", "")))
        testsuite.set("tests", str(total))
        testsuite.set("failures", str(failed))
        testsuite.set("time", f"{total_time:.3f}")

        # 添加测试用例
        for case in cases:
            testcase = SubElement(testsuite, "testcase")
            testcase.set("name", str(case.get("case_id", "")))
            testcase.set("time", f"{float(case.get('duration_ms', 0)) / 1000:.3f}")

            if case.get("status") == "failed":
                failure = SubElement(testcase, "failure")
                failure.set("message", str(case.get("error", "")))
                failure.text = str(case.get("error", ""))

        # 格式化输出
        rough_string = tostring(testsuites, encoding="unicode")
        reparsed = parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
