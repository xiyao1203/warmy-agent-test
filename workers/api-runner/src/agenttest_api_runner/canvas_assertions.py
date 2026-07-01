"""Canvas 画布断言引擎（Worker 内嵌）。

提供基于节点/连线结构的确定性断言能力：
- 节点类型、数量检查
- 连线存在性和方向检查
- 孤立节点检测
- Canvas JSON Schema 结构校验

不依赖 canvas-agent 插件，供 RunWorkflow browser 分支使用。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AssertionVerdict:
    """单条断言结果。"""

    passed: bool
    rule: str
    detail: str
    evidence: list[str] = field(default_factory=list)


@dataclass
class CanvasAssertionReport:
    """Canvas 断言汇总报告。"""

    results: list[AssertionVerdict]
    total: int
    passed: int
    failed: int
    score: float

    @classmethod
    def from_results(cls, results: list[AssertionVerdict]) -> CanvasAssertionReport:
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        score = passed / total if total > 0 else 1.0
        return cls(results=results, total=total, passed=passed, failed=failed, score=score)


def _ok(rule: str, detail: str = "") -> AssertionVerdict:
    return AssertionVerdict(passed=True, rule=rule, detail=detail)


def _fail(rule: str, detail: str, evidence: list[str] | None = None) -> AssertionVerdict:
    return AssertionVerdict(passed=False, rule=rule, detail=detail, evidence=evidence or [])


# ── 断言函数 ────────────────────────────────────────────────────────────────


def assert_node_count(
    nodes: list[dict[str, object]],
    *,
    min_count: int | None = None,
    max_count: int | None = None,
    exact_count: int | None = None,
) -> AssertionVerdict:
    """检查节点总数是否符合预期。"""
    actual = len(nodes)
    rule = "节点数量检查"
    if exact_count is not None:
        if actual != exact_count:
            return _fail(rule, f"期望 {exact_count} 个节点，实际 {actual} 个")
        return _ok(rule, f"恰好 {exact_count} 个节点")
    if min_count is not None and actual < min_count:
        return _fail(rule, f"至少需要 {min_count} 个节点，实际 {actual} 个")
    if max_count is not None and actual > max_count:
        return _fail(rule, f"最多允许 {max_count} 个节点，实际 {actual} 个")
    return _ok(rule, f"节点数 {actual} 在范围内")


def assert_node_types(
    nodes: list[dict[str, object]],
    *,
    required: list[str] | None = None,
) -> AssertionVerdict:
    """检查是否包含必需的节点类型。"""
    required = required or []
    actual_types = {str(n.get("node_type", "")) for n in nodes}
    missing = set(required) - actual_types
    if missing:
        return _fail(
            "必需节点类型检查",
            f"缺少节点类型: {', '.join(missing)}",
            [f"现有类型: {', '.join(actual_types)}"],
        )
    return _ok("必需节点类型检查", f"所有类型 {', '.join(required)} 都存在")


def assert_required_connection(
    connections: list[dict[str, object]],
    nodes: list[dict[str, object]],
    *,
    from_type: str,
    to_type: str,
) -> AssertionVerdict:
    """检查是否存在从类型 A 到类型 B 的连线。"""
    from_ids = {str(n["node_id"]) for n in nodes if str(n.get("node_type", "")) == from_type}
    to_ids = {str(n["node_id"]) for n in nodes if str(n.get("node_type", "")) == to_type}
    found = any(
        str(c.get("source_node_id", "")) in from_ids
        and str(c.get("target_node_id", "")) in to_ids
        for c in connections
    )
    rule = f"连线检查 ({from_type} -> {to_type})"
    if found:
        return _ok(rule)
    return _fail(rule, f"未找到 {from_type} -> {to_type} 的连线")


def assert_no_orphan_nodes(
    nodes: list[dict[str, object]],
    connections: list[dict[str, object]],
) -> AssertionVerdict:
    """检查是否存在孤立节点（无任何连线）。"""
    connected: set[str] = set()
    for c in connections:
        src = c.get("source_node_id")
        tgt = c.get("target_node_id")
        if src:
            connected.add(str(src))
        if tgt:
            connected.add(str(tgt))
    orphans = [str(n["node_id"]) for n in nodes if str(n.get("node_id", "")) not in connected]
    rule = "孤立节点检查"
    if orphans:
        return _fail(rule, f"发现 {len(orphans)} 个孤立节点", orphans[:5])
    return _ok(rule)


def assert_canvas_schema(
    nodes: list[dict[str, object]],
    connections: list[dict[str, object]],
) -> AssertionVerdict:
    """校验 Canvas 数据结构是否符合 JSON Schema。"""
    rule = "Canvas JSON Schema 校验"
    if not isinstance(nodes, list) or not isinstance(connections, list):
        return _fail(rule, "nodes 或 connections 不是数组类型")
    for i, n in enumerate(nodes):
        if not isinstance(n, dict):
            return _fail(rule, f"第 {i + 1} 个节点不是对象")
        if "node_id" not in n:
            return _fail(rule, f"第 {i + 1} 个节点缺少 node_id")
        if "node_type" not in n:
            return _fail(rule, f"第 {i + 1} 个节点缺少 node_type")
    for i, c in enumerate(connections):
        if not isinstance(c, dict):
            return _fail(rule, f"第 {i + 1} 条连线不是对象")
        if "source_node_id" not in c:
            return _fail(rule, f"第 {i + 1} 条连线缺少 source_node_id")
        if "target_node_id" not in c:
            return _fail(rule, f"第 {i + 1} 条连线缺少 target_node_id")
    return _ok(rule, "结构完全符合规范")


# ── 综合断言 ────────────────────────────────────────────────────────────────


def evaluate_canvas_assertions(
    nodes: list[dict[str, object]],
    connections: list[dict[str, object]],
    assertions: list[dict[str, object]],
) -> CanvasAssertionReport:
    """运行一组 canvas 断言并生成报告。

    assertions 中每项包含:
        type: 断言类型
        (canvas_schema / node_count / node_types / required_connection / no_orphan_nodes)
        以及对应的参数 (min_nodes / required_types / from_type / to_type 等)
    """
    results: list[AssertionVerdict] = []

    for a in assertions:
        kind = str(a.get("type", "")).lower()

        if kind == "canvas_schema":
            results.append(assert_canvas_schema(nodes, connections))

        elif kind == "node_count":
            min_v = a.get("min_count")
            max_v = a.get("max_count")
            exact_v = a.get("exact_count")
            results.append(
                assert_node_count(
                    nodes,
                    min_count=int(min_v) if isinstance(min_v, int | float) else None,
                    max_count=int(max_v) if isinstance(max_v, int | float) else None,
                    exact_count=int(exact_v) if isinstance(exact_v, int | float) else None,
                )
            )

        elif kind == "node_types":
            required_raw = a.get("required_types")
            if isinstance(required_raw, list):
                results.append(
                    assert_node_types(nodes, required=[str(t) for t in required_raw])
                )

        elif kind == "required_connection":
            from_t = str(a.get("from_type", ""))
            to_t = str(a.get("to_type", ""))
            if from_t and to_t:
                results.append(
                    assert_required_connection(connections, nodes, from_type=from_t, to_type=to_t)
                )

        elif kind == "no_orphan_nodes":
            results.append(assert_no_orphan_nodes(nodes, connections))

        else:
            results.append(_fail(f"未知断言类型: {kind}", f"类型 {kind} 不受支持"))

    return CanvasAssertionReport.from_results(results)
