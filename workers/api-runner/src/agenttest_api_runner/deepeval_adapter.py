"""DeepEval metric adapter returning AgentTest-native CaseScore values."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from temporalio import activity

from .contracts import CaseScore


@dataclass(frozen=True, slots=True)
class EvaluationInput:
    scorer_version_id: str
    intent: str
    output: str
    tools_called: list[str] = field(default_factory=list)
    expected_tools: list[str] = field(default_factory=list)


class DeepEvalAdapter:
    def __init__(self, metrics: list[tuple[str, object, float]]) -> None:
        self._metrics = metrics

    async def evaluate(self, item: EvaluationInput) -> list[CaseScore]:
        try:
            from deepeval.test_case import LLMTestCase, ToolCall
        except ImportError as error:
            raise RuntimeError("DeepEval runtime is not installed") from error
        test_case = LLMTestCase(
            input=item.intent,
            actual_output=item.output,
            tools_called=[ToolCall(name=name, input_parameters={}) for name in item.tools_called],
            expected_tools=[
                ToolCall(name=name, input_parameters={}) for name in item.expected_tools
            ],
        )
        results: list[CaseScore] = []
        for name, metric, threshold in self._metrics:
            measure = getattr(metric, "measure", None)
            if measure is None:
                raise TypeError(f"DeepEval metric {name} has no measure method")
            await asyncio.to_thread(measure, test_case)
            score = float(getattr(metric, "score", 0.0) or 0.0)
            results.append(
                CaseScore(
                    scorer_version_id=item.scorer_version_id,
                    scorer_type=f"deepeval:{name}",
                    score=score,
                    passed=score >= threshold,
                    explanation=str(getattr(metric, "reason", "") or ""),
                    confidence=1.0,
                )
            )
        return results


def build_tool_correctness_metric(*, threshold: float):
    from deepeval.metrics import ToolCorrectnessMetric
    from deepeval.models import DeepEvalBaseLLM

    class _DeterministicMetricModel(DeepEvalBaseLLM):
        """Satisfy DeepEval's constructor without creating a provider client.

        Tool correctness is calculated from the expected and observed tool calls;
        reasons are disabled, so this model must never be invoked.
        """

        def load_model(self) -> _DeterministicMetricModel:
            return self

        def generate(self, *_args: object, **_kwargs: object) -> str:
            raise RuntimeError("deterministic tool correctness must not invoke an LLM")

        async def a_generate(self, *_args: object, **_kwargs: object) -> str:
            raise RuntimeError("deterministic tool correctness must not invoke an LLM")

        def get_model_name(self) -> str:
            return "agenttest-deterministic-tool-correctness"

    return ToolCorrectnessMetric(
        threshold=threshold,
        include_reason=False,
        async_mode=False,
        model=_DeterministicMetricModel("agenttest-deterministic-tool-correctness"),
    )


@dataclass(frozen=True, slots=True)
class DeepEvalTask:
    run_case_id: str
    scorer_version_id: str
    intent: str
    output: str
    tools_called: list[str]
    expected_tools: list[str]
    threshold: float = 0.8


@activity.defn
async def evaluate_deepeval_case(task: DeepEvalTask) -> list[CaseScore]:
    activity.heartbeat({"run_case_id": task.run_case_id, "phase": "deepeval"})
    metric = build_tool_correctness_metric(threshold=task.threshold)
    return await DeepEvalAdapter([("tool_correctness", metric, task.threshold)]).evaluate(
        EvaluationInput(
            scorer_version_id=task.scorer_version_id,
            intent=task.intent,
            output=task.output,
            tools_called=task.tools_called,
            expected_tools=task.expected_tools,
        )
    )
