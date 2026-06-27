"""Unit tests for environment snapshot domain logic."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from agenttest.modules.environments.domain.entities import (
    EnvironmentTemplate,
    EnvironmentTemplateId,
)
from agenttest.modules.environments.domain.value_objects import TemplateType
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId


def _make_user() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("dev@example.com"),
        display_name="Dev",
        role=SystemRole.DEVELOPER,
    )


def _make_project_id() -> ProjectId:
    return ProjectId(uuid4())


def _make_template(config: dict | None = None) -> EnvironmentTemplate:
    return EnvironmentTemplate.create(
        template_id=EnvironmentTemplateId.new(),
        project_id=_make_project_id(),
        name="Test Env",
        template_type=TemplateType.BLANK,
        created_by=_make_user().user_id,
        config=config or {"snapshots": []},
    )


# Snapshot 数据结构（存储在 config["snapshots"] 里）
def make_snapshot(name: str = "snap-001") -> dict:
    return {
        "id": str(uuid4()),
        "name": name,
        "config": {"key": "value"},
        "created_at": datetime.now(UTC).isoformat(),
    }


def test_snapshot_can_be_added_to_template_config() -> None:
    """快照能存入 config.snapshots 列表。"""
    tpl = _make_template(config={"snapshots": []})
    snap = make_snapshot("snap-1")
    tpl.config["snapshots"].append(snap)  # type: ignore[attr-defined]

    assert len(tpl.config["snapshots"]) == 1  # type: ignore[arg-type]
    assert tpl.config["snapshots"][0]["name"] == "snap-1"  # type: ignore[index]


def test_snapshot_preserves_config_data() -> None:
    """快照正确记录原始 config 数据。"""
    original_config = {"initial_state": {"x": 1}, "mock_services": ["auth"]}
    snap = make_snapshot()
    snap["config"] = original_config

    tpl = _make_template(config={"snapshots": [snap]})
    assert tpl.config["snapshots"][0]["config"] == original_config  # type: ignore[index]


def test_snapshot_restore_overwrites_config() -> None:
    """从快照恢复后，config 被快照内容覆盖。"""
    snap_config = {"restored": True}
    snap = make_snapshot("snap-restore")
    snap["config"] = snap_config

    tpl = _make_template(config={"snapshots": [snap], "current": "old"})
    # 模拟恢复逻辑
    snap_data = next(s for s in tpl.config["snapshots"] if s["id"] == snap["id"])  # type: ignore[attr-defined]
    tpl.config = dict(snap_data["config"])  # type: ignore[arg-type]
    tpl.config["snapshots"] = [snap]

    assert tpl.config.get("current") is None
    assert tpl.config.get("restored") is True


def test_snapshot_delete_removes_only_target() -> None:
    """删除快照只移除目标，不影响其他快照。"""
    snap1 = make_snapshot("snap-1")
    snap2 = make_snapshot("snap-2")
    tpl = _make_template(config={"snapshots": [snap1, snap2]})

    # 模拟删除 snap1
    remaining = [s for s in tpl.config["snapshots"] if s["id"] != snap1["id"]]  # type: ignore[attr-defined]
    assert len(remaining) == 1
    assert remaining[0]["name"] == "snap-2"


def test_multiple_snapshots_ordered_by_creation() -> None:
    """多个快照按添加顺序存储。"""
    names = [f"snap-{i}" for i in range(5)]
    tpl = _make_template(config={"snapshots": []})
    for name in names:
        tpl.config["snapshots"].append(make_snapshot(name))  # type: ignore[attr-defined]

    stored_names = [s["name"] for s in tpl.config["snapshots"]]  # type: ignore[attr-defined]
    assert stored_names == names


def test_snapshot_id_is_unique_per_snapshot() -> None:
    """每次创建的快照 ID 唯一。"""
    snap1 = make_snapshot("a")
    snap2 = make_snapshot("b")
    assert snap1["id"] != snap2["id"]
