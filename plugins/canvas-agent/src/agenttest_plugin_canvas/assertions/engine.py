"""画布结构断言引擎。

提供基于 CanvasTrace 的确定性断言能力：
- 节点类型、数量、属性检查
- 连线存在性和方向检查
- 孤立节点检测
- 强制连接规则验证
- Canvas JSON Schema 结构校验
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agenttest_plugin_canvas.adapter import (
    CanvasNodeType,
    CanvasTrace,
)


@dataclass
class AssertionResult:
    """单条断言结果。"""

    passed: bool
    rule: str
    detail: str
    evidence: list[str] = field(default_factory=list)

    @classmethod
    def ok(cls, rule: str, detail: str = "") -> AssertionResult:
        return cls(passed=True, rule=rule, detail=detail)

    @classmethod
    def fail(cls, rule: str, detail: str, evidence: list[str] | None = None) -> AssertionResult:
        return cls(passed=False, rule=rule, detail=detail, evidence=evidence or [])


@dataclass
class AssertionReport:
    """结构断言汇总报告。"""

    results: list[AssertionResult]
    total: int
    passed: int
    failed: int
    score: float

    @classmethod
    def from_results(cls, results: list[AssertionResult]) -> AssertionReport:
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        score = passed / total if total > 0 else 1.0
        return cls(results=results, total=total, passed=passed, failed=failed, score=score)


# ── 断言函数 ────────────────────────────────────────────────────────────────


def assert_node_count(
    trace: CanvasTrace,
    *,
    min_count: int | None = None,
    max_count: int | None = None,
    exact_count: int | None = None,
) -> AssertionResult:
    """检查画布中节点总数是否符合预期。"""
    actual = len(trace.nodes)
    rule = "节点数量检查"
    if exact_count is not None:
        if actual != exact_count:
            return AssertionResult.fail(rule, f"期望 {exact_count} 个节点，实际 {actual} 个")
        return AssertionResult.ok(rule, f"恰好 {exact_count} 个节点")
    if min_count is not None and actual < min_count:
        return AssertionResult.fail(rule, f"至少需要 {min_count} 个节点，实际 {actual} 个")
    if max_count is not None and actual > max_count:
        return AssertionResult.fail(rule, f"最多允许 {max_count} 个节点，实际 {actual} 个")
    return AssertionResult.ok(rule, f"节点数 {actual} 在范围内")


def assert_node_types(
    trace: CanvasTrace,
    *,
    required: list[CanvasNodeType] | None = None,
) -> AssertionResult:
    """检查是否包含必需的节点类型。"""
    required = required or []
    actual_types = {n.node_type for n in trace.nodes}
    missing = set(required) - actual_types
    if missing:
        return AssertionResult.fail(
            "必需节点类型检查",
            f"缺少节点类型: {', '.join(m.value for m in missing)}",
            [f"现有类型: {', '.join(t.value for t in actual_types)}"],
        )
    return AssertionResult.ok(
        "必需节点类型检查",
        f"所有类型 {', '.join(t.value for t in required)} 都存在",
    )


def assert_node_has_property(
    trace: CanvasTrace,
    *,
    node_type: CanvasNodeType | None = None,
    property_name: str,
    property_value: object | None = None,
) -> AssertionResult:
    """检查指定类型的节点是否具有某个属性。"""
    targets = [n for n in trace.nodes if node_type is None or n.node_type == node_type]
    errors: list[str] = []
    for node in targets:
        val = node.properties.get(property_name)
        if property_value is not None and val != property_value:
            errors.append(f"节点 {node.node_id}: {property_name}={val}, 期望={property_value}")
        elif val is None:
            errors.append(f"节点 {node.node_id}: 缺少属性 {property_name}")
    if errors:
        return AssertionResult.fail(
            f"节点属性检查 ({property_name})",
            f"{len(errors)} 个节点不满足",
            errors[:5],
        )
    return AssertionResult.ok(f"节点属性检查 ({property_name})")


def assert_connection_count(
    trace: CanvasTrace,
    *,
    min_count: int | None = None,
    exact_count: int | None = None,
) -> AssertionResult:
    """检查连线数量。"""
    actual = len(trace.connections)
    rule = "连线数量检查"
    if exact_count is not None:
        if actual != exact_count:
            return AssertionResult.fail(rule, f"期望 {exact_count} 条连线，实际 {actual} 条")
        return AssertionResult.ok(rule, f"恰好 {exact_count} 条连线")
    if min_count is not None and actual < min_count:
        return AssertionResult.fail(rule, f"至少需要 {min_count} 条连线，实际 {actual} 条")
    return AssertionResult.ok(rule)


def assert_required_connection(
    trace: CanvasTrace,
    *,
    from_type: CanvasNodeType,
    to_type: CanvasNodeType,
) -> AssertionResult:
    """检查是否存在从类型 A 到类型 B 的连线。"""
    from_nodes = {n.node_id for n in trace.nodes if n.node_type == from_type}
    to_nodes = {n.node_id for n in trace.nodes if n.node_type == to_type}
    found = any(
        c.source_node_id in from_nodes and c.target_node_id in to_nodes
        for c in trace.connections
    )
    rule = f"连线检查 ({from_type.value} → {to_type.value})"
    if found:
        return AssertionResult.ok(rule)
    return AssertionResult.fail(rule, f"未找到 {from_type.value} → {to_type.value} 的连线")


def assert_no_orphan_nodes(trace: CanvasTrace) -> AssertionResult:
    """检查是否存在孤立节点（无任何连线）。"""
    connected = set()
    for c in trace.connections:
        connected.add(c.source_node_id)
        connected.add(c.target_node_id)
    orphans = [n.node_id for n in trace.nodes if n.node_id not in connected]
    rule = "孤立节点检查"
    if orphans:
        return AssertionResult.fail(rule, f"发现 {len(orphans)} 个孤立节点", orphans[:5])
    return AssertionResult.ok(rule)


# ── 综合断言函数 ────────────────────────────────────────────────────────────

CANVAS_SCHEMA = {
    "type": "object",
    "required": ["nodes", "connections"],
    "properties": {
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["node_id", "node_type"],
                "properties": {
                    "node_id": {"type": "string"},
                    "node_type": {"type": "string"},
                    "label": {"type": "string"},
                    "properties": {"type": "object"},
                },
            },
        },
        "connections": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["source_node_id", "target_node_id", "connection_type"],
                "properties": {
                    "source_node_id": {"type": "string"},
                    "target_node_id": {"type": "string"},
                    "connection_type": {"type": "string"},
                    "properties": {"type": "object"},
                },
            },
        },
    },
}


def assert_canvas_schema(trace: CanvasTrace) -> AssertionResult:
    """校验 CanvasTrace 数据结构是否符合 JSON Schema。"""
    import jsonschema

    raw = {
        "nodes": [
            {
                "node_id": n.node_id,
                "node_type": n.node_type.value,
                "label": n.label,
                "properties": n.properties,
            }
            for n in trace.nodes
        ],
        "connections": [
            {
                "source_node_id": c.source_node_id,
                "target_node_id": c.target_node_id,
                "connection_type": c.connection_type.value,
                "properties": c.properties,
            }
            for c in trace.connections
        ],
    }
    try:
        jsonschema.validate(raw, CANVAS_SCHEMA)
    except jsonschema.ValidationError as exc:
        return AssertionResult.fail(
            "Canvas JSON Schema 校验",
            f"数据结构不符合规范: {exc.message}",
            [str(exc.path) if exc.path else "根层级"],
        )
    return AssertionResult.ok("Canvas JSON Schema 校验", "结构完全符合规范")


def run_all_assertions(
    trace: CanvasTrace,
    *,
    min_nodes: int | None = None,
    required_types: list[CanvasNodeType] | None = None,
    required_connections: list[tuple[CanvasNodeType, CanvasNodeType]] | None = None,
) -> AssertionReport:
    """运行一组标准断言并生成报告。"""
    results: list[AssertionResult] = []

    if min_nodes is not None:
        results.append(assert_node_count(trace, min_count=min_nodes))

    if required_types:
        results.append(assert_node_types(trace, required=required_types))

    for from_t, to_t in (required_connections or []):
        results.append(assert_required_connection(trace, from_type=from_t, to_type=to_t))

    results.append(assert_no_orphan_nodes(trace))

    results.append(assert_canvas_schema(trace))

    return AssertionReport.from_results(results)
