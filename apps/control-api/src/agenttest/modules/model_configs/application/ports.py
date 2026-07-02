"""模型调用应用端口。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..domain.entities import ModelConfiguration


@dataclass(frozen=True, slots=True)
class InvocationMessage:
    """与供应商无关的模型消息（支持 tool calling 透传）。"""

    role: str
    content: str | list[dict[str, object]] | None
    tool_calls: list[dict[str, object]] | None = None
    tool_call_id: str | None = None
    name: str | None = None


@dataclass(frozen=True, slots=True)
class InvocationResult:
    """脱敏后的模型调用结果。"""

    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    response_id: str | None = None


@dataclass(frozen=True, slots=True)
class ModelStreamCallback:
    """Model Runner 可访问的受保护增量回调。"""

    url: str
    internal_token: str


class ModelInvoker(Protocol):
    """Control API 发起独立 Worker 模型调用的端口。"""

    async def invoke(
        self,
        config: ModelConfiguration,
        messages: list[InvocationMessage],
        *,
        response_format: dict[str, str] | None = None,
        timeout_seconds: int = 60,
        max_tokens: int = 2048,
    ) -> InvocationResult: ...

    async def stream(
        self,
        config: ModelConfiguration,
        messages: list[InvocationMessage],
        *,
        callback: ModelStreamCallback | None = None,
        timeout_seconds: int = 60,
        max_tokens: int = 2048,
    ) -> InvocationResult: ...


class ModelRuntimeUnavailableError(Exception):
    """部署尚未配置或无法连接 Model Runner。"""
