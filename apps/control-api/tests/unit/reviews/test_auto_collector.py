"""低置信度自动收集逻辑测试。"""

from __future__ import annotations

from uuid import uuid4

import pytest

from agenttest.modules.reviews.domain.auto_collector import (
    AutoCollectCriteria,
    AutoCollector,
)
from agenttest.modules.reviews.domain.entities import ReviewStatus


class TestAutoCollectCriteria:
    """自动收集条件测试。"""

    def test_default_criteria(self) -> None:
        """测试默认条件配置。"""
        criteria = AutoCollectCriteria()
        assert criteria.confidence_threshold == 0.7
        assert criteria.score_conflict_threshold == 0.3
        assert criteria.high_risk_enabled is True
        assert criteria.security_findings_enabled is True

    def test_custom_criteria(self) -> None:
        """测试自定义条件配置。"""
        criteria = AutoCollectCriteria(
            confidence_threshold=0.8,
            score_conflict_threshold=0.2,
            high_risk_enabled=False,
        )
        assert criteria.confidence_threshold == 0.8
        assert criteria.score_conflict_threshold == 0.2
        assert criteria.high_risk_enabled is False


class TestAutoCollector:
    """自动收集器测试。"""

    @pytest.fixture()
    def collector(self) -> AutoCollector:
        """创建收集器实例。"""
        return AutoCollector()

    def test_low_confidence_should_collect(self, collector: AutoCollector) -> None:
        """测试低置信度结果应被收集。"""
        result = {
            "case_id": str(uuid4()),
            "confidence": 0.5,
            "is_high_risk": False,
            "has_security_findings": False,
            "scores": {},
        }
        assert collector.should_collect(result) is True

    def test_high_confidence_should_not_collect(self, collector: AutoCollector) -> None:
        """测试高置信度结果不应被收集。"""
        result = {
            "case_id": str(uuid4()),
            "confidence": 0.9,
            "is_high_risk": False,
            "has_security_findings": False,
            "scores": {},
        }
        assert collector.should_collect(result) is False

    def test_score_conflict_should_collect(self, collector: AutoCollector) -> None:
        """测试评分冲突结果应被收集。"""
        result = {
            "case_id": str(uuid4()),
            "confidence": 0.9,
            "is_high_risk": False,
            "has_security_findings": False,
            "scores": {"scorer_a": 0.9, "scorer_b": 0.5},
        }
        assert collector.should_collect(result) is True

    def test_high_risk_should_collect(self, collector: AutoCollector) -> None:
        """测试高风险用例应被收集。"""
        result = {
            "case_id": str(uuid4()),
            "confidence": 0.9,
            "is_high_risk": True,
            "has_security_findings": False,
            "scores": {},
        }
        assert collector.should_collect(result) is True

    def test_security_findings_should_collect(self, collector: AutoCollector) -> None:
        """测试安全测试发现应被收集。"""
        result = {
            "case_id": str(uuid4()),
            "confidence": 0.9,
            "is_high_risk": False,
            "has_security_findings": True,
            "scores": {},
        }
        assert collector.should_collect(result) is True

    def test_priority_higher_for_lower_confidence(self, collector: AutoCollector) -> None:
        """测试置信度越低，优先级越高。"""
        result_low = {
            "case_id": str(uuid4()),
            "confidence": 0.3,
            "is_high_risk": False,
            "has_security_findings": False,
            "scores": {},
        }
        result_high = {
            "case_id": str(uuid4()),
            "confidence": 0.6,
            "is_high_risk": False,
            "has_security_findings": False,
            "scores": {},
        }
        priority_low = collector.calculate_priority(result_low)
        priority_high = collector.calculate_priority(result_high)
        assert priority_low > priority_high

    def test_priority_boosted_for_security_findings(self, collector: AutoCollector) -> None:
        """测试安全发现会提升优先级。"""
        result = {
            "case_id": str(uuid4()),
            "confidence": 0.5,
            "is_high_risk": False,
            "has_security_findings": False,
            "scores": {},
        }
        result_security = {
            "case_id": str(uuid4()),
            "confidence": 0.5,
            "is_high_risk": False,
            "has_security_findings": True,
            "scores": {},
        }
        priority_normal = collector.calculate_priority(result)
        priority_security = collector.calculate_priority(result_security)
        assert priority_security > priority_normal
