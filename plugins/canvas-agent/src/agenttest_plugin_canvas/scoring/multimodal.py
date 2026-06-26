"""多模态评分适配层。

提供 DeepEval 等多模态评分器的统一接口。
本地启发式评分器不依赖外部模型 API，可独立运行；
真实 DeepEval 在模型 API 就绪后接入。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urlparse


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
    """多模态评分器协议。"""

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


class HeuristicMultiModalScorer:
    """基于启发式规则的多模态评分器。

    通过 URL 结构化对比和 Prompt 关键词匹配给出有参考价值的评分。
    """

    async def score_image_prompt_alignment(
        self, *, image_url: str, prompt: str
    ) -> ScoreResult:
        keywords = _extract_keywords(prompt)
        url_lower = image_url.lower()
        matched = [kw for kw in keywords if kw in url_lower]
        evidence: list[str] = []
        if keywords:
            ratio = len(matched) / len(keywords)
            match_info = (
                f"Prompt 关键词 {len(keywords)} 个,"
                f" URL 命中 {len(matched)} 个 ({ratio:.0%})"
            )
            evidence.append(match_info)
            if matched:
                evidence.append(f"命中词: {', '.join(matched[:5])}")
        else:
            ratio = 0.5
            evidence.append("未能从 Prompt 提取有效关键词，返回中性分")
        score = min(1.0, max(0.0, ratio))
        return ScoreResult(
            score=score,
            passed=score >= 0.3,
            scorer_name="heuristic-image-alignment",
            explanation=_describe_alignment(score, matched),
            evidence=evidence,
            confidence=0.6 if keywords else 0.3,
        )

    async def score_image_similarity(
        self, *, reference_url: str, candidate_url: str
    ) -> ScoreResult:
        ref = urlparse(reference_url)
        cand = urlparse(candidate_url)
        evidence: list[str] = []
        if ref.netloc == cand.netloc and ref.path == cand.path:
            score = 1.0
            evidence.append("URL 完全一致（同源同路径）")
        elif ref.netloc == cand.netloc:
            score = 0.7
            evidence.append(f"同源（{ref.netloc}）但路径不同")
        else:
            score = 0.3
            evidence.append("不同源，无法确认相似度")
        return ScoreResult(
            score=score,
            passed=score >= 0.3,
            scorer_name="heuristic-image-similarity",
            explanation=f"URL 结构相似度 {score:.0%}",
            evidence=evidence,
            confidence=0.5,
        )


def _extract_keywords(text: str) -> list[str]:
    words = (
        text.lower()
        .replace(",", " ")
        .replace(".", " ")
        .replace("，", " ")
        .replace("。", " ")
        .split()
    )
    return [w for w in words if len(w) >= 2 and not w.isdigit()][:15]


def _describe_alignment(score: float, matched: list[str]) -> str:
    if score >= 0.8:
        return "高度对齐：Prompt 关键词广泛出现在生成结果中"
    elif score >= 0.5:
        return "中等对齐：部分 Prompt 关键词与生成结果匹配"
    elif score >= 0.3:
        return f"低对齐：仅 {len(matched)} 个关键词匹配，建议人工审核"
    else:
        return "未检测到明显对齐信号"
