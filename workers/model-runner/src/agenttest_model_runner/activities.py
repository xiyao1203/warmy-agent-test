"""Model Runner Temporal Activities。"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
from temporalio import activity

from .adapter import OpenAICompatibleAdapter
from .contracts import ChatMessage, ModelInvocationRequest
from .credentials import decrypt_credential


class ModelActivities:
    """在 Activity 生命周期内解密并调用模型。"""

    def __init__(self, master_key: str) -> None:
        self._master_key = master_key
        self._adapter = OpenAICompatibleAdapter()

    @activity.defn(name="invoke-model")
    async def invoke_model(self, payload: dict[str, Any]) -> dict[str, Any]:
        """执行一次真实模型调用并只返回脱敏结果。"""

        api_key = decrypt_credential(self._master_key, str(payload["encrypted_api_key"]))
        request = ModelInvocationRequest(
            base_url=str(payload["base_url"]),
            model_name=str(payload["model_name"]),
            api_key=api_key,
            messages=[
                ChatMessage(
                    role=item["role"],
                    content=item.get("content"),
                    tool_calls=item.get("tool_calls"),
                    tool_call_id=item.get("tool_call_id"),
                    name=item.get("name"),
                )
                for item in payload["messages"]
            ],
            response_format=payload.get("response_format"),
            temperature=float(payload.get("temperature", 0)),
            timeout_seconds=float(payload.get("timeout_seconds", 60)),
            max_tokens=int(payload.get("max_tokens", 2048)),
            allow_private_network=bool(payload.get("allow_private_network", False)),
        )
        result = await self._adapter.invoke(request)
        return {
            "content": result.content,
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "total_tokens": result.total_tokens,
            "latency_ms": result.latency_ms,
            "response_id": result.response_id,
        }

    @activity.defn(name="stream-model")
    async def stream_model(self, payload: dict[str, Any]) -> dict[str, Any]:
        """逐块读取供应商 SSE，按 kind 分别路由到 content / reasoning 回调。

        支持优雅取消：
        - 检测 Temporal Activity heartbeat 取消状态
        - 被取消时返回已累积内容，不抛异常中断调用链
        - 接近超时时（剩余 < 5s）提前结束流式循环
        """

        api_key = decrypt_credential(self._master_key, str(payload["encrypted_api_key"]))
        request = ModelInvocationRequest(
            base_url=str(payload["base_url"]),
            model_name=str(payload["model_name"]),
            api_key=api_key,
            messages=[
                ChatMessage(
                    role=item["role"],
                    content=item.get("content"),
                    tool_calls=item.get("tool_calls"),
                    tool_call_id=item.get("tool_call_id"),
                    name=item.get("name"),
                )
                for item in payload["messages"]
            ],
            timeout_seconds=float(payload.get("timeout_seconds", 60)),
            max_tokens=int(payload.get("max_tokens", 2048)),
            allow_private_network=bool(payload.get("allow_private_network", False)),
        )
        callback = payload.get("callback")
        reasoning_callback = payload.get("reasoning_callback")
        timeout_seconds = float(payload.get("timeout_seconds", 60))
        started_at = time.monotonic()
        chunks: list[str] = []
        try:
            async for kind, chunk in self._adapter.stream(request):
                # Reasoning is streamed via callback, only accumulate content in return
                if kind == "content":
                    chunks.append(chunk)
                target = None
                if kind == "reasoning" and reasoning_callback:
                    target = reasoning_callback
                elif kind == "content" and callback:
                    target = callback
                if target:
                    async with httpx.AsyncClient(timeout=10) as client:
                        try:
                            response = await client.post(
                                str(target["url"]),
                                headers={"X-Internal-Token": str(target["internal_token"])},
                                json={"content": chunk},
                            )
                            response.raise_for_status()
                        except Exception:
                            pass
                activity.heartbeat({"chunks": len(chunks)})
                # 接近超时时提前结束流式循环，返回已累积内容
                elapsed = time.monotonic() - started_at
                if elapsed > timeout_seconds - 5:
                    activity.logger.warning(
                        "approaching timeout (elapsed=%.1fs, limit=%.1fs), ending stream early",
                        elapsed,
                        timeout_seconds,
                    )
                    break
        except asyncio.CancelledError:
            # 优雅取消：返回已累积内容，provider 连接由 async generator aclose 清理
            activity.logger.warning("stream-model cancelled, returning accumulated chunks")
        return {"content": "".join(chunks)}
