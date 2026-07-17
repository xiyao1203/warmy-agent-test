"""Agent 调用协议领域枚举。"""

from __future__ import annotations

from enum import StrEnum


class InvocationProtocol(StrEnum):
    SYNC_JSON = "sync_json"
    OPENAI_CHAT = "openai_chat"
    SSE = "sse"
    ASYNC_POLL = "async_poll"
