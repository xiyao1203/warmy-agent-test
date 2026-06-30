import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from scripts.check_production_truthfulness import scan_repository


def test_production_paths_have_no_false_fallbacks() -> None:
    root = Path(__file__).resolve().parents[4]

    assert scan_repository(root) == []


def test_scanner_detects_auth_masking_and_fake_local_workflows(tmp_path: Path) -> None:
    source = tmp_path / "apps" / "control-api" / "src" / "unsafe.py"
    source.parent.mkdir(parents=True)
    source.write_text(
        "try:\n"
        "    actor = await actor_for(request)\n"
        "except (InvalidSessionError, Exception):\n"
        "    return authentication_required()\n"
        "except (ProjectNotFoundError, Exception):\n"
        "    return not_found()\n"
        'return f"run-{run.run_id.value}"\n'
        'if (!res.ok) throw new Error("Failed to create resource");\n',
        encoding="utf-8",
    )

    violations = scan_repository(tmp_path)

    assert {item.rule for item in violations} == {
        "broad authentication exception masking",
        "broad not-found exception masking",
        "generic frontend API error",
        "successful local execution fallback",
    }
