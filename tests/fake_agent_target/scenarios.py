from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCENARIOS = {
    "success",
    "stream_success",
    "product_error",
    "protocol_error",
    "auth_expired",
    "quota_exceeded",
    "timeout",
    "transient_failure",
    "incomplete_artifact",
    "prompt_injection",
    "data_leak_attempt",
    "privilege_escalation",
}


@dataclass(frozen=True, slots=True)
class ScenarioResponse:
    status_code: int
    payload: dict[str, Any]


def scenario_response(
    *, scenario: str, request_id: str, attempt: int, input_text: str, transient_failure: bool
) -> ScenarioResponse:
    evidence = {
        "scenario": scenario,
        "request_id": request_id,
        "attempt": attempt,
        "tool_calls": [{"name": "echo", "status": "completed"}],
        "artifacts": [{"type": "text", "name": "response.txt", "size": len(input_text)}],
    }
    if scenario == "transient_failure" and transient_failure:
        return _error(503, "target_temporarily_unavailable", evidence)
    errors = {
        "product_error": (422, "target_product_error"),
        "auth_expired": (401, "auth_expired"),
        "quota_exceeded": (429, "quota_exceeded"),
    }
    if scenario in errors:
        status, code = errors[scenario]
        return _error(status, code, evidence)
    if scenario == "protocol_error":
        return ScenarioResponse(200, {"unexpected": True, "evidence": evidence})
    if scenario == "timeout":
        return _error(504, "target_timeout", evidence)
    if scenario == "incomplete_artifact":
        evidence["artifacts"] = []
        return ScenarioResponse(200, {"output": "incomplete", "evidence": evidence})
    if scenario == "prompt_injection":
        return ScenarioResponse(
            200,
            {
                "output": "Ignored untrusted instruction",
                "security_signal": "prompt_injection",
                "evidence": evidence,
            },
        )
    if scenario == "data_leak_attempt":
        return ScenarioResponse(
            200,
            {
                "output": "Synthetic marker blocked",
                "security_signal": "data_leak_attempt",
                "evidence": evidence,
            },
        )
    if scenario == "privilege_escalation":
        return ScenarioResponse(
            200,
            {
                "output": "Privileged action denied",
                "security_signal": "privilege_escalation",
                "evidence": evidence,
            },
        )
    return ScenarioResponse(200, {"output": f"Echo: {input_text}", "evidence": evidence})


def _error(status: int, code: str, evidence: dict[str, Any]) -> ScenarioResponse:
    return ScenarioResponse(status, {"error": {"code": code}, "evidence": evidence})
