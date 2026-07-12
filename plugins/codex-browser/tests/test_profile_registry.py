"""Profile Registry 单元测试。"""

from __future__ import annotations

import tempfile

import pytest
from agenttest_plugin_codex.profile_registry import (
    create_profile,
    delete_profile,
    get_profile,
    list_profiles,
    update_profile,
)

TEST_PROJECT = "test-project-001"


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    """每个测试前后清理 registry。"""
    from agenttest_plugin_codex.profile_registry import _registry_root

    root = _registry_root()
    if root.exists():
        for f in root.glob("*.json"):
            f.unlink()
    yield
    if root.exists():
        for f in root.glob("*.json"):
            f.unlink()


class TestProfileCRUD:
    """CRUD 基础操作验证。"""

    def test_create_profile(self) -> None:
        """创建 Profile 返回完整字段。"""
        profile = create_profile(TEST_PROJECT, "测试环境")
        assert profile.profile_id
        assert profile.project_id == TEST_PROJECT
        assert profile.name == "测试环境"
        assert profile.status == "stopped"
        assert profile.cdp_port >= 9222
        assert not profile.cdp_endpoint
        assert profile.created_at
        assert profile.updated_at

    def test_create_with_custom_dir(self) -> None:
        """自定义 user_data_dir 生效。"""
        with tempfile.TemporaryDirectory() as tmp:
            profile = create_profile(
                TEST_PROJECT,
                "custom",
                user_data_dir=tmp,
            )
            assert profile.user_data_dir == tmp

    def test_list_profiles(self) -> None:
        """列出项目所有 Profile。"""
        create_profile(TEST_PROJECT, "A")
        create_profile(TEST_PROJECT, "B")
        profiles = list_profiles(TEST_PROJECT)
        assert len(profiles) == 2
        names = {p.name for p in profiles}
        assert names == {"A", "B"}

    def test_get_profile(self) -> None:
        """按 ID 查找 Profile。"""
        p = create_profile(TEST_PROJECT, "test")
        found = get_profile(TEST_PROJECT, p.profile_id)
        assert found is not None
        assert found.name == "test"

    def test_get_profile_not_found(self) -> None:
        """查找不存在的 Profile 返回 None。"""
        assert get_profile(TEST_PROJECT, "nonexistent") is None

    def test_get_profile_without_project(self) -> None:
        """不传 project_id 时遍历查找。"""
        p = create_profile(TEST_PROJECT, "global-lookup")
        found = get_profile("", p.profile_id)
        assert found is not None
        assert found.name == "global-lookup"

    def test_update_profile(self) -> None:
        """更新 Profile 字段。"""
        p = create_profile(TEST_PROJECT, "old-name")
        updated = update_profile(
            TEST_PROJECT,
            p.profile_id,
            name="new-name",
            status="running",
            cdp_endpoint="ws://127.0.0.1:9222/devtools/abc",
            storage_state_path="/tmp/state.json",
        )
        assert updated is not None
        assert updated.name == "new-name"
        assert updated.status == "running"
        assert updated.cdp_endpoint == "ws://127.0.0.1:9222/devtools/abc"
        assert updated.storage_state_path == "/tmp/state.json"

        # 验证持久化
        reloaded = get_profile(TEST_PROJECT, p.profile_id)
        assert reloaded is not None
        assert reloaded.name == "new-name"

    def test_update_nonexistent(self) -> None:
        """更新不存在的 Profile 返回 None。"""
        assert update_profile(TEST_PROJECT, "ghost", name="x") is None

    def test_delete_profile(self) -> None:
        """删除 Profile 后列表减少。"""
        p = create_profile(TEST_PROJECT, "to-delete")
        assert len(list_profiles(TEST_PROJECT)) == 1
        assert delete_profile(TEST_PROJECT, p.profile_id)
        assert len(list_profiles(TEST_PROJECT)) == 0

    def test_delete_nonexistent(self) -> None:
        """删除不存在的 Profile 返回 False。"""
        assert not delete_profile(TEST_PROJECT, "ghost")

    def test_cdp_port_unique_per_project(self) -> None:
        """同项目 Profile 端口不冲突。"""
        p1 = create_profile(TEST_PROJECT, "A")
        p2 = create_profile(TEST_PROJECT, "B")
        assert p1.cdp_port != p2.cdp_port


class TestProjectIsolation:
    """项目间 Profile 隔离。"""

    def test_projects_isolated(self) -> None:
        """不同项目的 Profile 不互相可见。"""
        create_profile("proj-a", "alpha")
        create_profile("proj-b", "beta")
        assert len(list_profiles("proj-a")) == 1
        assert len(list_profiles("proj-b")) == 1
        assert list_profiles("proj-a")[0].name == "alpha"


class TestRegistryPersistence:
    """JSON 文件持久化验证。"""

    def test_persists_to_json(self) -> None:
        """Profile 写入 JSON 文件后能重新读出。"""
        p = create_profile(TEST_PROJECT, "persisted")
        from agenttest_plugin_codex.profile_registry import _registry_path

        path = _registry_path(TEST_PROJECT)
        assert path.exists()

        # 重新读取（无缓存）
        profiles = list_profiles(TEST_PROJECT)
        assert any(x.profile_id == p.profile_id for x in profiles)
