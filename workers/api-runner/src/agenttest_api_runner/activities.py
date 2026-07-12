from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from temporalio import activity

from agenttest_api_runner.adapter import AgentRequest, GenericHttpAgentAdapter
from agenttest_api_runner.callback import ControlPlaneCallback, ResultCallbackTask
from agenttest_api_runner.contracts import RunCaseResult, RunCaseTask
from agenttest_api_runner.credentials import CredentialLeaseClient


def build_agent_request(
    agent_config: dict[str, object],
    case_input: dict[str, object],
    *,
    environment: dict[str, object] | None = None,
    credential_values: dict[str, str] | None = None,
) -> AgentRequest:
    environment = environment or {}
    headers_raw = environment.get("headers", agent_config.get("headers", {}))
    headers = headers_raw if isinstance(headers_raw, dict) else {}
    timeout_raw = agent_config.get("timeout_seconds", 30)
    timeout_seconds = float(timeout_raw) if isinstance(timeout_raw, int | float | str) else 30.0
    protocol = str(agent_config.get("protocol", agent_config.get("mode", "sync")))
    mode = {
        "sync_json": "sync",
        "openai_chat": "sync",
        "sse": "stream",
        "async_poll": "poll",
    }.get(protocol, protocol)
    if mode not in {"sync", "stream", "poll"}:
        raise ValueError(f"Unsupported invocation protocol: {protocol}")
    endpoint = agent_config.get("endpoint_url", agent_config.get("url"))
    if not isinstance(endpoint, str) or not endpoint:
        raise ValueError("Agent invocation endpoint_url is required")
    variables_raw = environment.get("variables", {})
    variables = variables_raw if isinstance(variables_raw, dict) else {}
    template_raw = agent_config.get("request_template")
    request_template = dict(template_raw) if isinstance(template_raw, dict) else None
    resolved_url, resolved_headers = _apply_credentials(
        endpoint,
        {str(key): str(value) for key, value in headers.items()},
        environment,
        credential_values or {},
    )
    return AgentRequest(
        url=resolved_url,
        mode=mode,  # type: ignore[arg-type]
        headers=resolved_headers,
        input=case_input,
        variables={str(key): str(value) for key, value in variables.items()},
        request_template=request_template,
        response_path=str(agent_config.get("response_path", "output")),
        timeout_seconds=timeout_seconds,
    )


def _apply_credentials(
    endpoint: str,
    headers: dict[str, str],
    environment: dict[str, object],
    credential_values: dict[str, str],
) -> tuple[str, dict[str, str]]:
    raw_bindings = environment.get("credential_bindings", [])
    if not isinstance(raw_bindings, list) or not raw_bindings:
        return endpoint, headers
    parts = urlsplit(endpoint)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    for item in raw_bindings:
        if not isinstance(item, dict):
            raise ValueError("Invalid credential binding snapshot")
        name = str(item.get("injection_name", ""))
        value = credential_values.get(name)
        if value is None:
            raise ValueError("Credential lease is missing an injection value")
        if item.get("kind") == "bearer" and not value.lower().startswith("bearer "):
            value = f"Bearer {value}"
        location = item.get("injection_location")
        if location == "header":
            headers[name] = value
        elif location == "cookie":
            headers["Cookie"] = f"{name}={value}"
        elif location == "query":
            query[name] = value
        else:
            raise ValueError("Unsupported credential injection location")
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)
    ), headers


@activity.defn
async def execute_agent_case(
    task: RunCaseTask,
    agent_config: dict[str, Any],
    environment: dict[str, Any] | None = None,
) -> RunCaseResult:
    activity.heartbeat({"run_case_id": task.run_case_id, "phase": "execute"})
    resolved_environment = environment or {}
    lease = resolved_environment.get("_credential_lease", {})
    credential_values: dict[str, str] = {}
    if isinstance(lease, dict) and lease.get("binding_ids"):
        credential_values = await CredentialLeaseClient(
            str(lease.get("base_url", "")), str(lease.get("internal_token", ""))
        ).redeem(
            project_id=str(lease.get("project_id", "")),
            run_id=str(lease.get("run_id", "")),
            run_case_id=task.run_case_id,
            binding_ids=[str(item) for item in lease.get("binding_ids", [])],
        )
    adapter = GenericHttpAgentAdapter()
    try:
        result = await adapter.execute(
            build_agent_request(
                agent_config,
                task.input,
                environment=resolved_environment,
                credential_values=credential_values,
            )
        )
        return RunCaseResult(
            run_case_id=task.run_case_id,
            status=_evaluate_assertions(result.output, task.assertions),
            output=result.output,
            trace=result.trace,
            duration_ms=result.duration_ms,
        )
    finally:
        credential_values.clear()


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
