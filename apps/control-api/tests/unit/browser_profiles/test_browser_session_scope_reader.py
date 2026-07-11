from uuid import uuid4

from agenttest.modules.browser_profiles.infrastructure.scope_reader import (
    snapshot_ref_from_plugin_snapshot,
)


def test_scope_reader_parses_only_complete_browser_snapshot_reference() -> None:
    profile_id = uuid4()

    ref = snapshot_ref_from_plugin_snapshot(
        {
            "browser_profile_snapshot": {
                "browser_profile_id": str(profile_id),
                "auth_state_version": 4,
                "auth_state_sha256": "c" * 64,
                "auth_state_envelope": "must-be-ignored",
            }
        }
    )

    assert ref is not None
    assert ref.browser_profile_id == profile_id
    assert ref.auth_state_version == 4
    assert ref.auth_state_sha256 == "c" * 64


def test_scope_reader_rejects_missing_or_malformed_snapshot() -> None:
    assert snapshot_ref_from_plugin_snapshot({}) is None
    assert (
        snapshot_ref_from_plugin_snapshot(
            {
                "browser_profile_snapshot": {
                    "browser_profile_id": str(uuid4()),
                    "auth_state_version": 0,
                    "auth_state_sha256": "short",
                }
            }
        )
        is None
    )
