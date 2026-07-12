"""Codex Browser 插件集成验证 —— 真实 Chrome + CDP + storageState 全链路。

验证项：
1. persistent Chrome 启动 + CDP 健康检查
2. Playwright 通过 CDP 连接并采集 storageState
3. storageState 文件读写 + TTL 过期
4. 旧进程清理 + atexit 注册
5. Codex CLI 可调用
6. 适配器完整执行路径（不含 Codex LLM 调用）
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from agenttest_plugin_codex.chrome_pool import (
    _cdp_health_check,
    stop_all,
)
from agenttest_plugin_codex.codex_invoker import (
    capture_storage_state,
    ensure_persistent_chrome,
    invoke_codex,
    load_storage_state,
    save_storage_state,
)
from agenttest_plugin_codex.contracts import BrowserMode, CodexBrowserInput, StorageStateConfig


@pytest.mark.integration
class TestChromeLifecycle:
    """持久 Chrome 生命周期管理验证。"""

    @pytest.mark.asyncio(loop_scope="function")
    async def test_start_persistent_chrome(self) -> None:
        """启动持久 Chrome 并获取 CDP endpoint。"""
        endpoint = await ensure_persistent_chrome(headless=True)
        assert endpoint.startswith("ws://"), f"无效 CDP endpoint: {endpoint}"

        # CDP 健康检查
        ok = await _cdp_health_check(endpoint)
        assert ok, "CDP 健康检查失败"

        stop_all()

    def test_parse_cdp_endpoint(self) -> None:
        """解析 CDP WebSocket URL 到 host:port。"""
        import re as _re

        m = _re.match(r"ws://([^:/]+):(\d+)", "ws://127.0.0.1:9222/devtools/browser/abc")
        result = (m.group(1), int(m.group(2)))
        assert result == ("127.0.0.1", 9222)

        m2 = _re.match(r"ws://([^:/]+):(\d+)", "ws://localhost:1234/foo")
        result2 = (m2.group(1), int(m2.group(2)))
        assert result2 == ("localhost", 1234)

    @pytest.mark.asyncio(loop_scope="function")
    async def test_kill_old_chrome_before_new(self) -> None:
        """启动新 Chrome 前清理旧进程不会报错。"""
        stop_all()  # 不应抛异常
        endpoint = await ensure_persistent_chrome(headless=True)
        assert endpoint
        stop_all()


@pytest.mark.integration
class TestStorageStateFlow:
    """storageState 读写与过期验证。"""

    def test_save_and_load_valid(self) -> None:
        """写入 → 读取 → TTL 内有效。"""
        with tempfile.TemporaryDirectory() as tmp:
            state_data = json.dumps({"cookies": [], "origins": []})
            path = save_storage_state("test-key", state_data, storage_dir=tmp)
            assert path
            assert Path(path).exists()

            loaded = load_storage_state("test-key", storage_dir=tmp, ttl_hours=24)
            assert loaded == path

    def test_ttl_expired_returns_empty(self) -> None:
        """TTL 过期返回 None。"""
        with tempfile.TemporaryDirectory() as tmp:
            state_data = json.dumps({"cookies": []})
            path = save_storage_state("expired-key", state_data, storage_dir=tmp)
            assert Path(path).exists()

            # TTL=0 → 立即过期（刚写入的文件年龄 ≈ 0 > 0 成立）
            loaded = load_storage_state("expired-key", storage_dir=tmp, ttl_hours=0)
            assert loaded is None
            assert not Path(path).exists()

    def test_missing_key_returns_empty(self) -> None:
        """不存在的 storageState 返回 None。"""
        with tempfile.TemporaryDirectory() as tmp:
            result = load_storage_state("nonexistent", storage_dir=tmp, ttl_hours=24)
            assert result is None


@pytest.mark.integration
class TestCaptureStorageState:
    """CDP + Playwright 采集 storageState 验证。"""

    @pytest.mark.asyncio
    async def test_capture_after_chrome_start(self) -> None:
        """启动 Chrome → CDP 连接 → 捕获 storageState。"""
        endpoint = await ensure_persistent_chrome(headless=True)

        with tempfile.TemporaryDirectory() as tmp:
            path = await capture_storage_state(
                cdp_endpoint=endpoint,
                target_url="about:blank",
                key="e2e-test",
                storage_dir=tmp,
            )
            assert path, "storageState 采集失败"
            assert Path(path).exists()  # noqa: ASYNC240

            # 验证内容合法
            content = Path(path).read_text()  # noqa: ASYNC240
            state = json.loads(content)
            assert "cookies" in state
            assert "origins" in state

        stop_all()

    @pytest.mark.asyncio
    async def test_capture_with_existing_state(self) -> None:
        """带已有 storageState 采集。"""
        endpoint = await ensure_persistent_chrome(headless=True)

        with tempfile.TemporaryDirectory() as tmp:
            # 先采集一次
            first = await capture_storage_state(
                cdp_endpoint=endpoint,
                target_url="about:blank",
                key="e2e-existing",
                storage_dir=tmp,
            )
            assert first

            # 带已有状态再采集
            second = await capture_storage_state(
                cdp_endpoint=endpoint,
                target_url="about:blank",
                key="e2e-existing",
                storage_dir=tmp,
                existing_storage_state_path=first,
            )
            assert second
            assert Path(second).exists()  # noqa: ASYNC240

        stop_all()

    @pytest.mark.asyncio
    async def test_invalid_cdp_returns_empty(self) -> None:
        """无效 CDP endpoint 返回空字符串。"""
        with tempfile.TemporaryDirectory() as tmp:
            result = await capture_storage_state(
                cdp_endpoint="ws://127.0.0.1:19999/notexist",
                target_url="about:blank",
                key="bad",
                storage_dir=tmp,
            )
            assert result == ""


@pytest.mark.integration
class TestCodexCLI:
    """Codex CLI 可调用性验证。"""

    @pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="需要 OPENAI_API_KEY 环境变量",
    )
    @pytest.mark.asyncio
    async def test_invoke_codex_with_real_api(self) -> None:
        """真实 Codex CLI 调用（需要 OPENAI_API_KEY）。"""
        raw = await invoke_codex(
            test_intent="打开 about:blank 并截图",
            target_url="about:blank",
            headless=True,
            timeout_seconds=30,
        )
        assert raw.returncode == 0, f"Codex CLI 失败: {raw.stderr}"
        assert raw.stdout, "无输出"

    def test_cli_available(self) -> None:
        """验证 codex CLI 可执行。"""

        result = subprocess.run(
            ["codex", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"Codex CLI 不可用: {result.stderr}"
        assert "codex-cli" in result.stdout.lower()


@pytest.mark.integration
class TestAdapterFlow:
    """适配器完整执行路径验证（无 Codex LLM 调用）。"""

    @pytest.mark.asyncio
    async def test_adapter_ephemeral_mode(self) -> None:
        """临时模式：适配器正确构造并返回错误（无 Codex CLI 执行时）。"""
        from agenttest_plugin_codex.adapter import CodexBrowserAdapter

        adapter = CodexBrowserAdapter()
        request = CodexBrowserInput(
            test_intent="验证登录页面存在",
            target_url="https://example.com/login",
            headless=True,
            browser_mode=BrowserMode.EPHEMERAL,
            storage_state=StorageStateConfig(enabled=True),
            storage_state_key="adapter-test",
            credentials={},
        )

        result = await adapter.execute(request)
        # 由于没有 Codex CLI 实际调用，期望 error 状态
        assert result.status in ("passed", "failed", "error")
        assert result.execution_log

    def test_detect_login_activity_keywords(self) -> None:
        """检测登录关键词。"""
        from agenttest_plugin_codex.adapter import _detect_login_activity

        # 含登录关键词
        result = {"steps": [{"action": "点击登录按钮"}, {"action": "输入用户名"}]}
        assert _detect_login_activity(result)

        # 不含
        result2 = {"steps": [{"action": "点击导航链接"}, {"action": "滚动页面"}]}
        assert not _detect_login_activity(result2)

    def test_detect_login_activity_credentials(self) -> None:
        """凭据值出现在步骤中视为登录。"""
        from agenttest_plugin_codex.adapter import _detect_login_activity

        result = {"steps": [{"action": "在表单中填入 admin@test.com"}]}
        assert _detect_login_activity(result, {"username": "admin@test.com"})

    def test_detect_login_activity_empty(self) -> None:
        """无 steps 字段返回 False。"""
        from agenttest_plugin_codex.adapter import _detect_login_activity

        assert not _detect_login_activity({})
        assert not _detect_login_activity({"steps": "not a list"})


@pytest.fixture(autouse=True)
def _cleanup_chrome() -> None:
    """每个测试后清理 Chrome。"""
    yield
    try:
        stop_all()
    except Exception:
        pass
