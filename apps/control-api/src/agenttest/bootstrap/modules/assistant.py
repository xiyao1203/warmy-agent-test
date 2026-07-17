from fastapi import FastAPI

from agenttest.bootstrap.context import BootstrapContext
from agenttest.bootstrap.endpoints.assistant import _register_test_agent_endpoints


def register(app: FastAPI, context: BootstrapContext) -> None:
    _register_test_agent_endpoints(app, context.settings, context.auth)
