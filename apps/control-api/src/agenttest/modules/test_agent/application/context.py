"""PydanticAI 运行时上下文模型。

提供 `OrchestrationContext` 作为所有 SubAgent 和 SuperAgent 的 `deps_type`，
将 actor、project_id、session_id、平台网关、确认处理器和流式回调
注入到每一次 Agent 运行中。
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from uuid import UUID


@dataclass
class OrchestrationContext:
    """PydanticAI Agent 运行时依赖容器。

    由 Control API 在收到用户消息时构建，随每次 `agent.run(deps=ctx)` 注入。
    """

    actor: object
    """当前用户（User）。"""
    project_id: UUID
    """目标项目 ID。"""
    session_id: UUID
    """会话 ID，用于事件追溯。"""
    platform_gateway: object
    """PlatformGateway 实例，提供对 28 个平台能力的统一调用。"""
    confirmation_handler: object | None = None
    """ConfirmationHandler 实例，驱动 READ/DRAFT_WRITE/HIGH_IMPACT 三级确认。"""
    generation_id: UUID | None = None
    """当前流式生成 ID，用于把工具事件关联到同一轮回复。"""
    stream_callback: Callable[[str, object], Awaitable[object]] | None = None
    """SSE 流式增量回调，签名为 async def(event_type, payload)。"""
