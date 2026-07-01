from __future__ import annotations

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from agenttest_api_runner.activities import execute_agent_case, post_run_result
    from agenttest_api_runner.browser_harness_activity import (
        CapturePageInput,
        capture_page_snapshot,
    )
    from agenttest_api_runner.callback import ResultCallbackTask
    from agenttest_api_runner.contracts import (
        CaseScore,
        ResultCallbackConfig,
        RunCaseResult,
        RunCaseTask,
        RunResult,
        RunTask,
    )
    from agenttest_api_runner.playwright_activity import (
        PlaywrightResult,
        PlaywrightTaskInput,
        run_playwright_case,
    )
    from agenttest_api_runner.reports import build_reports
    from agenttest_api_runner.scorer_activities import evaluate_scorers_sync

ACTIVITY_TIMEOUT = timedelta(minutes=5)
ACTIVITY_RETRY_POLICY = RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2,
    maximum_interval=timedelta(seconds=10),
    maximum_attempts=3,
    non_retryable_error_types=[
        "ValidationError",
        "PermissionError",
        "TargetProductError",
    ],
)


def execution_activity_options(
    policy: dict[str, object],
) -> tuple[timedelta, RetryPolicy]:
    """Translate a published plan policy into bounded Temporal options."""
    timeout_raw = policy.get("timeout", 300)
    retries_raw = policy.get("max_retries", 0)
    retry_config = policy.get("retry_policy", {})
    timeout_seconds = max(1, min(int(timeout_raw), 600))
    max_retries = max(0, min(int(retries_raw), 10))
    retry_values = retry_config if isinstance(retry_config, dict) else {}
    coefficient_raw = retry_values.get("backoff_coefficient", 2.0)
    coefficient = max(1.0, min(float(coefficient_raw), 10.0))
    return timedelta(seconds=timeout_seconds), RetryPolicy(
        initial_interval=timedelta(seconds=1),
        backoff_coefficient=coefficient,
        maximum_interval=timedelta(seconds=10),
        maximum_attempts=max_retries + 1,
        non_retryable_error_types=ACTIVITY_RETRY_POLICY.non_retryable_error_types,
    )


def aggregate_results(statuses: list[str]) -> str:
    if "cancelled" in statuses:
        return "cancelled"
    if "error" in statuses:
        return "error"
    if "failed" in statuses:
        return "failed"
    return "passed"


@workflow.defn
class RunWorkflow:
    def __init__(self) -> None:
        self._cancel_requested = False

    @workflow.signal
    async def cancel(self) -> None:
        self._cancel_requested = True

    @workflow.run
    async def run(self, task: RunTask | dict[str, object]) -> RunResult:
        task = normalize_run_task(task)
        activity_timeout, activity_retry_policy = execution_activity_options(task.execution_policy)
        results: list[RunCaseResult] = []
        for case in task.cases:
            if self._cancel_requested:
                results.append(
                    RunCaseResult(
                        run_case_id=case.run_case_id,
                        status="cancelled",
                        error_type="CancelledError",
                        error_message="Run cancellation requested",
                    )
                )
                continue
            try:
                # ── 执行模式分发 ─────────────────────────────────
                if case.execution_mode == "browser":
                    browser_url = str(
                        case.input.get(
                            "url",
                            task.agent_config.get(
                                "canvas_url",
                                task.agent_config.get("endpoint_url", ""),
                            ),
                        )
                    )
                    browser_steps = _browser_steps(case.input)
                    playwright_result = await workflow.execute_activity(
                        run_playwright_case,
                        PlaywrightTaskInput(
                            run_case_id=case.run_case_id,
                            url=browser_url,
                            steps=browser_steps,
                        ),
                        start_to_close_timeout=activity_timeout,
                        heartbeat_timeout=timedelta(seconds=30),
                        retry_policy=activity_retry_policy,
                    )
                    result = _playwright_to_run_case(playwright_result, case)
                else:
                    # ── Browser Harness 前置采集（可选） ──────────────────
                    capture_url = task.agent_config.get("pre_capture_url")
                    if capture_url and isinstance(capture_url, str):
                        await workflow.execute_activity(
                            capture_page_snapshot,
                            CapturePageInput(
                                url=capture_url,
                                run_case_id=case.run_case_id,
                            ),
                            start_to_close_timeout=timedelta(seconds=30),
                            retry_policy=RetryPolicy(
                                maximum_attempts=2,
                            ),
                        )

                    result = await workflow.execute_activity(
                        execute_agent_case,
                        args=[case, task.agent_config, task.environment],
                        start_to_close_timeout=activity_timeout,
                        heartbeat_timeout=timedelta(seconds=30),
                        retry_policy=activity_retry_policy,
                    )
                # ── 执行确定性评分器 ───────────────────────────────
                if task.scorer_configs and result.status == "passed" and result.output:
                    scorer_results = evaluate_scorers_sync(
                        task.scorer_configs,
                        result.output,
                        reference=dict(case.input) if case.assertions else None,
                    )
                    result = RunCaseResult(
                        run_case_id=result.run_case_id,
                        status=result.status,
                        output=result.output,
                        trace=result.trace,
                        error_type=result.error_type,
                        error_message=result.error_message,
                        duration_ms=result.duration_ms,
                        scores=[
                            CaseScore(
                                scorer_version_id=r.scorer_version_id,
                                scorer_type=r.scorer_type,
                                score=r.score,
                                passed=r.passed,
                                explanation=r.explanation,
                                confidence=r.confidence,
                            )
                            for r in scorer_results
                        ],
                    )
            except Exception as error:
                result = RunCaseResult(
                    run_case_id=case.run_case_id,
                    status="error",
                    error_type=type(error).__name__,
                    error_message=str(error),
                )
            results.append(result)
        run_result = RunResult(
            run_id=task.run_id,
            status=aggregate_results([result.status for result in results]),
            cases=results,
        )
        run_result = RunResult(
            run_id=run_result.run_id,
            status=run_result.status,
            cases=run_result.cases,
            reports=build_reports(run_result),
        )
        callback_task = callback_task_for(task, run_result)
        if callback_task is not None:
            await workflow.execute_activity(
                post_run_result,
                args=[callback_task],
                start_to_close_timeout=ACTIVITY_TIMEOUT,
                heartbeat_timeout=timedelta(seconds=30),
                retry_policy=ACTIVITY_RETRY_POLICY,
            )
        return run_result


def callback_task_for(task: RunTask, result: RunResult) -> ResultCallbackTask | None:
    if task.callback is None:
        return None
    return ResultCallbackTask(
        base_url=task.callback.base_url,
        internal_token=task.callback.internal_token,
        project_id=task.callback.project_id,
        result=result,
    )


def normalize_run_task(task: RunTask | dict[str, object]) -> RunTask:
    if isinstance(task, RunTask):
        return task
    callback_raw = task.get("callback")
    callback = None
    if isinstance(callback_raw, dict):
        callback = ResultCallbackConfig(
            base_url=str(callback_raw["base_url"]),
            internal_token=str(callback_raw["internal_token"]),
            project_id=str(callback_raw["project_id"]),
        )
    cases_raw = task.get("cases", [])
    case_items = cases_raw if isinstance(cases_raw, list) else []
    cases = [
        RunCaseTask(
            run_case_id=str(case["run_case_id"]),
            input=dict(case.get("input", {})),
            assertions=list(case.get("assertions", [])),
            execution_mode=str(case.get("execution_mode", "api")),
        )
        for case in case_items
        if isinstance(case, dict)
    ]
    agent_config_raw = task.get("agent_config", {})
    environment_raw = task.get("environment", {})
    execution_policy_raw = task.get("execution_policy", {})
    scorer_configs_raw = task.get("scorer_configs", [])
    return RunTask(
        run_id=str(task["run_id"]),
        idempotency_key=str(task["idempotency_key"]),
        cases=cases,
        agent_config=dict(agent_config_raw) if isinstance(agent_config_raw, dict) else {},
        agent_type=str(task.get("agent_type", "generic_http")),
        environment=dict(environment_raw) if isinstance(environment_raw, dict) else {},
        execution_policy=(
            dict(execution_policy_raw) if isinstance(execution_policy_raw, dict) else {}
        ),
        scorer_configs=(
            [dict(item) for item in scorer_configs_raw if isinstance(item, dict)]
            if isinstance(scorer_configs_raw, list)
            else []
        ),
        callback=callback,
    )


def _browser_steps(case_input: dict[str, object]) -> list[dict[str, str]]:
    """从用例 input 中提取 Playwright 操作步骤。"""
    raw = case_input.get("steps")
    if isinstance(raw, list):
        return [
            {
                "action": str(step.get("action", "")),
                "target": str(step.get("target", "")),
                "value": str(step.get("value", "")),
            }
            for step in raw
            if isinstance(step, dict)
        ]
    return []


def _playwright_to_run_case(
    playwright_result: PlaywrightResult,
    case: RunCaseTask,
) -> RunCaseResult:
    """将 Playwright 执行结果转换为 RunCaseResult。"""
    status = playwright_result.status
    if status == "passed":
        # 运行 API 风格的断言检查（contains/exact）
        output = {
            "page_title": playwright_result.page_title,
            "final_url": playwright_result.final_url,
        }
        from agenttest_api_runner.activities import _evaluate_assertions
        assertion_status = _evaluate_assertions(output, case.assertions)
        if assertion_status != "passed":
            status = assertion_status
        return RunCaseResult(
            run_case_id=case.run_case_id,
            status=status,
            output=output,
            trace=[
                {
                    "step_index": s.step_index,
                    "action": s.action,
                    "target": s.target,
                    "status": s.status,
                    "error": s.error,
                }
                for s in playwright_result.steps
            ],
            error_message=playwright_result.error_message,
        )
    return RunCaseResult(
        run_case_id=case.run_case_id,
        status=status,
        error_message=playwright_result.error_message,
    )
