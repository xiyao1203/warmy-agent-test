from fastapi import FastAPI

from agenttest.bootstrap import wiring
from agenttest.bootstrap.context import BootstrapContext


def register(app: FastAPI, context: BootstrapContext) -> None:
    settings = context.settings
    auth = context.auth
    wiring._register_archive_endpoints(app, settings, auth)
    wiring._register_snapshot_endpoints(app, settings, auth)
    wiring._register_dry_run_endpoints(app, settings, auth)
    wiring._register_credential_endpoints(app, settings, auth)
    wiring._register_test_account_endpoints(app, settings, auth)
    wiring._register_browser_profile_endpoints(app, settings, auth)
