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
        ResultCallbackConfig,
        RunCaseResult,
        RunCaseTask,
        RunResult,
        RunTask,
    )
    from agenttest_api_runner.reports import build_reports

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
        )
        for case in case_items
        if isinstance(case, dict)
    ]
    agent_config_raw = task.get("agent_config", {})
    environment_raw = task.get("environment", {})
    execution_policy_raw = task.get("execution_policy", {})
    return RunTask(
        run_id=str(task["run_id"]),
        idempotency_key=str(task["idempotency_key"]),
        cases=cases,
        agent_config=dict(agent_config_raw) if isinstance(agent_config_raw, dict) else {},
        environment=dict(environment_raw) if isinstance(environment_raw, dict) else {},
        execution_policy=(
            dict(execution_policy_raw) if isinstance(execution_policy_raw, dict) else {}
        ),
        callback=callback,
    )
