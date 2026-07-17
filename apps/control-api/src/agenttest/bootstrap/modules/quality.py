from fastapi import FastAPI

from agenttest.bootstrap.context import BootstrapContext
from agenttest.bootstrap.endpoints.quality import (
    _register_experiment_endpoints,
    _register_gate_endpoints,
    _register_review_endpoints,
    _register_scorer_endpoints,
    _register_security_endpoints,
    _register_security_scan_endpoints,
)


def register(app: FastAPI, context: BootstrapContext) -> None:
    settings = context.settings
    auth = context.auth
    _register_security_endpoints(app, settings, auth)
    _register_scorer_endpoints(app, settings, auth)
    _register_experiment_endpoints(app, settings, auth)
    _register_review_endpoints(app, settings, auth)
    _register_security_scan_endpoints(app, settings, auth)
    _register_gate_endpoints(app, settings, auth)
