from __future__ import annotations

from agenttest.modules.runs.domain.entities import Run, RunCase


class LocalRunOrchestrator:
    """本地可替换编排器；Temporal 适配器使用相同公开端口。"""

    async def start(self, run: Run, cases: list[RunCase]) -> str:
        del cases
        return f"run-{run.run_id.value}"

    async def cancel(self, run: Run) -> None:
        del run

