"""TapNow-specific browser contract and canvas normalization."""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from agenttest_plugin_canvas.adapter import (
    CanvasConnection,
    CanvasConnectionType,
    CanvasNode,
    CanvasNodeType,
    CanvasTrace,
)

USERNAME_SELECTOR = "input[name='username'], input[type='email'], input[autocomplete='username']"
PASSWORD_SELECTOR = "input[name='password'], input[type='password']"
LOGIN_SELECTOR = "button[type='submit'], button:has-text('登录'), button:has-text('Log in')"
PROMPT_SELECTOR = "textarea, [contenteditable='true'], input[placeholder*='Ask']"
SUBMIT_SELECTOR = "button:has-text('发送'), button:has-text('Send'), button[type='submit']"
READY_SELECTOR = (
    "[data-agent-status='completed'], [data-testid='agent-complete'], text=Ask before acting"
)

DANGEROUS_ACTIONS = frozenset(
    {"delete", "publish", "payment", "subscribe", "permission", "删除", "发布", "支付", "权限"}
)


class UnsafeTargetActionError(ValueError):
    pass


def assert_safe_action(action: str) -> None:
    normalized = action.strip().lower()
    if any(item in normalized for item in DANGEROUS_ACTIONS):
        raise UnsafeTargetActionError(f"dangerous target action blocked: {action}")


class TapNowBrowserContract:
    def __init__(self, *, run_id: UUID, agent_id: UUID, timeout_ms: int = 120_000) -> None:
        self._run_id = run_id
        self._agent_id = agent_id
        self._timeout_ms = timeout_ms

    async def login(self, page, credentials: Mapping[str, str]) -> None:
        username = credentials.get("username", "")
        password = credentials.get("password", "")
        if not username or not password:
            raise ValueError("TapNow login requires username and password")
        await page.fill(USERNAME_SELECTOR, username, timeout=self._timeout_ms)
        await page.fill(PASSWORD_SELECTOR, password, timeout=self._timeout_ms)
        await page.click(LOGIN_SELECTOR, timeout=self._timeout_ms)

    async def submit(self, page, intent: str) -> None:
        assert_safe_action(intent)
        await page.fill(PROMPT_SELECTOR, intent, timeout=self._timeout_ms)
        await page.click(SUBMIT_SELECTOR, timeout=self._timeout_ms)

    async def wait_until_complete(self, page) -> None:
        await page.wait_for_selector(READY_SELECTOR, timeout=self._timeout_ms)

    async def collect(self, page) -> CanvasTrace:
        raw = await page.evaluate(_COLLECT_SCRIPT)
        payload = raw if isinstance(raw, Mapping) else {}
        nodes = [_node(item) for item in _items(payload.get("nodes"))]
        connections = [_connection(item) for item in _items(payload.get("connections"))]
        artifacts = [dict(item) for item in _items(payload.get("artifacts"))]
        return CanvasTrace(
            run_id=self._run_id,
            agent_id=self._agent_id,
            nodes=nodes,
            connections=connections,
            artifacts=artifacts,
        )


def _items(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _node(item: Mapping[str, object]) -> CanvasNode:
    raw_type = str(item.get("type", "output"))
    try:
        node_type = CanvasNodeType(raw_type)
    except ValueError:
        node_type = CanvasNodeType.OUTPUT
    return CanvasNode(
        node_id=str(item.get("id", "")),
        node_type=node_type,
        label=str(item.get("label", "")),
        x=float(item.get("x", 0)),
        y=float(item.get("y", 0)),
        properties=dict(item.get("properties", {}))
        if isinstance(item.get("properties"), Mapping)
        else {},
        status=str(item.get("status", "idle")),
    )


def _connection(item: Mapping[str, object]) -> CanvasConnection:
    raw_type = str(item.get("type", "data_flow"))
    try:
        connection_type = CanvasConnectionType(raw_type)
    except ValueError:
        connection_type = CanvasConnectionType.DATA_FLOW
    return CanvasConnection(
        connection_id=str(item.get("id", "")),
        source_node_id=str(item.get("source", "")),
        target_node_id=str(item.get("target", "")),
        connection_type=connection_type,
    )


_COLLECT_SCRIPT = """
() => {
  const root = window.__canvasState || window.__INITIAL_STATE__?.canvas || {};
  const nodes = root.nodes || Array.from(document.querySelectorAll('[data-node-id]')).map((el) => ({
    id: el.getAttribute('data-node-id'),
    type: el.getAttribute('data-node-type') || 'output',
    label: el.getAttribute('aria-label') || el.textContent?.trim().slice(0, 200) || '',
    x: Number(el.getAttribute('data-x') || 0),
    y: Number(el.getAttribute('data-y') || 0),
    status: el.getAttribute('data-status') || 'idle'
  }));
  const connections = root.connections || root.edges || [];
  const artifacts = Array.from(document.querySelectorAll('img[src], video[src]')).map((el) => ({
    type: el.tagName.toLowerCase() === 'video' ? 'video' : 'image',
    url: el.currentSrc || el.src
  })).filter((item) => item.url);
  return { nodes, connections, artifacts };
}
"""
