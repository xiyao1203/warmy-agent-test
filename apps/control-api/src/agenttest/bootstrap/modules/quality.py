from fastapi import FastAPI

from agenttest.bootstrap import wiring
from agenttest.bootstrap.context import BootstrapContext


def register(app: FastAPI, context: BootstrapContext) -> None:
    settings = context.settings
    auth = context.auth
    wiring._register_security_endpoints(app, settings, auth)
    wiring._register_scorer_endpoints(app, settings, auth)
    wiring._register_experiment_endpoints(app, settings, auth)
    wiring._register_review_endpoints(app, settings, auth)
    wiring._register_security_scan_endpoints(app, settings, auth)
    wiring._register_gate_endpoints(app, settings, auth)
