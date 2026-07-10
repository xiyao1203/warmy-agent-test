from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest_plugin_canvas.tapnow import (
    TapNowBrowserContract,
    UnsafeTargetActionError,
    assert_safe_action,
)


class Page:
    def __init__(self) -> None:
        self.fills: list[tuple[str, str]] = []
        self.clicks: list[str] = []
        self.waits: list[str] = []

    async def fill(self, selector: str, value: str, **_kwargs) -> None:
        self.fills.append((selector, value))

    async def click(self, selector: str, **_kwargs) -> None:
        self.clicks.append(selector)

    async def wait_for_selector(self, selector: str, **_kwargs) -> None:
        self.waits.append(selector)

    async def evaluate(self, _script: str):
        return {
            "nodes": [
                {"id": "n1", "type": "image", "label": "Result", "x": 10, "y": 20}
            ],
            "connections": [],
            "artifacts": [{"url": "https://cdn.test/result.png", "type": "image"}],
        }


@pytest.mark.asyncio
async def test_contract_logs_in_submits_waits_and_collects_canvas() -> None:
    page = Page()
    contract = TapNowBrowserContract(run_id=uuid4(), agent_id=uuid4())

    await contract.login(page, {"username": "tester", "password": "secret"})
    await contract.submit(page, "生成一张商品图")
    await contract.wait_until_complete(page)
    trace = await contract.collect(page)

    assert any(value == "tester" for _, value in page.fills)
    assert any(value == "生成一张商品图" for _, value in page.fills)
    assert trace.nodes[0].node_id == "n1"
    assert trace.artifacts[0]["url"] == "https://cdn.test/result.png"


@pytest.mark.parametrize("action", ["delete", "publish", "payment", "permission"])
def test_contract_blocks_dangerous_actions(action: str) -> None:
    with pytest.raises(UnsafeTargetActionError):
        assert_safe_action(action)
