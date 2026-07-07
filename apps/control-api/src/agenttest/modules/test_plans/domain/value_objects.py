"""TestPlan 领域值对象。

定义 TestPlanConfig 不可变值对象——保存测试运行的
并发数、超时、重试策略、评分器和门禁阈值等配置。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class VersionStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


@dataclass(frozen=True, slots=True)
class TestPlanConfig:
    """测试计划运行配置值对象（不可变）。

    创建时校验所有字段合法性，发布后不可修改。

    Attributes:
        api_browser_ratio: API 与浏览器执行比例。
        runs_per_case: 每条用例运行次数，默认 1。
        concurrency: 并发数，默认 1。
        timeout: 单次执行超时秒数，默认 300。
        retry_policy: 重试策略。
        scorers: 评分器配置列表。
        pass_threshold: 通过阈值（0-1），默认 1.0。
        cost_budget: 费用预算上限（可选）。
    """

    api_browser_ratio: float = 0.0
    runs_per_case: int = 1
    concurrency: int = 1
    timeout: int = 300
    max_retries: int = 0
    retry_policy: dict[str, object] = field(default_factory=dict)
    scorers: list[dict[str, object]] = field(default_factory=list)
    pass_threshold: float = 1.0
    cost_budget: float | None = None
    baseline_run_id: str | None = None
    release_gate: dict[str, object] = field(default_factory=dict)
    scorer_ids: list[str] = field(default_factory=list)
    security_profile_ids: list[str] = field(default_factory=list)
    review_policy_id: str | None = None
    release_gate_id: str | None = None
    observation_only: bool = False
    browser_profile_id: str = ""
    codex_model_provider: str = ""
    codex_model: str = ""

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
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")

    def to_dict(self) -> dict[str, object]:
        """序列化为字典，用于 JSONB 列存储。"""
        return {
            "api_browser_ratio": self.api_browser_ratio,
            "runs_per_case": self.runs_per_case,
            "concurrency": self.concurrency,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_policy": self.retry_policy,
            "scorers": self.scorers,
            "pass_threshold": self.pass_threshold,
            "cost_budget": self.cost_budget,
            "baseline_run_id": self.baseline_run_id,
            "release_gate": self.release_gate,
            "scorer_ids": self.scorer_ids,
            "security_profile_ids": self.security_profile_ids,
            "review_policy_id": self.review_policy_id,
            "release_gate_id": self.release_gate_id,
            "observation_only": self.observation_only,
            "browser_profile_id": self.browser_profile_id,
            "codex_model_provider": self.codex_model_provider,
            "codex_model": self.codex_model,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> TestPlanConfig:
        """从字典反序列化（如从 JSONB 列读取）。"""
        cost_budget_raw = data.get("cost_budget")
        retry_policy_raw = data.get("retry_policy") or {}
        scorers_raw = data.get("scorers") or []
        abr_raw = data.get("api_browser_ratio", 0)
        rpc_raw = data.get("runs_per_case", 1)
        conc_raw = data.get("concurrency", 1)
        to_raw = data.get("timeout", 300)
        mr_raw = data.get("max_retries", 0)
        pt_raw = data.get("pass_threshold", 1.0)
        br_raw = data.get("baseline_run_id")
        rg_raw = data.get("release_gate") or {}
        scorer_ids_raw = data.get("scorer_ids") or []
        security_profile_ids_raw = data.get("security_profile_ids") or []
        return cls(
            api_browser_ratio=float(abr_raw) if isinstance(abr_raw, (int, float, str)) else 0.0,
            runs_per_case=int(rpc_raw) if isinstance(rpc_raw, (int, float, str)) else 1,
            concurrency=int(conc_raw) if isinstance(conc_raw, (int, float, str)) else 1,
            timeout=int(to_raw) if isinstance(to_raw, (int, float, str)) else 300,
            max_retries=int(mr_raw) if isinstance(mr_raw, (int, float, str)) else 0,
            retry_policy=(dict(retry_policy_raw) if isinstance(retry_policy_raw, dict) else {}),  # type: ignore[arg-type]
            scorers=(list(scorers_raw) if isinstance(scorers_raw, list) else []),  # type: ignore[arg-type]
            pass_threshold=float(pt_raw) if isinstance(pt_raw, (int, float, str)) else 1.0,
            cost_budget=(
                float(cost_budget_raw) if isinstance(cost_budget_raw, (int, float)) else None
            ),
            baseline_run_id=str(br_raw) if isinstance(br_raw, str) else None,
            release_gate=(dict(rg_raw) if isinstance(rg_raw, dict) else {}),  # type: ignore[arg-type]
            scorer_ids=[str(item) for item in scorer_ids_raw]
            if isinstance(scorer_ids_raw, list)
            else [],
            security_profile_ids=[str(item) for item in security_profile_ids_raw]
            if isinstance(security_profile_ids_raw, list)
            else [],
            review_policy_id=str(data["review_policy_id"])
            if data.get("review_policy_id")
            else None,
            release_gate_id=str(data["release_gate_id"]) if data.get("release_gate_id") else None,
            observation_only=bool(data.get("observation_only", False)),
            browser_profile_id=str(data.get("browser_profile_id", "")),
            codex_model_provider=str(data.get("codex_model_provider", "")),
            codex_model=str(data.get("codex_model", "")),
        )

    def dry_run_preview(self, *, num_cases: int = 0) -> dict[str, object]:
        """试运行预览：返回预计用例数、配置参数。"""
        return {
            "estimated_cases": num_cases,
            "concurrency": self.concurrency,
            "timeout_seconds": self.timeout,
            "max_retries": self.max_retries,
            "cost_budget": self.cost_budget,
            "pass_threshold": self.pass_threshold,
            "baseline_run_id": self.baseline_run_id,
            "release_gate": self.release_gate,
        }
