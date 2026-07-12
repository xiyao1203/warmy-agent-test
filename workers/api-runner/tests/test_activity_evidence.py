from __future__ import annotations

import pytest
from agenttest_api_runner import activities
from agenttest_api_runner.adapter import AgentResult, TargetProductError, TransientError
from agenttest_api_runner.contracts import RunCaseTask


class Adapter:
    async def execute(self, _request):
        return AgentResult(
            output={"message": "blocked"},
            tool_calls=[],
            trace=[{"name": "http.request"}],
            duration_ms=10,
            evidence={
                "artifacts": [],
                "scenario": "prompt_injection",
                "security_signal": "prompt_injection",
            },
        )


class FailingAdapter:
    def __init__(self, error: Exception) -> None:
        self.error = error

    async def execute(self, _request):
        raise self.error


def task() -> RunCaseTask:
    return RunCaseTask("case-1", {"message": "hello"}, [])


@pytest.mark.asyncio
async def test_activity_normalizes_target_evidence_and_security_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(activities.activity, "heartbeat", lambda _value: None)
    monkeypatch.setattr(activities, "GenericHttpAgentAdapter", lambda: Adapter())

    result = await activities.execute_agent_case(
        task(), {"endpoint_url": "https://agent.example/run"}
    )

    assert result.status == "passed"
    assert result.evidence["execution_outcome"] == "success"
    assert result.evidence["quality_decision"] == "pass"
    assert result.evidence["security_decision"] == "blocked"
    assert result.evidence["target"]["scenario"] == "prompt_injection"


@pytest.mark.asyncio
async def test_activity_returns_stable_deterministic_target_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(activities.activity, "heartbeat", lambda _value: None)
    monkeypatch.setattr(
        activities,
        "GenericHttpAgentAdapter",
        lambda: FailingAdapter(
            TargetProductError(
                "Target returned HTTP 401",
                code="auth_expired",
                evidence={"scenario": "auth_expired"},
            )
        ),
    )

    result = await activities.execute_agent_case(
        task(), {"endpoint_url": "https://agent.example/run"}
    )

    assert result.status == "error"
    assert result.error_type == "auth_expired"
    assert result.evidence["target"] == {"scenario": "auth_expired"}


@pytest.mark.asyncio
async def test_activity_leaves_transient_failure_for_temporal_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(activities.activity, "heartbeat", lambda _value: None)
    monkeypatch.setattr(
        activities,
        "GenericHttpAgentAdapter",
        lambda: FailingAdapter(TransientError("temporary")),
    )

    with pytest.raises(TransientError):
        await activities.execute_agent_case(task(), {"endpoint_url": "https://agent.example/run"})
