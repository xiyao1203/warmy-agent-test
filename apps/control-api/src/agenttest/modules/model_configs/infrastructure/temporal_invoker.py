"""通过 Temporal 调用独立 Model Runner。"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from temporalio.client import Client

from ..application.ports import (
    InvocationMessage,
    InvocationResult,
    ModelRuntimeUnavailableError,
    ModelStreamCallback,
    StreamContext,
)
from ..domain.entities import ModelConfiguration


class TemporalModelInvoker:
    """把加密配置快照发送到 Model Runner 任务队列。"""

    def __init__(
        self,
        *,
        address: str | None,
        namespace: str,
        task_queue: str,
        allow_private_network: bool = False,
    ) -> None:
        self._address = address
        self._namespace = namespace
        self._task_queue = task_queue
        self._allow_private_network = allow_private_network

    @staticmethod
    def _serialize_messages(messages: list[InvocationMessage]) -> list[dict[str, Any]]:
        """序列化消息列表（含 tool_calls / tool_call_id 透传）。"""
        result: list[dict[str, Any]] = []
        for item in messages:
            msg: dict[str, Any] = {"role": item.role}
            if item.content is not None:
                msg["content"] = item.content
            if item.tool_calls is not None:
                msg["tool_calls"] = item.tool_calls
            if item.tool_call_id is not None:
                msg["tool_call_id"] = item.tool_call_id
            if item.name is not None:
                msg["name"] = item.name
            result.append(msg)
        return result

    async def invoke(
        self,
        config: ModelConfiguration,
        messages: list[InvocationMessage],
        *,
        response_format: dict[str, str] | None = None,
        timeout_seconds: int = 60,
        max_tokens: int = 2048,
    ) -> InvocationResult:
        """等待一次真实模型 Workflow 完成并返回脱敏结果。"""

        if not self._address:
            raise ModelRuntimeUnavailableError("部署未配置 Model Runner")
        payload: dict[str, Any] = {
            "project_id": str(config.project_id.value),
            "model_config_id": str(config.model_config_id.value),
            "provider_type": config.provider_type.value,
            "base_url": config.base_url,
            "model_name": config.model_name,
            "encrypted_api_key": config.encrypted_api_key,
            "messages": self._serialize_messages(messages),
            "response_format": response_format,
            "timeout_seconds": timeout_seconds,
            "max_tokens": max_tokens,
            "allow_private_network": self._allow_private_network,
        }
        try:
            client = await Client.connect(self._address, namespace=self._namespace)
            result = await client.execute_workflow(
                "model-invocation",
                payload,
                id=f"model-invocation-{uuid4()}",
                task_queue=self._task_queue,
            )
        except Exception as error:
            # 只暴露稳定平台错误，避免 Temporal 或上游异常夹带凭证。
            raise ModelRuntimeUnavailableError("Model Runner 调用失败") from error
        if not isinstance(result, dict) or not isinstance(result.get("content"), str):
            raise ModelRuntimeUnavailableError("Model Runner 返回无效结果")
        return InvocationResult(
            content=result["content"],
            prompt_tokens=int(result.get("prompt_tokens", 0)),
            completion_tokens=int(result.get("completion_tokens", 0)),
            total_tokens=int(result.get("total_tokens", 0)),
            latency_ms=int(result.get("latency_ms", 0)),
            response_id=result.get("response_id"),
        )

    async def stream(
        self,
        config: ModelConfiguration,
        messages: list[InvocationMessage],
        *,
        callback: ModelStreamCallback,
        timeout_seconds: int = 60,
        max_tokens: int = 2048,
        stream_ctx: StreamContext | None = None,
    ) -> InvocationResult:
        """执行真实流式 Workflow；每个供应商增量由 Worker 持久回调。

        使用 start_workflow 获取 WorkflowHandle 以便外部取消。
        若提供 stream_ctx，会填充 workflow_id 供调用方取消。
        """

        if not self._address:
            raise ModelRuntimeUnavailableError("部署未配置 Model Runner")
        payload: dict[str, Any] = {
            "project_id": str(config.project_id.value),
            "model_config_id": str(config.model_config_id.value),
            "base_url": config.base_url,
            "model_name": config.model_name,
            "encrypted_api_key": config.encrypted_api_key,
            "messages": self._serialize_messages(messages),
            "timeout_seconds": timeout_seconds,
            "max_tokens": max_tokens,
            "allow_private_network": self._allow_private_network,
        }
        if callback is not None:
            payload["callback"] = {"url": callback.url, "internal_token": callback.internal_token}

        workflow_id = f"model-streaming-{uuid4()}"
        if stream_ctx is not None:
            stream_ctx.workflow_id = workflow_id

        try:
            client = await Client.connect(self._address, namespace=self._namespace)
            handle = await client.start_workflow(
                "model-streaming",
                payload,
                id=workflow_id,
                task_queue=self._task_queue,
            )
            result = await handle.result()
        except Exception as error:
            raise ModelRuntimeUnavailableError("Model Runner 流式调用失败") from error
        finally:
            if stream_ctx is not None:
                stream_ctx.workflow_id = None

        if not isinstance(result, dict) or not isinstance(result.get("content"), str):
            raise ModelRuntimeUnavailableError("Model Runner 返回无效流式结果")
        return InvocationResult(content=result["content"])

    async def cancel_workflow(self, workflow_id: str) -> None:
        """取消正在运行的 Temporal 流式 Workflow。

        向 Temporal Server 发送取消信号，触发 Workflow 的取消处理逻辑。
        若 workflow 已完成或不存在，忽略错误静默返回。
        """
        if not self._address or not workflow_id:
            return
        try:
            client = await Client.connect(self._address, namespace=self._namespace)
            handle = client.get_workflow_handle(workflow_id)
            await handle.cancel()
        except Exception:
            pass
