from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

import httpx

from agenttest.modules.agents.domain.value_objects import AgentConfig
from agenttest.modules.security.public import validate_agent_endpoint


@dataclass(frozen=True, slots=True)
class ConnectionValidationResult:
    status_code: int
    latency_ms: int
    response_preview: object


class HttpAgentConnectionValidator:
    def __init__(self, *, allow_private_network: bool = False) -> None:
        self._allow_private_network = allow_private_network

    async def validate(
        self,
        config: AgentConfig,
        probe_input: dict[str, object],
    ) -> ConnectionValidationResult:
        if config.credential_binding_ids:
            raise ValueError("请通过环境凭证绑定执行带认证的连接测试")
        validate_agent_endpoint(config.api_url, allow_private_network=self._allow_private_network)
        payload = _render(config.request_template, probe_input)
        started = monotonic()
        async with httpx.AsyncClient() as client:
            response = await client.post(config.api_url, json=payload, timeout=config.timeout)
        response.raise_for_status()
        try:
            preview: object = response.json()
        except ValueError:
            preview = response.text[:1000]
        return ConnectionValidationResult(
            status_code=response.status_code,
            latency_ms=round((monotonic() - started) * 1000),
            response_preview=preview,
        )


def _render(template: dict[str, object], probe_input: dict[str, object]) -> dict[str, object]:
    if template == {"input": "{{ input }}"}:
        return {"input": probe_input}
    return {
        key: probe_input if value == "{{ input }}" else value for key, value in template.items()
    }
