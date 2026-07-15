from __future__ import annotations

from collections.abc import Callable

from fastapi import FastAPI

from agenttest.bootstrap.context import BootstrapContext
from agenttest.bootstrap.modules import (
    assets,
    assistant,
    core,
    execution,
    plugins,
    quality,
)

Registrar = Callable[[FastAPI, BootstrapContext], None]

MODULE_REGISTRARS: tuple[Registrar, ...] = (
    core.register,
    assets.register,
    execution.register,
    quality.register,
    assistant.register,
    plugins.register,
)

__all__ = ["MODULE_REGISTRARS", "Registrar"]
