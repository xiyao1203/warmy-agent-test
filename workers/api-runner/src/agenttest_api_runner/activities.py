from __future__ import annotations

from temporalio import activity

from agenttest_api_runner.adapter import AgentRequest, GenericHttpAgentAdapter
from agenttest_api_runner.callback import ControlPlaneCallback, ResultCallbackTask
from agenttest_api_runner.contracts import RunCaseResult, RunCaseTask


@activity.defn
async def execute_agent_case(
    task: RunCaseTask,
    agent_config: dict[str, object],
) -> RunCaseResult:
    activity.heartbeat({"run_case_id": task.run_case_id, "phase": "execute"})
    adapter = GenericHttpAgentAdapter()
    headers_raw = agent_config.get("headers", {})
    headers = headers_raw if isinstance(headers_raw, dict) else {}
    timeout_raw = agent_config.get("timeout_seconds", 30)
    timeout_seconds = float(timeout_raw) if isinstance(timeout_raw, int | float | str) else 30.0
    result = await adapter.execute(
        AgentRequest(
            url=str(agent_config["url"]),
            mode=str(agent_config.get("mode", "sync")),  # type: ignore[arg-type]
            headers={str(key): str(value) for key, value in headers.items()},
            input=task.input,
            timeout_seconds=timeout_seconds,
        )
    )
    return RunCaseResult(
        run_case_id=task.run_case_id,
        status=_evaluate_assertions(result.output, task.assertions),
        output=result.output,
        trace=result.trace,
        duration_ms=result.duration_ms,
    )


def _evaluate_assertions(
    output: dict[str, object],
    assertions: list[dict[str, object]],
) -> str:
    rendered = str(output)
    for assertion in assertions:
        kind = assertion.get("type")
        expected = assertion.get("value")
        if kind == "contains" and str(expected) not in rendered:
            return "failed"
        if kind == "exact" and output != expected:
            return "failed"
    return "passed"


@activity.defn
async def post_run_result(task: ResultCallbackTask) -> None:
    activity.heartbeat({"run_id": task.result.run_id, "phase": "callback"})
    await ControlPlaneCallback().post_result(task)
