"""Model Runner Temporal Workflow。"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import CancelledError


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


@workflow.defn(name="model-streaming")
class ModelStreamingWorkflow:
    """可靠执行单轮流式模型调用，支持外部取消。

    取消信号来自 Control API 的 cancel_workflow() 调用，
    由 Temporal Server 传播到 Workflow → Activity。
    """

    @workflow.run
    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        timeout_seconds = int(payload.get("timeout_seconds", 60))
        activity_timeout = max(1, min(timeout_seconds + 15, 315))

        try:
            return await workflow.execute_activity(
                "stream-model",
                payload,
                start_to_close_timeout=timedelta(seconds=activity_timeout),
                heartbeat_timeout=timedelta(seconds=15),
                cancellation_type=workflow.ActivityCancellationType.WAIT_CANCELLATION_COMPLETED,
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    non_retryable_error_types=[
                        "ModelPermissionError",
                        "ModelProtocolError",
                        "ValueError",
                    ],
                ),
            )
        except CancelledError:
            # 用户取消：返回已累积内容而非抛异常
            return {"content": "", "cancelled": True}
