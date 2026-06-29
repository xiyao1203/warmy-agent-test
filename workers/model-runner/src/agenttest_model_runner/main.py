"""Model Runner Worker 启动入口。"""

from __future__ import annotations

import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from .activities import ModelActivities
from .workflow import ModelInvocationWorkflow


async def run() -> None:
    """连接 Temporal 并运行独立模型任务队列。"""

    address = os.environ.get("AGENTTEST_TEMPORAL_ADDRESS")
    master_key = os.environ.get("AGENTTEST_MODEL_CREDENTIAL_KEY")
    if not address or not master_key:
        raise RuntimeError("Model Runner requires Temporal address and model credential key")
    client = await Client.connect(
        address,
        namespace=os.environ.get("AGENTTEST_TEMPORAL_NAMESPACE", "default"),
    )
    activities = ModelActivities(master_key)
    worker = Worker(
        client,
        task_queue=os.environ.get("AGENTTEST_MODEL_RUNNER_TASK_QUEUE", "agenttest-model-runner"),
        workflows=[ModelInvocationWorkflow],
        activities=[activities.invoke_model],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run())
