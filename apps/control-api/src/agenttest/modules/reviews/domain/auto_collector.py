"""低置信度自动收集逻辑。

评分完成后自动将低置信度结果加入审核队列。

触发规则：
1. 评分置信度 < 0.7
2. 评分冲突（不同评分器结果差异 > 0.3）
3. 高风险用例（标记为 high_risk）
4. 安全测试发现
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AutoCollectCriteria:
    """自动收集条件配置。

    Attributes:
        confidence_threshold: 置信度阈值，低于此值自动收集。
        score_conflict_threshold: 评分冲突阈值，高于此差异自动收集。
        high_risk_enabled: 是否启用高风险用例自动收集。
        security_findings_enabled: 是否启用安全发现自动收集。
    """

    confidence_threshold: float = 0.7
    score_conflict_threshold: float = 0.3
    high_risk_enabled: bool = True
    security_findings_enabled: bool = True


class AutoCollector:
    """自动收集器。

    评估评分结果是否需要自动加入审核队列。
    """

    def __init__(self, criteria: AutoCollectCriteria | None = None) -> None:
        self._criteria = criteria or AutoCollectCriteria()

    def should_collect(self, result: dict[str, object]) -> bool:
        """判断结果是否需要自动收集。

        Args:
            result: 评分结果，包含 case_id, confidence, is_high_risk,
                    has_security_findings, scores 等字段。

        Returns:
            True 表示需要收集到审核队列。
        """
        confidence: float = result.get("confidence", 1.0)  # type: ignore[assignment]
        is_high_risk: bool = result.get("is_high_risk", False)  # type: ignore[assignment]
        has_security_findings: bool = result.get("has_security_findings", False)  # type: ignore[assignment]
        scores: dict[str, float] = result.get("scores", {})  # type: ignore[assignment]

        # 1. 低置信度
        if confidence < self._criteria.confidence_threshold:
            return True

        # 2. 评分冲突
        if self._has_score_conflict(scores):
            return True

        # 3. 高风险用例
        if self._criteria.high_risk_enabled and is_high_risk:
            return True

        # 4. 安全测试发现
        if self._criteria.security_findings_enabled and has_security_findings:
            return True

        return False

    def calculate_priority(self, result: dict[str, object]) -> int:
        """计算审核优先级（0-100，数值越高优先级越高）。

        Args:
            result: 评分结果。

        Returns:
            优先级数值。
        """
        confidence: float = result.get("confidence", 1.0)  # type: ignore[assignment]
        has_security_findings: bool = result.get("has_security_findings", False)  # type: ignore[assignment]
        is_high_risk: bool = result.get("is_high_risk", False)  # type: ignore[assignment]

        # 基础优先级：置信度越低，优先级越高
        base_priority = int((1.0 - confidence) * 100)

        # 安全发现加成
        if has_security_findings:
            base_priority += 20

        # 高风险用例加成
        if is_high_risk:
            base_priority += 10

        # 限制在 0-100 范围
        return min(max(base_priority, 0), 100)

    def _has_score_conflict(self, scores: dict[str, float]) -> bool:
        """判断是否存在评分冲突。

        Args:
            scores: 各评分器的分数。

        Returns:
            True 表示存在冲突。
        """
        if len(scores) < 2:
            return False

        values = list(scores.values())
        max_score = max(values)
        min_score = min(values)
        return (max_score - min_score) > self._criteria.score_conflict_threshold
