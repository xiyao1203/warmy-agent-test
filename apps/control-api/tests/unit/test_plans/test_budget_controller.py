"""成本预算控制测试。"""

from __future__ import annotations

import pytest

from agenttest.modules.test_plans.domain.budget_controller import (
    BudgetController,
    BudgetExceededError,
    BudgetWarningError,
)


class TestBudgetController:
    """预算控制器测试。"""

    @pytest.fixture()
    def controller(self) -> BudgetController:
        """创建控制器实例。"""
        return BudgetController(budget=100.0)

    def test_initial_state(self, controller: BudgetController) -> None:
        """测试初始状态。"""
        assert controller.budget == 100.0
        assert controller.used == 0.0
        assert controller.remaining == 100.0
        assert controller.usage_percent == 0.0

    def test_add_cost(self, controller: BudgetController) -> None:
        """测试添加成本。"""
        controller.add_cost(30.0)
        assert controller.used == 30.0
        assert controller.remaining == 70.0
        assert controller.usage_percent == 30.0

    def test_warning_at_80_percent(self, controller: BudgetController) -> None:
        """测试 80% 时警告。"""
        with pytest.raises(BudgetWarningError):
            controller.add_cost(85.0)

    def test_error_at_100_percent(self, controller: BudgetController) -> None:
        """测试 100% 时停止。"""
        with pytest.raises(BudgetExceededError):
            controller.add_cost(110.0)

    def test_multiple_costs(self, controller: BudgetController) -> None:
        """测试多次添加成本。"""
        controller.add_cost(30.0)
        controller.add_cost(40.0)
        assert controller.used == 70.0
        assert controller.remaining == 30.0

    def test_get_status(self, controller: BudgetController) -> None:
        """测试获取状态。"""
        controller.add_cost(50.0)
        status = controller.get_status()
        assert status["budget"] == 100.0
        assert status["used"] == 50.0
        assert status["remaining"] == 50.0
        assert status["usage_percent"] == 50.0
        assert status["is_warning"] is False
        assert status["is_exceeded"] is False

    def test_get_warning_status(self, controller: BudgetController) -> None:
        """测试警告状态。"""
        try:
            controller.add_cost(85.0)
        except BudgetWarningError:
            pass

        status = controller.get_status()
        assert status["is_warning"] is True
        assert status["is_exceeded"] is False
