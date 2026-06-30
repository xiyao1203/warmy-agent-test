"""阈值校验逻辑测试。"""

from __future__ import annotations

import pytest
from agenttest.modules.test_plans.domain.threshold_validator import (
    ThresholdValidator,
    ValidationError,
)


class TestThresholdValidator:
    """阈值校验器测试。"""

    @pytest.fixture()
    def validator(self) -> ThresholdValidator:
        """创建校验器实例。"""
        return ThresholdValidator()

    def test_valid_pass_threshold(self, validator: ThresholdValidator) -> None:
        """测试有效的通过阈值。"""
        assert validator.validate_pass_threshold(0.8) is True
        assert validator.validate_pass_threshold(0.0) is True
        assert validator.validate_pass_threshold(1.0) is True

    def test_invalid_pass_threshold(self, validator: ThresholdValidator) -> None:
        """测试无效的通过阈值。"""
        with pytest.raises(ValidationError):
            validator.validate_pass_threshold(-0.1)
        with pytest.raises(ValidationError):
            validator.validate_pass_threshold(1.1)

    def test_valid_cost_budget(self, validator: ThresholdValidator) -> None:
        """测试有效的成本预算。"""
        assert validator.validate_cost_budget(100.0) is True
        assert validator.validate_cost_budget(0.01) is True

    def test_invalid_cost_budget(self, validator: ThresholdValidator) -> None:
        """测试无效的成本预算。"""
        with pytest.raises(ValidationError):
            validator.validate_cost_budget(0.0)
        with pytest.raises(ValidationError):
            validator.validate_cost_budget(-10.0)

    def test_valid_timeout(self, validator: ThresholdValidator) -> None:
        """测试有效的超时时间。"""
        assert validator.validate_timeout(30) is True
        assert validator.validate_timeout(1) is True

    def test_invalid_timeout(self, validator: ThresholdValidator) -> None:
        """测试无效的超时时间。"""
        with pytest.raises(ValidationError):
            validator.validate_timeout(0)
        with pytest.raises(ValidationError):
            validator.validate_timeout(-1)

    def test_valid_retry_count(self, validator: ThresholdValidator) -> None:
        """测试有效的重试次数。"""
        assert validator.validate_retry_count(3) is True
        assert validator.validate_retry_count(0) is True

    def test_invalid_retry_count(self, validator: ThresholdValidator) -> None:
        """测试无效的重试次数。"""
        with pytest.raises(ValidationError):
            validator.validate_retry_count(-1)

    def test_validate_all_valid(self, validator: ThresholdValidator) -> None:
        """测试全量校验通过。"""
        config = {
            "pass_threshold": 0.8,
            "cost_budget": 100.0,
            "timeout": 30,
            "retry_count": 3,
        }
        errors = validator.validate_all(config)
        assert len(errors) == 0

    def test_validate_all_invalid(self, validator: ThresholdValidator) -> None:
        """测试全量校验失败。"""
        config = {
            "pass_threshold": 1.5,
            "cost_budget": -10.0,
            "timeout": 0,
            "retry_count": -1,
        }
        errors = validator.validate_all(config)
        assert len(errors) == 4
