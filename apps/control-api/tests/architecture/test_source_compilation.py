from pathlib import Path
import py_compile


def test_all_control_api_sources_compile() -> None:
    source_root = Path(__file__).parents[2] / "src"
    failures: list[str] = []
    for source in source_root.rglob("*.py"):
        try:
            py_compile.compile(source, doraise=True)
        except py_compile.PyCompileError as error:
            failures.append(f"{source}: {error.msg}")
    assert failures == []


import py_compile
from pathlib import Path


def test_all_control_api_sources_compile() -> None:
    source_root = Path(__file__).parents[2] / "src"
    failures: list[str] = []

    for source in source_root.rglob("*.py"):
        try:
            py_compile.compile(source, doraise=True)
        except py_compile.PyCompileError as error:
            failures.append(f"{source}: {error.msg}")

    assert failures == []
