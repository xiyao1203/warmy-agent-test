from fastapi import FastAPI

from agenttest.bootstrap import wiring
from agenttest.bootstrap.context import BootstrapContext


def register(app: FastAPI, context: BootstrapContext) -> None:
    wiring._register_test_agent_endpoints(app, context.settings, context.auth)
