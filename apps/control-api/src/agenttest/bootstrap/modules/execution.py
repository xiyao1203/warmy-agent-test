from fastapi import FastAPI

from agenttest.bootstrap.context import BootstrapContext
from agenttest.bootstrap.endpoints.execution import (
    _register_artifact_endpoints,
    _register_run_stream_endpoints,
    _register_trace_diff_endpoints,
)


def register(app: FastAPI, context: BootstrapContext) -> None:
    settings = context.settings
    auth = context.auth
    _register_artifact_endpoints(app, settings, auth)
    _register_trace_diff_endpoints(app, settings, auth)
    _register_run_stream_endpoints(app, settings, auth)
