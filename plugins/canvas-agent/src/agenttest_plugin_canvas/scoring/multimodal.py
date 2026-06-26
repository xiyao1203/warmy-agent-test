"""多模态评分适配层。

提供 DeepEval 等多模态评分器的统一接口。
首版实现基于规则的多模态评分，真实 DeepEval 在环境就绪后接入。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ScoreResult:
    """评分结果。"""

    score: float
    passed: bool
    scorer_name: str
    explanation: str
    evidence: list[str] = field(default_factory=list)
    confidence: float = 1.0


class MultiModalScorer(Protocol):
    """多模态评分器协议。

    实现者负责对图片、视频等产物进行评分。
    """

    async def score_image_prompt_alignment(
        self, *, image_url: str, prompt: str
    ) -> ScoreResult:
        """评估图片与 Prompt 的一致性。"""
        ...

    async def score_image_similarity(
        self, *, reference_url: str, candidate_url: str
    ) -> ScoreResult:
        """评估两张图片的视觉相似度。"""
        ...


class RuleBasedMultiModalScorer:
    """基于规则的多模态评分器（占位实现）。

    在真实 DeepEval 环境就绪前使用，始终返回中性分数。
    """

    async def score_image_prompt_alignment(
        self, *, image_url: str, prompt: str
    ) -> ScoreResult:
        return ScoreResult(
            score=0.5,
            passed=True,
            scorer_name="rule-based-image-alignment",
            explanation=f"占位评分（图片={image_url[:40]}..., prompt={prompt[:40]}...）",
        )

    async def score_image_similarity(
        self, *, reference_url: str, candidate_url: str
    ) -> ScoreResult:
        return ScoreResult(
            score=0.5,
            passed=True,
            scorer_name="rule-based-image-similarity",
            explanation=f"占位评分（ref={reference_url[:40]}..., cand={candidate_url[:40]}...）",
        )
