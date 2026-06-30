from __future__ import annotations

from agenttest.modules.runs.application.ports import RunRuntimeUnavailableError
from agenttest.modules.runs.domain.entities import Run, RunCase


class LocalRunOrchestrator:
    """缺少 Temporal 时明确拒绝执行，避免产生假 Workflow。"""

    async def ensure_available(self) -> None:
        raise RunRuntimeUnavailableError("Run execution runtime is unavailable")

    async def start(self, run: Run, cases: list[RunCase]) -> str:
        del run, cases
        raise RunRuntimeUnavailableError("Run execution runtime is unavailable")

    async def cancel(self, run: Run) -> None:
        del run
        raise RunRuntimeUnavailableError("Run execution runtime is unavailable")
