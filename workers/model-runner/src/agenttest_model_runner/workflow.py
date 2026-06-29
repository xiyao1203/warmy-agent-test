"""Model Runner Temporal Workflow。"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn(name="model-invocation")
class ModelInvocationWorkflow:
    """为一次模型请求提供可靠重试和超时编排。"""

    @workflow.run
    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """调用无数据库访问的模型 Activity。"""

        timeout_seconds = max(1, min(int(payload.get("timeout_seconds", 60)) + 5, 305))
        return await workflow.execute_activity(
            "invoke-model",
            payload,
            start_to_close_timeout=timedelta(seconds=timeout_seconds),
            retry_policy=RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
                non_retryable_error_types=[
                    "ModelPermissionError",
                    "ModelProtocolError",
                    "ValueError",
                ],
            ),
        )
