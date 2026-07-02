"""Model Runner 的稳定调用契约。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """OpenAI-Compatible 对话消息（支持 tool calling）。"""

    role: str
    content: str | list[dict[str, Any]] | None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None


@dataclass(frozen=True, slots=True)
class ModelInvocationRequest:
    """Worker 执行一次模型调用所需的最小明文请求。"""

    base_url: str
    model_name: str
    api_key: str
    messages: list[ChatMessage]
    response_format: dict[str, str] | None = None
    temperature: float = 0
    timeout_seconds: float = 60
    max_tokens: int = 2048
    allow_private_network: bool = False


@dataclass(frozen=True, slots=True)
class ModelInvocationResult:
    """脱敏后的模型调用结果。"""

    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    response_id: str | None = None
