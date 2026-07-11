"""Stable public interface for browser profile execution references."""

from agenttest.modules.browser_profiles.application.leases import (
    BrowserSessionSnapshotRef,
    snapshot_ref_from_plugin_snapshot,
)

__all__ = ["BrowserSessionSnapshotRef", "snapshot_ref_from_plugin_snapshot"]
