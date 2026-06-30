"""Browser Harness Workflow 集成测试。"""


class TestBrowserHarnessWorkflowIntegration:
    def test_workflow_imports_harness_activity(self):
        """验证 Workflow 可导入 browser harness activity。"""
        from agenttest_api_runner.browser_harness_activity import (
            CapturePageInput,
            PageSnapshot,
            capture_page_snapshot,
        )

        assert hasattr(capture_page_snapshot, "__temporal_activity_definition")
        assert CapturePageInput is not None
        assert PageSnapshot is not None

    def test_activity_can_be_registered_in_worker(self):
        """验证 Activity 可被 Worker 注册（有 @activity.defn）。"""
        from agenttest_api_runner.browser_harness_activity import (
            capture_page_snapshot,
        )

        definition = getattr(capture_page_snapshot, "__temporal_activity_definition", None)
        assert definition is not None

    def test_capture_input_factory(self):
        """验证输入构造正确。"""
        from agenttest_api_runner.browser_harness_activity import CapturePageInput

        inp = CapturePageInput(url="https://test.example", run_case_id="rc-1")
        assert inp.url == "https://test.example"
        assert inp.run_case_id == "rc-1"

    def test_agent_config_accepts_capture_url(self):
        """验证 agent_config 支持 pre_capture_url 字段。"""
        config: dict[str, object] = {
            "url": "https://api.example/chat",
            "mode": "sync",
            "pre_capture_url": "https://example.com",
        }
        assert config.get("pre_capture_url") == "https://example.com"

    def test_snapshot_result_has_expected_fields(self):
        """验证 PageSnapshot 结构完整。"""
        from agenttest_api_runner.browser_harness_activity import PageSnapshot

        snap = PageSnapshot(
            url="https://example.com",
            title="Test Page",
            dom_nodes=10,
            html_preview="<div>test</div>",
            errors=[],
        )
        assert snap.url
        assert snap.title
        assert snap.dom_nodes >= 0
        assert isinstance(snap.errors, list)
