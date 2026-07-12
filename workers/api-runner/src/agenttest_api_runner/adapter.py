from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from time import monotonic
from typing import Literal

import httpx

SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key", "api-key"}
SENSITIVE_EVIDENCE_KEYS = {
    "api_key",
    "authorization",
    "cookie",
    "credentials",
    "password",
    "secret",
    "secret_key",
    "token",
}
TARGET_EVIDENCE_KEYS = {"scenario", "request_id", "attempt", "tool_calls", "artifacts"}
SECURITY_SIGNALS = {"prompt_injection", "data_leak_attempt", "privilege_escalation"}


class TargetProductError(Exception):
    """待测 Agent 返回确定性业务错误。"""

    def __init__(
        self,
        message: str,
        *,
        code: str = "target_product_error",
        evidence: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.evidence = dict(evidence or {})


class TransientError(Exception):
    """网络或临时依赖错误，可由 Temporal 重试。"""


@dataclass(frozen=True, slots=True)
class AgentRequest:
    url: str
    input: dict[str, object]
    variables: dict[str, str] = field(default_factory=dict)
    request_template: dict[str, object] | None = None
    response_path: str = "output"
    mode: Literal["sync", "stream", "poll"] = "sync"
    headers: dict[str, str] = field(default_factory=dict)
    timeout_seconds: float = 30
    poll_url_field: str = "status_url"
    poll_interval_seconds: float = 0.25


@dataclass(frozen=True, slots=True)
class AgentResult:
    output: dict[str, object]
    tool_calls: list[dict[str, object]]
    trace: list[dict[str, object]]
    duration_ms: int
    evidence: dict[str, object] = field(default_factory=dict)


class GenericHttpAgentAdapter:
    def __init__(self, *, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(trust_env=False)
        self._owns_client = client is None

    async def execute(self, request: AgentRequest) -> AgentResult:
        started = monotonic()
        attributes: dict[str, object] = {
            "http.request.method": "POST",
            "url.full": request.url,
            **{
                f"http.request.header.{name.lower()}": (
                    "***" if name.lower() in SENSITIVE_HEADERS else value
                )
                for name, value in request.headers.items()
            },
        }
        trace: list[dict[str, object]] = [
            {
                "name": "http.request",
                "attributes": attributes,
            }
        ]
        try:
            response = await self._client.post(
                request.url,
                json=_render_request(request),
                headers=request.headers,
                timeout=request.timeout_seconds,
            )
            if response.status_code >= 400:
                code, evidence = _error_details(response)
                if response.status_code >= 500 or response.status_code in {408, 425}:
                    raise TransientError(f"Target returned HTTP {response.status_code}")
                raise TargetProductError(
                    f"Target returned HTTP {response.status_code}",
                    code=code,
                    evidence=evidence,
                )
            if request.mode == "stream":
                output, tool_calls = _parse_sse(response.text)
            elif request.mode == "poll":
                output, tool_calls = await self._poll(request, response)
            else:
                output, tool_calls = _parse_json(response, request.response_path)
            evidence = _response_evidence(response)
        except TargetProductError:
            raise
        except (httpx.TimeoutException, httpx.NetworkError) as error:
            raise TransientError(str(error)) from error
        finally:
            if self._owns_client:
                await self._client.aclose()
        duration_ms = max(0, round((monotonic() - started) * 1000))
        attributes["http.response.status_code"] = response.status_code
        trace[0]["duration_ms"] = duration_ms
        return AgentResult(
            output=output,
            tool_calls=tool_calls,
            trace=trace,
            duration_ms=duration_ms,
            evidence=evidence,
        )

    async def _poll(
        self,
        request: AgentRequest,
        initial_response: httpx.Response,
    ) -> tuple[dict[str, object], list[dict[str, object]]]:
        payload = initial_response.json()
        status_url = payload.get(request.poll_url_field)
        if not isinstance(status_url, str):
            raise TargetProductError("Polling response did not include a status URL")
        while True:
            response = await self._client.get(
                status_url,
                headers=request.headers,
                timeout=request.timeout_seconds,
            )
            if response.status_code >= 400:
                raise TargetProductError(f"Target polling returned HTTP {response.status_code}")
            data = response.json()
            if data.get("status") in {"completed", "failed"}:
                if data.get("status") == "failed":
                    raise TargetProductError("Target asynchronous task failed")
                return _payload_output(data)
            import asyncio

            await asyncio.sleep(request.poll_interval_seconds)


def _parse_json(
    response: httpx.Response,
    response_path: str = "output",
) -> tuple[dict[str, object], list[dict[str, object]]]:
    try:
        payload = response.json()
    except json.JSONDecodeError as error:
        raise TargetProductError(
            "Target response was not valid JSON", code="target_protocol_error"
        ) from error
    if not isinstance(payload, dict):
        raise TargetProductError(
            "Target response must be a JSON object", code="target_protocol_error"
        )
    try:
        selected = _resolve_path(payload, response_path)
    except TargetProductError as error:
        raise TargetProductError(str(error), code="target_protocol_error") from error
    output = selected if isinstance(selected, dict) else {"value": selected}
    raw_calls = payload.get("tool_calls", [])
    tool_calls = list(raw_calls) if isinstance(raw_calls, list) else []
    return dict(output), [dict(call) for call in tool_calls if isinstance(call, dict)]


def _render_request(request: AgentRequest) -> dict[str, object]:
    template = request.request_template
    if template is None:
        return request.input
    context: dict[str, object] = {"input": request.input, "env": request.variables}
    rendered = _render_value(template, context)
    if not isinstance(rendered, dict):
        raise TargetProductError("Request template must render to a JSON object")
    return rendered


def _render_value(value: object, context: dict[str, object]) -> object:
    if isinstance(value, dict):
        return {str(key): _render_value(item, context) for key, item in value.items()}
    if isinstance(value, list):
        return [_render_value(item, context) for item in value]
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if stripped.startswith("{{") and stripped.endswith("}}"):
        expression = stripped[2:-2].strip()
        return _resolve_path(context, expression)
    return value


def _resolve_path(payload: object, path: str) -> object:
    current = payload
    for segment in path.split("."):
        if isinstance(current, dict) and segment in current:
            current = current[segment]
        elif isinstance(current, list) and segment.isdigit():
            index = int(segment)
            if index >= len(current):
                raise TargetProductError(f"Response path was not found: {path}")
            current = current[index]
        else:
            raise TargetProductError(f"Response path was not found: {path}")
    return current


def _error_details(response: httpx.Response) -> tuple[str, dict[str, object]]:
    try:
        payload = response.json()
    except json.JSONDecodeError:
        return "target_protocol_error", {}
    if not isinstance(payload, dict):
        return "target_protocol_error", {}
    raw_error = payload.get("error")
    error = raw_error if isinstance(raw_error, dict) else {}
    code = error.get("code")
    evidence = _target_evidence(payload.get("evidence"))
    return str(code or _status_error_code(response.status_code)), evidence


def _status_error_code(status_code: int) -> str:
    if status_code == 401:
        return "auth_expired"
    if status_code == 429:
        return "quota_exceeded"
    return "target_product_error"


def _response_evidence(response: httpx.Response) -> dict[str, object]:
    try:
        payload = response.json()
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    evidence = _target_evidence(payload.get("evidence"))
    signal = payload.get("security_signal")
    if signal in SECURITY_SIGNALS:
        evidence["security_signal"] = signal
    return evidence


def _target_evidence(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key): sanitized
        for key, item in value.items()
        if str(key) in TARGET_EVIDENCE_KEYS
        and (sanitized := _sanitize_evidence_value(item)) is not None
    }


def _sanitize_evidence_value(value: object) -> object | None:
    if isinstance(value, Mapping):
        return {
            str(key): sanitized
            for key, item in value.items()
            if _normalize_key(key) not in SENSITIVE_EVIDENCE_KEYS
            and (sanitized := _sanitize_evidence_value(item)) is not None
        }
    if isinstance(value, list | tuple):
        return [
            sanitized for item in value if (sanitized := _sanitize_evidence_value(item)) is not None
        ]
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return None


def _normalize_key(value: object) -> str:
    return str(value).strip().lower().replace("-", "_")


def _payload_output(
    payload: dict[str, object],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    raw_output = payload.get("output", payload)
    output = raw_output if isinstance(raw_output, dict) else {"value": raw_output}
    raw_calls = payload.get("tool_calls", [])
    tool_calls = list(raw_calls) if isinstance(raw_calls, list) else []
    return dict(output), [dict(call) for call in tool_calls if isinstance(call, dict)]


def _parse_sse(body: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    text_parts: list[str] = []
    tool_calls: list[dict[str, object]] = []
    for line in body.splitlines():
        if not line.startswith("data:"):
            continue
        raw = line.removeprefix("data:").strip()
        if not raw or raw == "[DONE]":
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as error:
            raise TargetProductError("Target SSE event was not valid JSON") from error
        if not isinstance(event, dict):
            continue
        if event.get("type") == "message.delta":
            text_parts.append(str(event.get("delta", "")))
        elif event.get("type") == "tool.call":
            tool_calls.append(event)
    return {"message": "".join(text_parts)}, tool_calls
