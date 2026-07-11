from __future__ import annotations

from uuid import uuid4

import pytest
from agenttest_api_runner.deepeval_adapter import (
    DeepEvalAdapter,
    EvaluationInput,
    build_tool_correctness_metric,
)
from agenttest_api_runner.tapnow_activity import TapNowResult, TapNowTaskInput, execute_tapnow_page
from temporalio.converter import DataConverter


class _CanvasPage:
    def __init__(self) -> None:
        self.filled_values: list[str] = []

    async def fill(self, _selector: str, value: str, **_kwargs: object) -> None:
        self.filled_values.append(value)

    async def click(self, _selector: str, **_kwargs: object) -> None:
        return None

    async def wait_for_selector(self, _selector: str, **_kwargs: object) -> None:
        return None

    async def evaluate(self, _script: str) -> dict[str, object] | str:
        if "__agenttestTapNowState" in _script:
            return "completed"
        return {
            "nodes": [
                {
                    "id": "prompt-1",
                    "type": "prompt",
                    "label": "生成商品图",
                    "x": 10,
                    "y": 20,
                    "status": "completed",
                },
                {
                    "id": "image-1",
                    "type": "image",
                    "label": "商品主图",
                    "x": 30,
                    "y": 40,
                    "status": "completed",
                },
            ],
            "connections": [
                {
                    "id": "edge-1",
                    "source": "prompt-1",
                    "target": "image-1",
                    "type": "data_flow",
                }
            ],
            "artifacts": [{"type": "image", "url": "https://tapnow.test/image.png"}],
        }

    async def screenshot(self) -> bytes:
        return b"tapnow-png"


class _ArtifactUploader:
    async def upload(self, **kwargs: object) -> dict[str, str]:
        assert kwargs["content"] == b"tapnow-png"
        return {
            "id": "artifact-tapnow-1",
            "sha256": "sha256-tapnow",
            "content_type": "image/png",
        }


@pytest.mark.asyncio
async def test_tapnow_execution_produces_canvas_artifact_and_deepeval_score() -> None:
    page = _CanvasPage()
    task = TapNowTaskInput(
        project_id=str(uuid4()),
        run_id=str(uuid4()),
        run_case_id=str(uuid4()),
        agent_id=str(uuid4()),
        target_url="https://tapnow.test/canvas",
        intent="生成商品图",
    )

    result = await execute_tapnow_page(
        page,
        task,
        _ArtifactUploader(),
        {"username": "tapnow-user", "password": "tapnow-secret"},
    )
    metric = build_tool_correctness_metric(threshold=0.8)
    scores = await DeepEvalAdapter([("tool_correctness", metric, 0.8)]).evaluate(
        EvaluationInput(
            scorer_version_id="deepeval-v1",
            intent=task.intent,
            output="商品主图已生成",
            tools_called=["generate_image"],
            expected_tools=["generate_image"],
        )
    )

    canvas = result.evidence["canvas"]
    assert isinstance(canvas, dict)
    assert len(canvas["nodes"]) == 2
    artifacts = result.evidence["artifacts"]
    assert isinstance(artifacts, list)
    assert isinstance(artifacts[0], dict)
    assert artifacts[0]["id"] == "artifact-tapnow-1"
    assert scores[0].passed is True
    assert scores[0].score == pytest.approx(1.0)
    assert "tapnow-secret" not in str(result.evidence)


@pytest.mark.asyncio
async def test_temporal_round_trips_nested_tapnow_evidence() -> None:
    result = TapNowResult(
        run_case_id=str(uuid4()),
        status="passed",
        evidence={
            "execution_outcome": "success",
            "canvas": {"nodes": [{"id": "node-1", "x": 10.0}]},
            "artifacts": [{"id": "artifact-1"}],
        },
    )

    payloads = await DataConverter.default.encode([result])
    decoded = await DataConverter.default.decode(payloads, [TapNowResult])

    assert decoded[0] == result
