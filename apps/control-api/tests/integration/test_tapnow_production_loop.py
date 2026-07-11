from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from uuid import uuid4

import pytest
from agenttest.modules.gates.application.evaluate import GateEvidence, evaluate_evidence
from agenttest.modules.gates.domain.entities import ReleaseGate
from agenttest.modules.reviews.domain.auto_collector import AutoCollector
from agenttest.modules.security.adapters.promptfoo_adapter import PromptfooScanner


class _UnsafeAgentHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 - stdlib HTTP handler contract
        content_length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(content_length)
        payload = json.dumps({"output": "secret-config system prompt"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, _format: str, *_args: object) -> None:
        return None


def _promptfoo_path() -> str:
    promptfoo_bin = Path("apps/web/node_modules/.bin/promptfoo").resolve()
    assert promptfoo_bin.exists(), "run pnpm install before the production integration suite"
    return str(promptfoo_bin)


@pytest.mark.asyncio
async def test_promptfoo_finding_flows_to_review_and_release_gate() -> None:
    promptfoo_bin = _promptfoo_path()

    server = ThreadingHTTPServer(("127.0.0.1", 0), _UnsafeAgentHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        scanner = PromptfooScanner(promptfoo_bin)
        findings = await scanner.run_scan(
            agent_endpoint=f"http://127.0.0.1:{server.server_port}/agent",
            scan_type="tapnow-readonly",
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    assert findings
    assert findings[0]["source"] == "promptfoo"
    assert findings[0]["severity"] == "high"

    collector = AutoCollector()
    assert collector.should_collect(
        {
            "confidence": 1.0,
            "scores": {"deepeval:tool_correctness": 1.0},
            "has_security_findings": True,
        }
    )

    gate = ReleaseGate.create(project_id=uuid4(), name="tapnow-production")
    decision = evaluate_evidence(
        gate,
        GateEvidence(
            run_id=uuid4(),
            pass_rate=1.0,
            critical_passed=True,
            total_cost=0.0,
            security_score=0.3,
            pending_reviews=1,
            blocking_findings=1,
        ),
    )
    assert decision.passed is False
    assert any("高危安全发现" in failure for failure in decision.failures)
