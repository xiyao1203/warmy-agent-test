"""报告生成器测试。"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from agenttest.modules.reports.generators.json_report import JsonReportGenerator
from agenttest.modules.reports.generators.junit_report import JunitReportGenerator
from agenttest.modules.reports.generators.html_report import HtmlReportGenerator


@pytest.fixture()
def mock_run_data() -> dict[str, object]:
    """模拟运行数据。"""
    return {
        "run_id": "run-123",
        "plan_id": "plan-456",
        "status": "completed",
        "started_at": datetime(2026, 6, 29, 10, 0, 0).isoformat(),
        "completed_at": datetime(2026, 6, 29, 10, 5, 0).isoformat(),
        "total_cases": 10,
        "passed_cases": 8,
        "failed_cases": 2,
        "cases": [
            {
                "case_id": "case-1",
                "status": "passed",
                "duration_ms": 1000,
                "scorer_results": [
                    {"scorer": "accuracy", "score": 0.95},
                ],
            },
            {
                "case_id": "case-2",
                "status": "failed",
                "duration_ms": 2000,
                "error": "AssertionError: expected 'A' but got 'B'",
                "scorer_results": [
                    {"scorer": "accuracy", "score": 0.3},
                ],
            },
        ],
    }


class TestJsonReportGenerator:
    """JSON 报告生成器测试。"""

    def test_generate_json_report(self, mock_run_data: dict[str, object]) -> None:
        """测试生成 JSON 报告。"""
        generator = JsonReportGenerator()
        report = generator.generate(mock_run_data)
        
        assert isinstance(report, str)
        data = json.loads(report)
        assert data["run_id"] == "run-123"
        assert data["total_cases"] == 10
        assert data["passed_cases"] == 8

    def test_json_report_contains_cases(self, mock_run_data: dict[str, object]) -> None:
        """测试 JSON 报告包含用例。"""
        generator = JsonReportGenerator()
        report = generator.generate(mock_run_data)
        data = json.loads(report)
        
        assert len(data["cases"]) == 2
        assert data["cases"][0]["case_id"] == "case-1"

    def test_json_report_has_metadata(self, mock_run_data: dict[str, object]) -> None:
        """测试 JSON 报告包含元数据。"""
        generator = JsonReportGenerator()
        report = generator.generate(mock_run_data)
        data = json.loads(report)
        
        assert "generated_at" in data
        assert "format_version" in data


class TestJunitReportGenerator:
    """JUnit XML 报告生成器测试。"""

    def test_generate_junit_report(self, mock_run_data: dict[str, object]) -> None:
        """测试生成 JUnit XML 报告。"""
        generator = JunitReportGenerator()
        report = generator.generate(mock_run_data)
        
        assert isinstance(report, str)
        assert '<?xml version="1.0"' in report
        assert "<testsuite" in report

    def test_junit_report_contains_tests(self, mock_run_data: dict[str, object]) -> None:
        """测试 JUnit 报告包含测试用例。"""
        generator = JunitReportGenerator()
        report = generator.generate(mock_run_data)
        
        assert 'name="case-1"' in report
        assert 'name="case-2"' in report
        assert "<failure" in report

    def test_junit_report_has_summary(self, mock_run_data: dict[str, object]) -> None:
        """测试 JUnit 报告包含摘要。"""
        generator = JunitReportGenerator()
        report = generator.generate(mock_run_data)
        
        assert 'tests="10"' in report
        assert 'failures="2"' in report


class TestHtmlReportGenerator:
    """HTML 报告生成器测试。"""

    def test_generate_html_report(self, mock_run_data: dict[str, object]) -> None:
        """测试生成 HTML 报告。"""
        generator = HtmlReportGenerator()
        report = generator.generate(mock_run_data)
        
        assert isinstance(report, str)
        assert "<!DOCTYPE html>" in report
        assert "<html" in report

    def test_html_report_contains_summary(self, mock_run_data: dict[str, object]) -> None:
        """测试 HTML 报告包含摘要。"""
        generator = HtmlReportGenerator()
        report = generator.generate(mock_run_data)
        
        assert "run-123" in report
        assert "10" in report  # total cases
        assert "8" in report   # passed

    def test_html_report_contains_table(self, mock_run_data: dict[str, object]) -> None:
        """测试 HTML 报告包含用例表格。"""
        generator = HtmlReportGenerator()
        report = generator.generate(mock_run_data)
        
        assert "<table" in report
        assert "case-1" in report
        assert "case-2" in report
