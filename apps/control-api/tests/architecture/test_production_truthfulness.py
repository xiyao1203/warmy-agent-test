import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from scripts.check_production_truthfulness import scan_repository


def test_production_paths_have_no_false_fallbacks() -> None:
    root = Path(__file__).resolve().parents[4]

    assert scan_repository(root) == []
