from __future__ import annotations

import json
from dataclasses import dataclass, field
from time import monotonic
from typing import Literal

import httpx

SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key", "api-key"}


class TargetProductError(Exception):
    """待测 Agent 返回确定性业务错误。"""


class TransientError(Exception):
    """网络或临时依赖错误，可由 Temporal 重试。"""


@dataclass(frozen=True, slots=True)
class AgentRequest:
    url: str
    input: dict[str, object]
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


class GenericHttpAgentAdapter:
    def __init__(self, *, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient()
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
                json=request.input,
                headers=request.headers,
                timeout=request.timeout_seconds,
            )
            if response.status_code >= 400:
                raise TargetProductError(
                    f"Target returned HTTP {response.status_code}"
                )
            if request.mode == "stream":
                output, tool_calls = _parse_sse(response.text)
            elif request.mode == "poll":
                output, tool_calls = await self._poll(request, response)
            else:
                output, tool_calls = _parse_json(response)
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
                raise TargetProductError(
                    f"Target polling returned HTTP {response.status_code}"
                )
            data = response.json()
            if data.get("status") in {"completed", "failed"}:
                if data.get("status") == "failed":
                    raise TargetProductError("Target asynchronous task failed")
                return _payload_output(data)
            import asyncio

            await asyncio.sleep(request.poll_interval_seconds)


def _parse_json(response: httpx.Response) -> tuple[dict[str, object], list[dict[str, object]]]:
    try:
        payload = response.json()
    except json.JSONDecodeError as error:
        raise TargetProductError("Target response was not valid JSON") from error
    if not isinstance(payload, dict):
        raise TargetProductError("Target response must be a JSON object")
    return _payload_output(payload)


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
