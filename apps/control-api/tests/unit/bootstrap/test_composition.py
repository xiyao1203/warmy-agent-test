from importlib import import_module
from pathlib import Path

EXPECTED_MODULES = (
    "core",
    "assets",
    "execution",
    "quality",
    "assistant",
    "plugins",
)


def test_app_module_is_only_top_level_composition() -> None:
    path = Path("apps/control-api/src/agenttest/bootstrap/app.py")
    source = path.read_text(encoding="utf-8")

    assert len(source.splitlines()) <= 350
    assert "session.execute" not in source
    assert "def _register_" not in source


def test_each_module_exposes_one_register_function() -> None:
    for name in EXPECTED_MODULES:
        module = import_module(f"agenttest.bootstrap.modules.{name}")
        assert callable(module.register)
