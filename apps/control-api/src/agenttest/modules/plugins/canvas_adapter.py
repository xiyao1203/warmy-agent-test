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

    def get_execution_order(self) -> list[UUID]:
        """返回基于拓扑排序的执行顺序（无向图 BFS）。"""
        adj: dict[UUID, set[UUID]] = {n.id: set() for n in self.nodes}
        for c in self.connections:
            adj[c.source_node_id].add(c.target_node_id)
            adj[c.target_node_id].add(c.source_node_id)
        visited: set[UUID] = set()
        order: list[UUID] = []
        for n in self.nodes:
            if n.id not in visited:
                queue = [n.id]
                visited.add(n.id)
                while queue:
                    cur = queue.pop(0)
                    order.append(cur)
                    for nb in adj[cur]:
                        if nb not in visited:
                            visited.add(nb)
                            queue.append(nb)
        return order

    def assert_creation_order(self, expected: list[UUID]) -> list[str]:
        """断言节点创建顺序。返回错误列表（空则通过）。"""
        errors: list[str] = []
        actual_ids = [n.id for n in self.nodes]
        for i, nid in enumerate(expected):
            if nid not in actual_ids:
                errors.append(f"expected node {nid} at position {i} not found")
            elif actual_ids.index(nid) != i:
                errors.append(f"node {nid} expected at {i}, actual {actual_ids.index(nid)}")
        return errors

    def assert_no_failed_nodes(self) -> list[str]:
        """断言无失败/错误节点。返回错误列表（空则通过）。"""
        errors: list[str] = []
        for n in self.nodes:
            if n.status in ("failed", "error"):
                errors.append(f"node {n.id} ({n.label}) is {n.status}")
        return errors

    def assert_required_io(self) -> list[str]:
        """断言所有节点都有必需的连线（输入或输出至少一个）。返回错误列表。"""
        errors: list[str] = []
        sources = {c.source_node_id for c in self.connections}
        targets = {c.target_node_id for c in self.connections}
        for n in self.nodes:
            has_output = n.id in sources
            has_input = n.id in targets
            if not has_output and not has_input and len(self.nodes) > 1:
                errors.append(f"node {n.id} ({n.label}) has no connections")
        return errors

    def assert_no_overlapping_nodes(self, threshold: float = 10.0) -> list[str]:
        """断言节点位置无重叠（基于阈值）。返回错误列表。"""
        errors: list[str] = []
        for i, a in enumerate(self.nodes):
            for b in self.nodes[i + 1:]:
                dx = abs(a.position.get("x", 0) - b.position.get("x", 0))
                dy = abs(a.position.get("y", 0) - b.position.get("y", 0))
                if dx < threshold and dy < threshold:
                    errors.append(f"nodes {a.id} and {b.id} overlap (dx={dx:.1f}, dy={dy:.1f})")
        return errors
