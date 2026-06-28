"""成本预算控制。

实时计算已用成本，监控预算使用情况。
"""

from __future__ import annotations

from dataclasses import dataclass, field


class BudgetWarningError(Exception):
    """预算警告（超过 80%）。"""

    def __init__(self, usage_percent: float) -> None:
        self.usage_percent = usage_percent
        super().__init__(f"预算使用已达 {usage_percent:.1f}%，超过 80% 警告线")


class BudgetExceededError(Exception):
    """预算超支（超过 100%）。"""

    def __init__(self, usage_percent: float) -> None:
        self.usage_percent = usage_percent
        super().__init__(f"预算使用已达 {usage_percent:.1f}%，已超预算")


@dataclass(slots=True)
class BudgetController:
    """预算控制器。

    功能：
    - 实时计算已用成本
    - 超过预算 80% 时警告
    - 超过预算 100% 时停止执行

    Attributes:
        budget: 预算总额（美元）。
        used: 已用金额。
    """

    budget: float
    used: float = field(default=0.0)

    @property
    def remaining(self) -> float:
        """剩余金额。"""
        return self.budget - self.used

    @property
    def usage_percent(self) -> float:
        """使用百分比。"""
        if self.budget <= 0:
            return 0.0
        return (self.used / self.budget) * 100

    @property
    def is_warning(self) -> bool:
        """是否处于警告状态（>= 80%）。"""
        return self.usage_percent >= 80

    @property
    def is_exceeded(self) -> bool:
        """是否超支（>= 100%）。"""
        return self.usage_percent >= 100

    def add_cost(self, amount: float) -> None:
        """添加成本。

        Args:
            amount: 成本金额（美元）。

        Raises:
            BudgetWarningError: 超过 80% 警告线。
            BudgetExceededError: 超过 100% 预算。
        """
        new_used = self.used + amount
        new_percent = (new_used / self.budget) * 100 if self.budget > 0 else 0

        if new_percent >= 100:
            self.used = new_used
            raise BudgetExceededError(new_percent)

        if new_percent >= 80:
            self.used = new_used
            raise BudgetWarningError(new_percent)

        self.used = new_used

    def get_status(self) -> dict[str, object]:
        """获取预算状态。

        Returns:
            包含预算状态的字典。
        """
        return {
            "budget": self.budget,
            "used": self.used,
            "remaining": self.remaining,
            "usage_percent": self.usage_percent,
            "is_warning": self.is_warning,
            "is_exceeded": self.is_exceeded,
        }
