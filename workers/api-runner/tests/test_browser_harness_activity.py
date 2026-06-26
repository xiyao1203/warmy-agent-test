"""Browser Harness Activity 测试。"""

import pytest


class TestBrowserHarnessActivity:
    def test_activity_is_registered_as_temporal_activity(self):
        """验证 Browser Harness Activity 可被 Temporal 注册。"""
        from agenttest_api_runner.browser_harness_activity import (
            capture_page_snapshot,
        )

        # Temporal activity 装饰器会设置 __temporal_activity_definition
        assert hasattr(capture_page_snapshot, "__temporal_activity_definition")

    def test_capture_input_serialization(self):
        """验证输入可被 JSON 序列化（Temporal 传输要求）。"""
        import json

        from agenttest_api_runner.browser_harness_activity import CapturePageInput

        inp = CapturePageInput(url="https://example.com", run_case_id="case-1")
        serialized = json.dumps({"url": inp.url, "run_case_id": inp.run_case_id})
        assert "https://example.com" in serialized

    def test_snapshot_output_is_serializable(self):
        """验证输出数据类可序列化。"""
        import json

        from agenttest_api_runner.browser_harness_activity import PageSnapshot

        snap = PageSnapshot(
            url="https://example.com",
            title="Test",
            dom_nodes=42,
            html_preview="<html>...</html>",
            errors=[],
        )
        data = {
            "url": snap.url,
            "title": snap.title,
            "dom_nodes": snap.dom_nodes,
            "html_preview": snap.html_preview,
            "errors": snap.errors,
        }
        # 不应抛异常
        json.dumps(data)
