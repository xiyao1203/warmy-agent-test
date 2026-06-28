"""阈值校验逻辑。

校验测试计划配置的各项阈值是否有效。
"""

from __future__ import annotations

from dataclasses import dataclass


class ValidationError(Exception):
    """校验错误。"""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


@dataclass(frozen=True, slots=True)
class ThresholdValidator:
    """阈值校验器。

    校验规则：
    - pass_threshold: 0-100%（0.0-1.0）
    - cost_budget: > 0
    - timeout: > 0 秒
    - retry_count: >= 0 次
    """

    def validate_pass_threshold(self, threshold: float) -> bool:
        """校验通过阈值。

        Args:
            threshold: 通过阈值（0.0-1.0）。

        Returns:
            True 表示校验通过。

        Raises:
            ValidationError: 阈值不在有效范围。
        """
        if not (0.0 <= threshold <= 1.0):
            raise ValidationError(
                "pass_threshold",
                f"必须在 0.0-1.0 之间，当前值: {threshold}",
            )
        return True

    def validate_cost_budget(self, budget: float) -> bool:
        """校验成本预算。

        Args:
            budget: 成本预算（美元）。

        Returns:
            True 表示校验通过。

        Raises:
            ValidationError: 预算不在有效范围。
        """
        if budget <= 0:
            raise ValidationError(
                "cost_budget",
                f"必须大于 0，当前值: {budget}",
            )
        return True

    def validate_timeout(self, timeout: int) -> bool:
        """校验超时时间。

        Args:
            timeout: 超时时间（秒）。

        Returns:
            True 表示校验通过。

        Raises:
            ValidationError: 超时时间不在有效范围。
        """
        if timeout <= 0:
            raise ValidationError(
                "timeout",
                f"必须大于 0，当前值: {timeout}",
            )
        return True

    def validate_retry_count(self, retry_count: int) -> bool:
        """校验重试次数。

        Args:
            retry_count: 重试次数。

        Returns:
            True 表示校验通过。

        Raises:
            ValidationError: 重试次数不在有效范围。
        """
        if retry_count < 0:
            raise ValidationError(
                "retry_count",
                f"必须大于等于 0，当前值: {retry_count}",
            )
        return True

    def validate_all(self, config: dict[str, object]) -> list[ValidationError]:
        """全量校验配置。

        Args:
            config: 测试计划配置。

        Returns:
            错误列表，空列表表示校验通过。
        """
        errors: list[ValidationError] = []

        if "pass_threshold" in config:
            try:
                self.validate_pass_threshold(config["pass_threshold"])  # type: ignore[arg-type]
            except ValidationError as e:
                errors.append(e)

        if "cost_budget" in config:
            try:
                self.validate_cost_budget(config["cost_budget"])  # type: ignore[arg-type]
            except ValidationError as e:
                errors.append(e)

        if "timeout" in config:
            try:
                self.validate_timeout(config["timeout"])  # type: ignore[arg-type]
            except ValidationError as e:
                errors.append(e)

        if "retry_count" in config:
            try:
                self.validate_retry_count(config["retry_count"])  # type: ignore[arg-type]
            except ValidationError as e:
                errors.append(e)

        return errors
