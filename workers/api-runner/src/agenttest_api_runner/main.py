"""API Runner Worker startup entry point."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

from temporalio.client import Client
from temporalio.worker import Worker

from .activities import execute_agent_case, post_run_result
from .browser_harness_activity import capture_page_snapshot
from .codex_browser_activity import run_codex_browser_case
from .deepeval_adapter import evaluate_deepeval_case
from .mission_activities import execute_mission_stage
from .mission_workflow import TestMissionWorkflow
from .playwright_activity import run_playwright_case
from .postprocess_activities import execute_postprocess_stage
from .postprocess_workflow import RunPostprocessWorkflow
from .tapnow_activity import run_tapnow_case
from .target_chat import TargetAgentChatWorkflow, execute_target_chat
from .workflow import RunWorkflow


@dataclass(frozen=True, slots=True)
class WorkerSettings:
    """Connection settings shared with the control plane Run orchestrator."""

    address: str
    namespace: str
    task_queue: str

    @classmethod
    def from_environment(cls) -> WorkerSettings:
        address = os.environ.get("AGENTTEST_TEMPORAL_ADDRESS")
        if not address:
            raise RuntimeError("API Runner requires a Temporal address")
        return cls(
            address=address,
            namespace=os.environ.get("AGENTTEST_TEMPORAL_NAMESPACE", "default"),
            task_queue=os.environ.get(
                "AGENTTEST_TEMPORAL_TASK_QUEUE",
                "agenttest-api-runner",
            ),
        )


async def run() -> None:
    """Connect to Temporal and consume API Runner workflows."""

    settings = WorkerSettings.from_environment()
    client = await Client.connect(settings.address, namespace=settings.namespace)
    worker = Worker(
        client,
        task_queue=settings.task_queue,
        workflows=[
            RunWorkflow,
            TargetAgentChatWorkflow,
            TestMissionWorkflow,
            RunPostprocessWorkflow,
        ],
        activities=[
            execute_agent_case,
            post_run_result,
            capture_page_snapshot,
            run_playwright_case,
            run_codex_browser_case,
            execute_target_chat,
            run_tapnow_case,
            evaluate_deepeval_case,
            execute_mission_stage,
            execute_postprocess_stage,
        ],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run())
