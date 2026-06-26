"""画布 Agent 插件 — CanvasAdapter 核心实现。

对接画布 Agent API，负责：
- 启动画布任务并轮询执行状态
- 采集画布节点、连线、属性和执行日志
- 提取生成产物（图片、视频 URL）
- 输出规范化 CanvasTrace 供断言引擎评分
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol
from uuid import UUID

# ── 画布数据模型 ────────────────────────────────────────────────────────────


class CanvasNodeType(StrEnum):
    """画布节点类型枚举。"""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    PROMPT = "prompt"
    OUTPUT = "output"
    GROUP = "group"


class CanvasConnectionType(StrEnum):
    """画布连线类型。"""

    DATA_FLOW = "data_flow"
    CONTROL_FLOW = "control_flow"
    REFERENCE = "reference"


@dataclass
class CanvasNode:
    """画布节点快照。"""

    node_id: str
    node_type: CanvasNodeType
    label: str
    x: float
    y: float
    width: float = 200
    height: float = 120
    properties: dict[str, object] = field(default_factory=dict)
    status: str = "idle"
    error: str | None = None


@dataclass
class CanvasConnection:
    """节点连线快照。"""

    connection_id: str
    source_node_id: str
    target_node_id: str
    connection_type: CanvasConnectionType
    properties: dict[str, object] = field(default_factory=dict)


@dataclass
class CanvasTrace:
    """画布执行 Trace，包含完整快照。"""

    run_id: UUID
    agent_id: UUID
    nodes: list[CanvasNode]
    connections: list[CanvasConnection]
    artifacts: list[dict[str, object]] = field(default_factory=list)
    execution_log: list[dict[str, object]] = field(default_factory=list)
    total_duration_ms: int = 0
    error: str | None = None


# ── 插件协议接口 ────────────────────────────────────────────────────────────


class CanvasAgentAdapter(Protocol):
    """画布 Agent 适配器协议。

    实现者负责与具体画布 Agent API 通信，采集画布状态。
    不依赖控制面内部模块。
    """

    async def start(
        self, *, prompt: str, template: dict[str, object] | None = None
    ) -> str:
        """启动画布任务，返回任务 ID。"""
        ...

    async def poll(self, task_id: str) -> CanvasTrace | None:
        """轮询画布任务状态。返回 None 表示仍在执行中。"""
        ...

    async def cancel(self, task_id: str) -> None:
        """取消画布任务。"""
        ...


class CanvasArtifactAdapter(Protocol):
    """画布产物适配器协议。

    负责提取和规范化画布生成的图片、视频等产物。
    """

    async def collect(self, trace: CanvasTrace) -> list[dict[str, object]]:
        """从 Trace 中提取产物描述符。"""
        ...
