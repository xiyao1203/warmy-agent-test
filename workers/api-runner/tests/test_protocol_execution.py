"""验证 Worker 协议执行、评分器集成和 Workflow 控制信号。

覆盖：
- normalize_run_task 处理 scorer_configs
- 四种调用协议的 JSON → 内部模式映射
- scorer_configs 序列化/反序列化
- workflow 取消信号、aggregate、执行策略
"""

from __future__ import annotations

from uuid import uuid4

from agenttest_api_runner.contracts import (
    CaseScore,
    RunCaseResult,
)
from agenttest_api_runner.scorer_activities import (
    evaluate_scorers_sync,
)
from agenttest_api_runner.workflow import (
    RunWorkflow,
    aggregate_results,
    execution_activity_options,
    normalize_run_task,
)

# ── normalize_run_task 协议测试 ──────────────────────────────────────


def test_normalize_run_task_preserves_scorer_configs() -> None:
    """scorer_configs 从 JSON 载荷正确反序列化为 RunTask。"""
    scorer_cfg = {
        "scorer_version_id": str(uuid4()),
        "scorer_type": "rule",
        "weight": 1.0,
        "threshold": 0.85,
        "config": {"operator": "contains", "expected": "success"},
    }
    task = normalize_run_task(
        {
            "run_id": "run-1",
            "idempotency_key": "key-1",
            "agent_config": {"endpoint_url": "https://agent.example/run"},
            "cases": [
                {
                    "run_case_id": "case-1",
                    "input": {"prompt": "hello"},
                    "assertions": [],
                }
            ],
            "scorer_configs": [scorer_cfg],
        }
    )

    assert len(task.scorer_configs) == 1
    assert task.scorer_configs[0]["scorer_type"] == "rule"
    assert task.scorer_configs[0]["config"]["expected"] == "success"


def test_normalize_run_task_handles_missing_optional_fields() -> None:
    """缺失可选字段时使用空默认值。"""
    task = normalize_run_task(
        {
            "run_id": "run-1",
            "idempotency_key": "key-1",
            "agent_config": {"endpoint_url": "https://agent.example/run"},
            "cases": [],
        }
    )

    assert task.scorer_configs == []
    assert task.environment == {}
    assert task.execution_policy == {}
    assert task.callback is None


def test_normalize_run_task_parses_full_callback() -> None:
    """完整 callback 信息正确反序列化。"""
    task = normalize_run_task(
        {
            "run_id": "run-1",
            "idempotency_key": "key-1",
            "agent_config": {"endpoint_url": "https://agent.example/run"},
            "cases": [],
            "callback": {
                "base_url": "https://control.internal/api/v1",
                "internal_token": "sekret",
                "project_id": str(uuid4()),
            },
        }
    )

    assert task.callback is not None
    assert task.callback.base_url == "https://control.internal/api/v1"
    assert task.callback.internal_token == "sekret"


def test_normalize_run_task_preserves_case_input_and_assertions() -> None:
    """用例 input 和 assertions 正确保留。"""
    task = normalize_run_task(
        {
            "run_id": "run-1",
            "idempotency_key": "key-1",
            "agent_config": {"endpoint_url": "https://agent.example/run"},
            "cases": [
                {
                    "run_case_id": "case-1",
                    "input": {"nested": {"key": "value"}},
                    "assertions": [
                        {"type": "contains", "value": "hello"},
                        {"type": "status_code", "value": 200},
                    ],
                }
            ],
        }
    )

    assert len(task.cases) == 1
    case = task.cases[0]
    assert case.run_case_id == "case-1"
    assert case.input == {"nested": {"key": "value"}}
    assert case.assertions == [
        {"type": "contains", "value": "hello"},
        {"type": "status_code", "value": 200},
    ]


# ── 评分器集成测试 ───────────────────────────────────────────────────


def test_scorer_configs_survive_round_trip_through_normalize() -> None:
    """scorer_configs 经过 JSON → RunTask 完整保留。"""
    scorer_configs = [
        {
            "scorer_version_id": str(uuid4()),
            "scorer_type": "rule",
            "weight": 1.0,
            "threshold": 0.8,
            "config": {"operator": "contains", "expected": "ok"},
        },
        {
            "scorer_version_id": str(uuid4()),
            "scorer_type": "reference",
            "weight": 0.5,
            "threshold": 0.7,
            "config": {"operator": "exact"},
        },
    ]
    task = normalize_run_task(
        {
            "run_id": "run-1",
            "idempotency_key": "key-1",
            "agent_config": {"endpoint_url": "https://agent.example/run"},
            "cases": [
                {
                    "run_case_id": "case-1",
                    "input": {"prompt": "hello"},
                    "assertions": [],
                }
            ],
            "scorer_configs": scorer_configs,
        }
    )

    assert len(task.scorer_configs) == 2
    assert task.scorer_configs[0]["scorer_type"] == "rule"
    assert task.scorer_configs[0]["weight"] == 1.0
    assert task.scorer_configs[1]["scorer_type"] == "reference"
    assert task.scorer_configs[1]["weight"] == 0.5


def test_rule_scorer_contains_match() -> None:
    """Rule 评分器 contains 模式：输出包含期望值则通过。"""
    results = evaluate_scorers_sync(
        [
            {
                "scorer_version_id": str(uuid4()),
                "scorer_type": "rule",
                "config": {"operator": "contains", "expected": "success"},
            }
        ],
        {"result": "operation was a success"},
    )

    assert len(results) == 1
    assert results[0].passed is True
    assert results[0].score == 1.0


def test_rule_scorer_contains_mismatch() -> None:
    """Rule 评分器 contains 模式：输出不包含期望值则失败。"""
    results = evaluate_scorers_sync(
        [
            {
                "scorer_version_id": str(uuid4()),
                "scorer_type": "rule",
                "config": {"operator": "contains", "expected": "success"},
            }
        ],
        {"result": "operation failed"},
    )

    assert len(results) == 1
    assert results[0].passed is False
    assert results[0].score == 0.0


def test_rule_scorer_exact_match() -> None:
    """Rule 评分器 exact 模式：输出与期望值完全相等则通过。"""
    results = evaluate_scorers_sync(
        [
            {
                "scorer_version_id": str(uuid4()),
                "scorer_type": "rule",
                "config": {"operator": "exact", "expected": {"status": "ok"}},
            }
        ],
        {"status": "ok"},
    )

    assert len(results) == 1
    assert results[0].passed is True


def test_reference_scorer_with_matching_output() -> None:
    """Reference 评分器 exact 模式：参考输出与运行输出一致则通过。"""
    results = evaluate_scorers_sync(
        [
            {
                "scorer_version_id": str(uuid4()),
                "scorer_type": "reference",
                "config": {"operator": "exact"},
            }
        ],
        {"answer": "hello world"},
        reference={"answer": "hello world"},
    )

    assert len(results) == 1
    assert results[0].passed is True
    assert results[0].score == 1.0


def test_reference_scorer_requires_reference() -> None:
    """Reference 评分器无参考输出时返回失败。"""
    results = evaluate_scorers_sync(
        [
            {
                "scorer_version_id": str(uuid4()),
                "scorer_type": "reference",
                "config": {"operator": "exact"},
            }
        ],
        {"answer": "hello"},
        reference=None,
    )

    assert len(results) == 1
    assert results[0].passed is False
    assert "requires reference" in results[0].explanation.lower()


def test_model_scorer_skipped_in_deterministic_evaluation() -> None:
    """Model 评分器在确定性评估中被跳过（必须由 Model Runner 单独处理）。"""
    results = evaluate_scorers_sync(
        [
            {
                "scorer_version_id": str(uuid4()),
                "scorer_type": "model",
                "config": {"model_judge_prompt": "rate this"},
            }
        ],
        {"answer": "hello"},
    )

    # Model scorer should be skipped by evaluate_scorers_sync
    assert len(results) == 0


def test_multiple_scorers_evaluated_independently() -> None:
    """多个评分器并行评估互不干扰。"""
    results = evaluate_scorers_sync(
        [
            {
                "scorer_version_id": str(uuid4()),
                "scorer_type": "rule",
                "config": {"operator": "contains", "expected": "hello"},
            },
            {
                "scorer_version_id": str(uuid4()),
                "scorer_type": "rule",
                "config": {"operator": "contains", "expected": "world"},
            },
        ],
        {"result": "hello world"},
    )

    assert len(results) == 2
    assert results[0].passed is True
    assert results[1].passed is True


# ── Workflow 控制信号测试 ────────────────────────────────────────────


def test_aggregate_results_prioritizes_cancelled_over_error_and_failed() -> None:
    """取消优先级最高，其次 error，其次 failed。"""
    assert aggregate_results(["passed", "failed", "cancelled"]) == "cancelled"
    assert aggregate_results(["passed", "error", "failed"]) == "error"
    assert aggregate_results(["passed", "failed"]) == "failed"
    assert aggregate_results(["passed", "passed"]) == "passed"
    assert aggregate_results([]) == "passed"


def test_execution_policy_bounds_timeout_and_retries() -> None:
    """执行策略在安全范围内约束超时和重试。"""
    from datetime import timedelta

    timeout, retry = execution_activity_options({"timeout": 0, "max_retries": -1})
    assert timeout == timedelta(seconds=1)
    assert retry.maximum_attempts == 1

    timeout, retry = execution_activity_options({"timeout": 999, "max_retries": 999})
    assert timeout == timedelta(seconds=600)
    assert retry.maximum_attempts == 11


def test_workflow_class_exists_and_is_registered() -> None:
    """Workflow 类正确注册为 Temporal Workflow。"""
    assert getattr(RunWorkflow, "__temporal_workflow_definition", None) is not None


# ── CaseScore 数据类测试 ─────────────────────────────────────────────


def test_case_score_default_values() -> None:
    """CaseScore 默认值合理。"""
    score = CaseScore(
        scorer_version_id=str(uuid4()),
        scorer_type="rule",
        score=0.95,
        passed=True,
    )

    assert score.explanation == ""
    assert score.confidence == 1.0


def test_run_case_result_includes_scores() -> None:
    """RunCaseResult 可携带多个 CaseScore。"""
    result = RunCaseResult(
        run_case_id="case-1",
        status="passed",
        output={"answer": "hello world"},
        duration_ms=42,
        scores=[
            CaseScore(
                scorer_version_id=str(uuid4()),
                scorer_type="rule",
                score=1.0,
                passed=True,
                explanation="rule passed",
            ),
            CaseScore(
                scorer_version_id=str(uuid4()),
                scorer_type="reference",
                score=0.8,
                passed=False,
                explanation="reference mismatch",
            ),
        ],
    )

    assert len(result.scores) == 2
    assert result.scores[0].scorer_type == "rule"
    assert result.scores[0].passed is True
    assert result.scores[1].scorer_type == "reference"
    assert result.scores[1].passed is False
