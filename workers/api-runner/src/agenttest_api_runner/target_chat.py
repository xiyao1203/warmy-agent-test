"""被测 Agent 单轮真实调用的 Temporal 契约。"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import activity, workflow
from temporalio.common import RetryPolicy


@activity.defn(name="execute-target-chat")
async def execute_target_chat(payload: dict[str, Any]) -> dict[str, Any]:
    from .adapter import AgentRequest, GenericHttpAgentAdapter

    activity.heartbeat({"phase": "invoke"})
    result = await GenericHttpAgentAdapter().execute(
        AgentRequest(
            url=str(payload["url"]),
            mode=str(payload.get("mode", "sync")),  # type: ignore[arg-type]
            headers={str(key): str(value) for key, value in payload.get("headers", {}).items()},
            input=dict(payload["input"]),
            timeout_seconds=float(payload.get("timeout_seconds", 30)),
        )
    )
    return {
        "output": result.output,
        "trace": result.trace,
        "duration_ms": result.duration_ms,
        "token_usage": None,
    }


@workflow.defn(name="target-agent-chat")
class TargetAgentChatWorkflow:
    @workflow.run
    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        timeout = max(1, min(int(payload.get("timeout_seconds", 30)) + 5, 305))
        return await workflow.execute_activity(
            "execute-target-chat",
            payload,
            start_to_close_timeout=timedelta(seconds=timeout),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )
