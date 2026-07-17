from fastapi import FastAPI

from agenttest.bootstrap import wiring
from agenttest.bootstrap.context import BootstrapContext


def register(app: FastAPI, context: BootstrapContext) -> None:
    settings = context.settings
    auth = context.auth
    wiring._register_artifact_endpoints(app, settings, auth)
    wiring._register_trace_diff_endpoints(app, settings, auth)
    wiring._register_run_stream_endpoints(app, settings, auth)
