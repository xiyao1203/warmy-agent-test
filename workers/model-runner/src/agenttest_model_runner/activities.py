"""Model Runner Temporal Activities。"""

from __future__ import annotations

from typing import Any

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
                ChatMessage(role=item["role"], content=item["content"])
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
