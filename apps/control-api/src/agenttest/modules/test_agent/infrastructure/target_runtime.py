"""通过 API Runner 调用真实被测 Agent。"""

from __future__ import annotations

from uuid import uuid4

from temporalio.client import Client

from agenttest.modules.test_agent.application.target_chat import TargetInvocationResult


class TemporalTargetAgentRuntime:
    def __init__(self, *, address: str | None, namespace: str, task_queue: str) -> None:
        self._address = address
        self._namespace = namespace
        self._task_queue = task_queue

    async def invoke(
        self,
        *,
        url: str,
        mode: str,
        headers: dict[str, str],
        input: dict[str, object],
        timeout_seconds: int,
    ) -> TargetInvocationResult:
        if not self._address:
            raise RuntimeError("部署未配置 API Runner")
        client = await Client.connect(self._address, namespace=self._namespace)
        result = await client.execute_workflow(
            "target-agent-chat",
            {
                "url": url,
                "mode": mode,
                "headers": headers,
                "input": input,
                "timeout_seconds": timeout_seconds,
            },
            id=f"target-agent-chat-{uuid4()}",
            task_queue=self._task_queue,
        )
        if not isinstance(result, dict) or not isinstance(result.get("output"), dict):
            raise RuntimeError("API Runner 返回无效结果")
        return TargetInvocationResult(
            output=dict(result["output"]),
            trace=list(result.get("trace", [])),
            duration_ms=int(result.get("duration_ms", 0)),
            token_usage=(
                dict(result["token_usage"]) if isinstance(result.get("token_usage"), dict) else None
            ),
        )
