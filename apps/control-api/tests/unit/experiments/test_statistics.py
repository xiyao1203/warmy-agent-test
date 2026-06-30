"""Experiment 统计分析服务测试。"""

from __future__ import annotations

import pytest
from agenttest.modules.experiments.domain.statistics import (
    ExperimentStatistics,
    MetricStatistics,
    calculate_statistics,
    identify_degradation,
)


class TestMetricStatistics:
    """MetricStatistics 值对象测试。"""

    def test_empty_list_returns_zero_stats(self):
        """空列表返回全零统计。"""
        stats = MetricStatistics.from_values([])
        assert stats.avg == 0.0
        assert stats.p50 == 0.0
        assert stats.p95 == 0.0
        assert stats.std_dev == 0.0
        assert stats.min_val == 0.0
        assert stats.max_val == 0.0

    def test_single_value(self):
        """单个值的统计。"""
        stats = MetricStatistics.from_values([100.0])
        assert stats.avg == 100.0
        assert stats.p50 == 100.0
        assert stats.p95 == 100.0
        assert stats.std_dev == 0.0
        assert stats.min_val == 100.0
        assert stats.max_val == 100.0

    def test_multiple_values(self):
        """多个值的统计计算。"""
        values = [100.0, 200.0, 300.0, 400.0, 500.0]
        stats = MetricStatistics.from_values(values)
        assert stats.avg == 300.0
        assert stats.p50 == 300.0
        assert stats.p95 == 500.0
        assert stats.min_val == 100.0
        assert stats.max_val == 500.0

    def test_to_dict(self):
        """序列化为字典。"""
        stats = MetricStatistics(
            avg=100.0, p50=90.0, p95=200.0, std_dev=10.0, min_val=50.0, max_val=250.0
        )
        result = stats.to_dict()
        assert result["avg"] == 100.0
        assert result["p50"] == 90.0
        assert result["p95"] == 200.0
        assert result["std_dev"] == 10.0
        assert result["min_val"] == 50.0
        assert result["max_val"] == 250.0


class TestExperimentStatistics:
    """ExperimentStatistics 值对象测试。"""

    def test_to_dict(self):
        """序列化为字典。"""
        latency = MetricStatistics(
            avg=100.0, p50=90.0, p95=200.0, std_dev=10.0, min_val=50.0, max_val=250.0
        )
        score = MetricStatistics(avg=0.8, p50=0.85, p95=0.6, std_dev=0.1, min_val=0.5, max_val=1.0)
        cost = MetricStatistics(
            avg=0.05, p50=0.04, p95=0.12, std_dev=0.02, min_val=0.01, max_val=0.15
        )
        stats = ExperimentStatistics(
            total_cases=10,
            passed=8,
            failed=2,
            pass_rate=0.8,
            latency=latency,
            score=score,
            cost=cost,
        )
        result = stats.to_dict()
        assert result["total_cases"] == 10
        assert result["passed"] == 8
        assert result["failed"] == 2
        assert result["pass_rate"] == 0.8
        assert "latency" in result
        assert "score" in result
        assert "cost" in result


class TestCalculateStatistics:
    """calculate_statistics 函数测试。"""

    def test_empty_cases(self):
        """空用例列表返回零统计。"""
        stats = calculate_statistics([])
        assert stats.total_cases == 0
        assert stats.passed == 0
        assert stats.failed == 0
        assert stats.pass_rate == 0.0

    def test_single_case_passed(self):
        """单个通过用例。"""
        cases = [{"status": "passed", "duration_ms": 100, "score": 0.9, "cost": 0.05}]
        stats = calculate_statistics(cases)
        assert stats.total_cases == 1
        assert stats.passed == 1
        assert stats.failed == 0
        assert stats.pass_rate == 1.0

    def test_multiple_cases(self):
        """多个用例统计。"""
        cases = [
            {"status": "passed", "duration_ms": 100, "score": 0.9, "cost": 0.05},
            {"status": "passed", "duration_ms": 200, "score": 0.8, "cost": 0.06},
            {"status": "failed", "duration_ms": 300, "score": 0.5, "cost": 0.10},
        ]
        stats = calculate_statistics(cases)
        assert stats.total_cases == 3
        assert stats.passed == 2
        assert stats.failed == 1
        assert stats.pass_rate == pytest.approx(0.6667, abs=0.001)
        assert stats.latency.avg == 200.0
        assert stats.score.avg == pytest.approx(0.7333, abs=0.001)

    def test_cases_with_null_values(self):
        """处理 null 值。"""
        cases = [
            {"status": "passed", "duration_ms": None, "score": None, "cost": None},
            {"status": "passed", "duration_ms": 100, "score": 0.9, "cost": 0.05},
        ]
        stats = calculate_statistics(cases)
        assert stats.total_cases == 2
        assert stats.latency.avg == 100.0  # 只计算非 null 值


class TestIdentifyDegradation:
    """identify_degradation 函数测试。"""

    def test_no_degradation(self):
        """无退化项。"""
        cases_a = [
            {"test_case_id": "tc1", "status": "passed", "score": 0.9, "duration_ms": 100},
        ]
        cases_b = [
            {"test_case_id": "tc1", "status": "passed", "score": 0.9, "duration_ms": 100},
        ]
        degradations = identify_degradation(cases_a, cases_b, threshold=0.2)
        assert len(degradations) == 0

    def test_score_degradation(self):
        """分数退化。"""
        cases_a = [
            {"test_case_id": "tc1", "status": "passed", "score": 0.9, "duration_ms": 100},
        ]
        cases_b = [
            {"test_case_id": "tc1", "status": "passed", "score": 0.5, "duration_ms": 100},
        ]
        degradations = identify_degradation(cases_a, cases_b, threshold=0.2)
        assert len(degradations) == 1
        assert degradations[0]["metric"] == "score"
        assert degradations[0]["baseline"] == 0.9
        assert degradations[0]["current"] == 0.5

    def test_status_degradation(self):
        """状态退化（通过变失败）。"""
        cases_a = [
            {"test_case_id": "tc1", "status": "passed", "score": 0.9, "duration_ms": 100},
        ]
        cases_b = [
            {"test_case_id": "tc1", "status": "failed", "score": 0.9, "duration_ms": 100},
        ]
        degradations = identify_degradation(cases_a, cases_b, threshold=0.2)
        assert len(degradations) == 1
        assert degradations[0]["metric"] == "status"

    def test_duration_degradation(self):
        """时长退化（超过 50%）。"""
        cases_a = [
            {"test_case_id": "tc1", "status": "passed", "score": 0.9, "duration_ms": 100},
        ]
        cases_b = [
            {"test_case_id": "tc1", "status": "passed", "score": 0.9, "duration_ms": 200},
        ]
        degradations = identify_degradation(cases_a, cases_b, threshold=0.2)
        assert len(degradations) == 1
        assert degradations[0]["metric"] == "duration"
        assert degradations[0]["baseline"] == 100
        assert degradations[0]["current"] == 200

    def test_missing_case_in_b(self):
        """B 中缺失用例。"""
        cases_a = [
            {"test_case_id": "tc1", "status": "passed", "score": 0.9, "duration_ms": 100},
        ]
        cases_b = []
        degradations = identify_degradation(cases_a, cases_b, threshold=0.2)
        assert len(degradations) == 0  # 缺失不算退化

    def test_improvement_not_reported(self):
        """提升不算退化。"""
        cases_a = [
            {"test_case_id": "tc1", "status": "failed", "score": 0.5, "duration_ms": 200},
        ]
        cases_b = [
            {"test_case_id": "tc1", "status": "passed", "score": 0.9, "duration_ms": 100},
        ]
        degradations = identify_degradation(cases_a, cases_b, threshold=0.2)
        assert len(degradations) == 0
