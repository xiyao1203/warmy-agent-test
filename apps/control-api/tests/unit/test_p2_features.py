"""P2 功能测试。"""

from __future__ import annotations

import pytest

from agenttest.modules.plugins.canvas_adapter import CanvasState
from agenttest.modules.plugins.network_mock import NetworkMockManager
from agenttest.modules.security.adapters.future_adapters import (
    AgentDojoScanner,
    GarakScanner,
    PyRITScanner,
)


@pytest.mark.asyncio
async def test_garak_scanner_returns_empty():
    scanner = GarakScanner()
    result = await scanner.run_scan()
    assert result == []


@pytest.mark.asyncio
async def test_pyrit_scanner_returns_empty():
    scanner = PyRITScanner()
    result = await scanner.run_scan()
    assert result == []


@pytest.mark.asyncio
async def test_agentdojo_scanner_returns_empty():
    scanner = AgentDojoScanner()
    result = await scanner.run_scan()
    assert result == []


def test_canvas_creation_order_assertion():
    cs = CanvasState()
    n1 = cs.add_node("start", "Start", {"x": 0, "y": 0})
    n2 = cs.add_node("end", "End", {"x": 100, "y": 100})
    cs.connect(n1.id, n2.id)
    errors = cs.assert_creation_order([n1.id, n2.id])
    assert errors == []


def test_canvas_creation_order_wrong():
    cs = CanvasState()
    n1 = cs.add_node("start", "Start", {"x": 0, "y": 0})
    n2 = cs.add_node("end", "End", {"x": 100, "y": 100})
    errors = cs.assert_creation_order([n2.id, n1.id])
    assert len(errors) > 0


def test_canvas_no_failed_nodes():
    cs = CanvasState()
    cs.add_node("start", "Start", {"x": 0, "y": 0})
    assert cs.assert_no_failed_nodes() == []


def test_canvas_required_io():
    cs = CanvasState()
    n1 = cs.add_node("start", "Start", {"x": 0, "y": 0})
    n2 = cs.add_node("end", "End", {"x": 100, "y": 100})
    cs.connect(n1.id, n2.id)
    assert cs.assert_required_io() == []


def test_canvas_no_overlapping():
    cs = CanvasState()
    cs.add_node("a", "A", {"x": 0, "y": 0})
    cs.add_node("b", "B", {"x": 100, "y": 100})
    assert cs.assert_no_overlapping_nodes() == []


def test_canvas_overlapping():
    cs = CanvasState()
    cs.add_node("a", "A", {"x": 0, "y": 0})
    cs.add_node("b", "B", {"x": 5, "y": 5})
    errors = cs.assert_no_overlapping_nodes()
    assert len(errors) > 0


def test_network_mock_manager():
    mgr = NetworkMockManager()
    rule = mgr.add_mock("/api/test", status=200, body={"ok": True})
    assert rule.url_pattern == "/api/test"
    assert len(mgr.get_mock_rules()) == 1


def test_network_fault_manager():
    mgr = NetworkMockManager()
    rule = mgr.add_fault("/api/fail", fault_type="abort", delay_ms=500)
    assert rule.fault_type == "abort"
    assert len(mgr.get_fault_rules()) == 1


def test_network_mock_clear():
    mgr = NetworkMockManager()
    mgr.add_mock("/a")
    mgr.add_fault("/b")
    mgr.clear()
    assert mgr.get_mock_rules() == []
    assert mgr.get_fault_rules() == []
