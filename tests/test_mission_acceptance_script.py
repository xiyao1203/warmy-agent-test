import runpy
from pathlib import Path

unique_run_ids = runpy.run_path(
    Path(__file__).parents[1] / "scripts" / "run_mission_acceptance.py",
    run_name="mission_acceptance_test",
)["unique_run_ids"]


def test_unique_run_ids_deduplicates_created_and_reported_relations() -> None:
    assets = [
        {"type": "run", "id": "run-1", "relation": "created"},
        {"type": "run", "id": "run-1", "relation": "reported"},
        {"type": "report", "id": "report-1", "relation": "created"},
    ]

    assert unique_run_ids(assets) == ["run-1"]
