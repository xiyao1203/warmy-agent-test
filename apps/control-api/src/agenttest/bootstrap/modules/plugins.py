from pathlib import Path

from fastapi import FastAPI

from agenttest.bootstrap.context import BootstrapContext
from agenttest.modules.plugins.infrastructure.file_registry import FileBasedPluginRegistry


def register(app: FastAPI, context: BootstrapContext) -> None:
    del context
    plugins_root = Path(__file__).resolve().parents[6] / "plugins"
    app.state.plugins = FileBasedPluginRegistry(plugins_root)
