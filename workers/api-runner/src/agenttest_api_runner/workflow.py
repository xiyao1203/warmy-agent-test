from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from agenttest_api_runner.activities import execute_agent_case, post_run_result
    from agenttest_api_runner.browser_harness_activity import (
        CapturePageInput,
        capture_page_snapshot,
    )
    from agenttest_api_runner.callback import ResultCallbackTask
    from agenttest_api_runner.codex_browser_activity import (
        CodexBrowserResult,
        CodexBrowserTaskInput,
        run_codex_browser_case,
    )
    from agenttest_api_runner.contracts import (
        CaseScore,
        ResultCallbackConfig,
        RunCaseResult,
        RunCaseTask,
        RunResult,
        RunTask,
    )
    from agenttest_api_runner.deepeval_adapter import DeepEvalTask, evaluate_deepeval_case
    from agenttest_api_runner.playwright_activity import (
        PlaywrightResult,
        PlaywrightTaskInput,
        run_playwright_case,
    )
    from agenttest_api_runner.reports import build_reports
    from agenttest_api_runner.scorer_activities import evaluate_scorers_sync
    from agenttest_api_runner.tapnow_activity import (
        TapNowResult,
        TapNowTaskInput,
        run_tapnow_case,
    )

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
    timeout_seconds = max(1, min(_int_value(timeout_raw, 300), 600))
    max_retries = max(0, min(_int_value(retries_raw, 0), 10))
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


def _target_config(agent_config: dict[str, object]) -> dict[str, object]:
    raw = agent_config.get("target_config")
    return raw if isinstance(raw, dict) else {}


def _target_url(case_input: dict[str, object], agent_config: dict[str, object]) -> str:
    target_config = _target_config(agent_config)
    return str(
        case_input.get("url")
        or target_config.get("entry_url")
        or agent_config.get("canvas_url")
        or agent_config.get("endpoint_url")
        or ""
    )


def _target_browser_profile_id(
    case_input: dict[str, object],
    execution_policy: dict[str, object],
    agent_config: dict[str, object],
) -> str:
    target_config = _target_config(agent_config)
    return str(
        case_input.get("browser_profile_id")
        or execution_policy.get("browser_profile_id")
        or target_config.get("browser_profile_id")
        or ""
    )


@workflow.defn
class RunWorkflow:
    def __init__(self) -> None:
        self._cancel_requested = False

    @workflow.signal
    async def cancel(self) -> None:
        self._cancel_requested = True

    @workflow.run
    async def run(self, task: Any) -> RunResult:
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
                if case.execution_mode == "codex_explore":
                    codex_url = _target_url(case.input, task.agent_config)
                    browser_profile_id = _target_browser_profile_id(
                        case.input,
                        task.execution_policy,
                        task.agent_config,
                    )
                    codex_intent = str(case.input.get("test_intent", ""))
                    codex_result = await workflow.execute_activity(
                        run_codex_browser_case,
                        CodexBrowserTaskInput(
                            run_case_id=case.run_case_id,
                            test_intent=codex_intent,
                            target_url=codex_url,
                            timeout_seconds=_int_value(case.input.get("timeout"), 120),
                            model=_codex_model(case.input, task.execution_policy),
                            model_provider=_codex_model_provider(
                                case.input,
                                task.execution_policy,
                            ),
                            browser_profile_id=browser_profile_id,
                            browser_mode=_codex_browser_mode(
                                case.input,
                                {
                                    **task.execution_policy,
                                    "browser_profile_id": browser_profile_id,
                                },
                            ),
                            storage_state_key=str(case.input.get("storage_state_key", "")),
                            credentials=_extract_credentials(case.input),
                        ),
                        start_to_close_timeout=timedelta(
                            seconds=_int_value(case.input.get("timeout"), 120)
                        ),
                        heartbeat_timeout=timedelta(seconds=60),
                        retry_policy=RetryPolicy(
                            maximum_attempts=1,
                        ),
                    )
                    result = _codex_to_run_case(codex_result, case)
                    if result.status == "passed" and _is_canvas_target(task):
                        tapnow_result = await workflow.execute_activity(
                            run_tapnow_case,
                            _tapnow_task(task, case),
                            start_to_close_timeout=activity_timeout,
                            heartbeat_timeout=timedelta(seconds=30),
                            retry_policy=activity_retry_policy,
                        )
                        result = _tapnow_to_run_case(tapnow_result, case)
                elif case.execution_mode == "browser":
                    if _is_canvas_target(task):
                        tapnow_result = await workflow.execute_activity(
                            run_tapnow_case,
                            _tapnow_task(task, case),
                            start_to_close_timeout=activity_timeout,
                            heartbeat_timeout=timedelta(seconds=30),
                            retry_policy=activity_retry_policy,
                        )
                        result = _tapnow_to_run_case(tapnow_result, case)
                    else:
                        browser_url = _target_url(case.input, task.agent_config)
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
                        args=[case, task.agent_config, _environment_with_lease(task)],
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
                        evidence=result.evidence,
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
                    for scorer in task.scorer_configs:
                        if str(scorer.get("scorer_type")) != "deepeval":
                            continue
                        raw_config = scorer.get("config", {})
                        config = raw_config if isinstance(raw_config, dict) else {}
                        expected = config.get("expected_tools", [])
                        trace = result.evidence.get("trace", {})
                        tools = trace.get("tools_called", []) if isinstance(trace, dict) else []
                        deepeval_scores = await workflow.execute_activity(
                            evaluate_deepeval_case,
                            DeepEvalTask(
                                run_case_id=case.run_case_id,
                                scorer_version_id=str(scorer.get("scorer_version_id", "")),
                                intent=str(
                                    case.input.get("test_intent") or case.input.get("prompt") or ""
                                ),
                                output=str(result.output),
                                tools_called=[str(item) for item in tools]
                                if isinstance(tools, list)
                                else [],
                                expected_tools=[str(item) for item in expected]
                                if isinstance(expected, list)
                                else [],
                                threshold=float(scorer.get("threshold", 0.8) or 0.8),
                            ),
                            start_to_close_timeout=timedelta(minutes=3),
                            heartbeat_timeout=timedelta(seconds=30),
                            retry_policy=RetryPolicy(maximum_attempts=1),
                        )
                        result.scores.extend(deepeval_scores)
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
    browser_profile_snapshot_raw = task.get("browser_profile_snapshot", {})
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
        browser_profile_snapshot=(
            dict(browser_profile_snapshot_raw)
            if isinstance(browser_profile_snapshot_raw, dict)
            else {}
        ),
        callback=callback,
    )


def _is_canvas_target(task: RunTask) -> bool:
    target = _target_config(task.agent_config)
    plugin_id = str(target.get("plugin_id") or task.agent_config.get("plugin_id") or "")
    adapter_id = str(target.get("adapter_id") or task.agent_config.get("adapter_id") or "")
    return (
        task.agent_type in {"canvas", "canvas_agent"}
        or plugin_id in {"canvas-agent", "tapnow-canvas-agent"}
        or adapter_id.startswith("tapnow-canvas")
    )


def _environment_with_lease(task: RunTask) -> dict[str, object]:
    environment = dict(task.environment)
    if task.callback is None:
        return environment
    bindings = environment.get("credential_binding_ids", [])
    if not isinstance(bindings, list) or not bindings:
        return environment
    environment["_credential_lease"] = {
        "base_url": task.callback.base_url,
        "internal_token": task.callback.internal_token,
        "project_id": task.callback.project_id,
        "run_id": task.run_id,
        "binding_ids": [str(item) for item in bindings],
    }
    return environment


def _tapnow_task(task: RunTask, case: RunCaseTask) -> TapNowTaskInput:
    if task.callback is None:
        raise ValueError("TapNow execution requires a control plane callback")
    target = _target_config(task.agent_config)
    raw_bindings = (
        target.get("credential_binding_ids")
        or task.agent_config.get("credential_binding_ids")
        or task.environment.get("credential_binding_ids", [])
    )
    bindings = [str(item) for item in raw_bindings] if isinstance(raw_bindings, list) else []
    agent_id = str(
        task.agent_config.get("agent_id")
        or task.agent_config.get("agent_version_id")
        or task.run_id
    )
    login_raw = target.get("login")
    login_config = login_raw if isinstance(login_raw, dict) else {}
    login_strategy = str(login_config.get("strategy") or "none")
    browser_profile_id = str(target.get("browser_profile_id") or "")
    if login_strategy == "browser_profile":
        snapshot_profile_id = str(
            task.browser_profile_snapshot.get("browser_profile_id") or ""
        )
        if not browser_profile_id or snapshot_profile_id != browser_profile_id:
            raise ValueError("TapNow browser profile does not match the immutable run snapshot")
    return TapNowTaskInput(
        project_id=task.callback.project_id,
        run_id=task.run_id,
        run_case_id=case.run_case_id,
        agent_id=agent_id,
        target_url=_target_url(case.input, task.agent_config),
        intent=str(case.input.get("test_intent") or case.input.get("prompt") or ""),
        binding_ids=bindings,
        login_strategy=login_strategy,
        browser_profile_id=browser_profile_id,
        control_api_base_url=task.callback.base_url,
        internal_token=task.callback.internal_token,
        timeout_ms=_int_value(case.input.get("timeout_ms"), 120_000),
    )


def _tapnow_to_run_case(result: TapNowResult, case: RunCaseTask) -> RunCaseResult:
    raw_trace = result.evidence.get("trace")
    return RunCaseResult(
        run_case_id=case.run_case_id,
        status=result.status,
        output={"canvas": result.evidence.get("canvas", {})},
        trace=[dict(raw_trace)] if isinstance(raw_trace, dict) else [],
        error_type=result.error_type,
        error_message=result.error_message,
        evidence=result.evidence,
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


def _codex_browser_mode(
    case_input: dict[str, object],
    execution_policy: dict[str, object],
) -> str:
    """Resolve Codex browser mode.

    Selecting a browser profile means the run should reuse that profile's
    persistent user data directory unless the case explicitly overrides mode.
    """
    explicit = case_input.get("browser_mode")
    if isinstance(explicit, str) and explicit:
        return explicit
    profile_id = case_input.get("browser_profile_id") or execution_policy.get("browser_profile_id")
    return "persistent" if profile_id else "ephemeral"


def _codex_model(case_input: dict[str, object], execution_policy: dict[str, object]) -> str:
    """Resolve Codex model, keeping case-level overrides first."""

    return str(case_input.get("model") or execution_policy.get("codex_model") or "")


def _codex_model_provider(
    case_input: dict[str, object],
    execution_policy: dict[str, object],
) -> str:
    """Resolve Codex provider, keeping case-level overrides first."""

    return str(
        case_input.get("model_provider") or execution_policy.get("codex_model_provider") or ""
    )


def _extract_credentials(case_input: dict[str, object]) -> dict[str, str]:
    """从用例 input 中提取测试凭据。"""
    creds = case_input.get("credentials")
    if isinstance(creds, dict):
        return {str(k): str(v) for k, v in creds.items()}
    return {}


def _int_value(value: object, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int | float | str):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
    return default


def _codex_to_run_case(
    codex_result: CodexBrowserResult,
    case: RunCaseTask,
) -> RunCaseResult:
    """将 Codex 浏览器探索结果转换为 RunCaseResult。"""
    status = "passed" if codex_result.status == "planned" else codex_result.status
    output: dict[str, object] = {
        "status": codex_result.status,
        "execution_log": codex_result.execution_log[:2000] if codex_result.execution_log else "",
    }
    if codex_result.generated_script:
        output["generated_script"] = codex_result.generated_script
    if codex_result.screenshots:
        output["screenshot_count"] = len(codex_result.screenshots)
    return RunCaseResult(
        run_case_id=case.run_case_id,
        status=status,
        output=output,
        trace=[
            {
                "execution_log": codex_result.execution_log,
                "generated_script": codex_result.generated_script,
            }
        ],
        error_message=codex_result.error_message,
        duration_ms=codex_result.duration_ms,
    )


def _playwright_to_run_case(
    playwright_result: PlaywrightResult,
    case: RunCaseTask,
) -> RunCaseResult:
    """将 Playwright 执行结果转换为 RunCaseResult。"""
    status = playwright_result.status
    if status == "passed":
        # 运行 API 风格的断言检查（contains/exact）
        output: dict[str, object] = {
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
