"""Canvas Agent Adapter - 画布操作 API。

实现画布节点创建、连线、执行等操作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class CanvasNode:
    """画布节点。"""
    id: UUID
    node_type: str
    label: str
    position: dict[str, float]
    config: dict[str, object] = field(default_factory=dict)
    status: str = "idle"


@dataclass(frozen=True, slots=True)
class CanvasConnection:
    """画布连线。"""
    id: UUID
    source_node_id: UUID
    target_node_id: UUID
    label: str | None = None


@dataclass(slots=True)
class CanvasState:
    """画布状态。"""
    nodes: list[CanvasNode] = field(default_factory=list)
    connections: list[CanvasConnection] = field(default_factory=list)

    def add_node(
        self,
        node_type: str,
        label: str,
        position: dict[str, float],
        config: dict[str, object] | None = None,
    ) -> CanvasNode:
        node = CanvasNode(
            id=uuid4(),
            node_type=node_type,
            label=label,
            position=position,
            config=config or {},
        )
        self.nodes.append(node)
        return node

    def connect(
        self,
        source_id: UUID,
        target_id: UUID,
        label: str | None = None,
    ) -> CanvasConnection:
        conn = CanvasConnection(
            id=uuid4(),
            source_node_id=source_id,
            target_node_id=target_id,
            label=label,
        )
        self.connections.append(conn)
        return conn

    def get_node(self, node_id: UUID) -> CanvasNode | None:
        for n in self.nodes:
            if n.id == node_id:
                return n
        return None

    def execute_node(self, node_id: UUID) -> None:
        """标记节点为执行中。"""
        node = self.get_node(node_id)
        if node is None:
            raise ValueError(f"Node {node_id} not found")
        node.status = "running"  # type: ignore[misc]

    def complete_node(self, node_id: UUID) -> None:
        """标记节点为完成。"""
        node = self.get_node(node_id)
        if node is None:
            raise ValueError(f"Node {node_id} not found")
        node.status = "completed"  # type: ignore[misc]
