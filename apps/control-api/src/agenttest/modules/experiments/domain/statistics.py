"""Experiment 统计分析服务。

提供 P50/P95 计算、退化项识别和聚合统计功能。
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetricStatistics:
    """单指标统计值对象。"""

    avg: float
    p50: float
    p95: float
    std_dev: float
    min_val: float
    max_val: float

    @classmethod
    def from_values(cls, values: list[float]) -> MetricStatistics:
        """从值列表计算统计。"""
        if not values:
            return cls(avg=0.0, p50=0.0, p95=0.0, std_dev=0.0, min_val=0.0, max_val=0.0)

        sorted_vals = sorted(values)
        n = len(sorted_vals)

        avg = statistics.mean(sorted_vals)
        p50_idx = int(n * 0.5)
        p95_idx = int(n * 0.95)
        p50 = sorted_vals[min(p50_idx, n - 1)]
        p95 = sorted_vals[min(p95_idx, n - 1)]
        std_dev = statistics.stdev(sorted_vals) if n > 1 else 0.0

        return cls(
            avg=round(avg, 4),
            p50=round(p50, 4),
            p95=round(p95, 4),
            std_dev=round(std_dev, 4),
            min_val=round(sorted_vals[0], 4),
            max_val=round(sorted_vals[-1], 4),
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "avg": self.avg,
            "p50": self.p50,
            "p95": self.p95,
            "std_dev": self.std_dev,
            "min_val": self.min_val,
            "max_val": self.max_val,
        }


@dataclass(frozen=True, slots=True)
class ExperimentStatistics:
    """实验统计结果值对象。"""

    total_cases: int
    passed: int
    failed: int
    pass_rate: float
    latency: MetricStatistics
    score: MetricStatistics
    cost: MetricStatistics

    def to_dict(self) -> dict[str, object]:
        return {
            "total_cases": self.total_cases,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": round(self.pass_rate, 4),
            "latency": self.latency.to_dict(),
            "score": self.score.to_dict(),
            "cost": self.cost.to_dict(),
        }


def calculate_statistics(cases: list[dict[str, object]]) -> ExperimentStatistics:
    """计算运行用例的统计信息。

    Args:
        cases: 用例列表，每项包含 status, duration_ms, score, cost 字段。

    Returns:
        ExperimentStatistics 统计结果。
    """
    if not cases:
        return ExperimentStatistics(
            total_cases=0,
            passed=0,
            failed=0,
            pass_rate=0.0,
            latency=MetricStatistics.from_values([]),
            score=MetricStatistics.from_values([]),
            cost=MetricStatistics.from_values([]),
        )

    passed = sum(1 for c in cases if c.get("status") == "passed")
    failed = sum(1 for c in cases if c.get("status") == "failed")
    total = len(cases)
    pass_rate = passed / total if total > 0 else 0.0

    # 提取有效值（忽略 None）
    durations = [value for c in cases if (value := _numeric(c.get("duration_ms"))) is not None]
    scores = [value for c in cases if (value := _numeric(c.get("score"))) is not None]
    costs = [value for c in cases if (value := _numeric(c.get("cost"))) is not None]

    return ExperimentStatistics(
        total_cases=total,
        passed=passed,
        failed=failed,
        pass_rate=pass_rate,
        latency=MetricStatistics.from_values(durations),
        score=MetricStatistics.from_values(scores),
        cost=MetricStatistics.from_values(costs),
    )


def identify_degradation(
    cases_a: list[dict[str, object]],
    cases_b: list[dict[str, object]],
    threshold: float = 0.2,
) -> list[dict[str, object]]:
    """识别退化项。

    比较两个运行的用例，找出退化项：
    - 状态退化：通过变失败
    - 分数退化：下降超过阈值
    - 时长退化：增加超过 50%

    Args:
        cases_a: 基准运行用例列表。
        cases_b: 当前运行用例列表。
        threshold: 分数退化阈值（默认 0.2）。

    Returns:
        退化项列表。
    """
    map_a = {c["test_case_id"]: c for c in cases_a}
    map_b = {c["test_case_id"]: c for c in cases_b}

    degradations = []

    for case_id, case_a in map_a.items():
        case_b = map_b.get(case_id)
        if case_b is None:
            continue  # B 中缺失不算退化

        # 状态退化
        status_a = case_a.get("status")
        status_b = case_b.get("status")
        if status_a == "passed" and status_b != "passed":
            degradations.append(
                {
                    "case_id": case_id,
                    "metric": "status",
                    "baseline": status_a,
                    "current": status_b,
                    "change": -1.0,
                }
            )
            continue

        # 分数退化
        score_a = case_a.get("score")
        score_b = case_b.get("score")
        score_a = _numeric(score_a)
        score_b = _numeric(score_b)
        if score_a is not None and score_b is not None:
            if score_a > 0 and (score_a - score_b) / score_a > threshold:
                degradations.append(
                    {
                        "case_id": case_id,
                        "metric": "score",
                        "baseline": score_a,
                        "current": score_b,
                        "change": round((score_b - score_a) / score_a, 4),
                    }
                )

        # 时长退化（增加超过 50%）
        dur_a = case_a.get("duration_ms")
        dur_b = case_b.get("duration_ms")
        dur_a = _numeric(dur_a)
        dur_b = _numeric(dur_b)
        if dur_a is not None and dur_b is not None:
            if dur_a > 0 and dur_b > dur_a * 1.5:
                degradations.append(
                    {
                        "case_id": case_id,
                        "metric": "duration",
                        "baseline": dur_a,
                        "current": dur_b,
                        "change": round((dur_b - dur_a) / dur_a, 4),
                    }
                )

    return degradations


def _numeric(value: object) -> float | None:
    if isinstance(value, (int, float, str)) and not isinstance(value, bool):
        try:
            return float(value)
        except ValueError:
            return None
    return None
