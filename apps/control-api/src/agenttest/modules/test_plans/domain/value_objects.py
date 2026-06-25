"""TestPlan domain value objects and enums."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class VersionStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


@dataclass(frozen=True, slots=True)
class TestPlanConfig:
    api_browser_ratio: float = 0.0
    runs_per_case: int = 1
    concurrency: int = 1
    timeout: int = 300
    retry_policy: dict[str, object] = field(default_factory=dict)
    scorers: list[dict[str, object]] = field(default_factory=list)
    pass_threshold: float = 1.0
    cost_budget: float | None = None

    def __post_init__(self) -> None:
        if self.runs_per_case < 1:
            raise ValueError("runs_per_case must be >= 1")
        if self.concurrency < 1:
            raise ValueError("concurrency must be >= 1")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if not (0.0 <= self.pass_threshold <= 1.0):
            raise ValueError("pass_threshold must be between 0 and 1")
        if self.cost_budget is not None and self.cost_budget < 0:
            raise ValueError("cost_budget must be non-negative")

    def to_dict(self) -> dict[str, object]:
        return {
            "api_browser_ratio": self.api_browser_ratio,
            "runs_per_case": self.runs_per_case,
            "concurrency": self.concurrency,
            "timeout": self.timeout,
            "retry_policy": self.retry_policy,
            "scorers": self.scorers,
            "pass_threshold": self.pass_threshold,
            "cost_budget": self.cost_budget,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> TestPlanConfig:
        cost_budget_raw = data.get("cost_budget")
        retry_policy_raw = data.get("retry_policy") or {}
        scorers_raw = data.get("scorers") or []
        abr_raw = data.get("api_browser_ratio", 0)
        rpc_raw = data.get("runs_per_case", 1)
        conc_raw = data.get("concurrency", 1)
        to_raw = data.get("timeout", 300)
        pt_raw = data.get("pass_threshold", 1.0)
        return cls(
            api_browser_ratio=float(abr_raw) if isinstance(abr_raw, (int, float, str)) else 0.0,
            runs_per_case=int(rpc_raw) if isinstance(rpc_raw, (int, float, str)) else 1,
            concurrency=int(conc_raw) if isinstance(conc_raw, (int, float, str)) else 1,
            timeout=int(to_raw) if isinstance(to_raw, (int, float, str)) else 300,
            retry_policy=(
                dict(retry_policy_raw)
                if isinstance(retry_policy_raw, dict)
                else {}
            ),  # type: ignore[arg-type]
            scorers=(
                list(scorers_raw)
                if isinstance(scorers_raw, list)
                else []
            ),  # type: ignore[arg-type]
            pass_threshold=float(pt_raw) if isinstance(pt_raw, (int, float, str)) else 1.0,
            cost_budget=(
                float(cost_budget_raw)
                if isinstance(cost_budget_raw, (int, float))
                else None
            ),
        )
