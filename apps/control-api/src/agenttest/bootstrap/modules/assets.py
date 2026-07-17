from fastapi import FastAPI

from agenttest.bootstrap.context import BootstrapContext
from agenttest.bootstrap.endpoints.assets import (
    _register_archive_endpoints,
    _register_browser_profile_endpoints,
    _register_credential_endpoints,
    _register_dry_run_endpoints,
    _register_snapshot_endpoints,
    _register_test_account_endpoints,
)


def register(app: FastAPI, context: BootstrapContext) -> None:
    settings = context.settings
    auth = context.auth
    _register_archive_endpoints(app, settings, auth)
    _register_snapshot_endpoints(app, settings, auth)
    _register_dry_run_endpoints(app, settings, auth)
    _register_credential_endpoints(app, settings, auth)
    _register_test_account_endpoints(app, settings, auth)
    _register_browser_profile_endpoints(app, settings, auth)
