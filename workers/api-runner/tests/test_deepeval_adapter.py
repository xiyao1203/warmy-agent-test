from __future__ import annotations

import pytest
from agenttest_api_runner.deepeval_adapter import DeepEvalAdapter, EvaluationInput


class Metric:
    score = 0.0
    reason = ""
    success = False

    def measure(self, test_case) -> float:
        assert test_case.input == "生成商品图"
        self.score = 0.9
        self.reason = "任务与结果一致"
        self.success = True
        return self.score


@pytest.mark.asyncio
async def test_adapter_maps_metric_result_to_case_score() -> None:
    scores = await DeepEvalAdapter([("task_completion", Metric(), 0.8)]).evaluate(
        EvaluationInput(
            scorer_version_id="scorer-1",
            intent="生成商品图",
            output="已生成图片节点",
            tools_called=["create_image_node"],
            expected_tools=["create_image_node"],
        )
    )

    assert scores[0].score == 0.9
    assert scores[0].passed is True
    assert scores[0].explanation == "任务与结果一致"
    assert scores[0].scorer_type == "deepeval:task_completion"
