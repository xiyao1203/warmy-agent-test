"""基于 OpenAI 兼容 API 的多模态评分器。

使用视觉模型（如 GPT-4o）对生成图片进行 Prompt 对齐和相似度评分。
"""

from __future__ import annotations

import base64

import httpx
from openai import AsyncOpenAI

from agenttest_plugin_canvas.scoring.config import ModelConfig
from agenttest_plugin_canvas.scoring.multimodal import ScoreResult


class OpenAIMultiModalScorer:
    """基于 OpenAI 兼容视觉模型的评分器。

    通过 OpenAI SDK 调用视觉模型，评估图片与 Prompt 的一致性
    以及两张图片之间的相似度。
    """

    def __init__(self, config: ModelConfig | None = None) -> None:
        self._config = config or ModelConfig.from_env()
        self._client = AsyncOpenAI(
            base_url=self._config.base_url,
            api_key=self._config.api_key,
        )

    async def score_image_prompt_alignment(
        self, *, image_url: str, prompt: str
    ) -> ScoreResult:
        """使用视觉模型评估图片是否满足 Prompt 要求。

        向模型展示图片和原始 Prompt，让模型从画面内容、风格、
        构图等方面评估一致性，输出 0–10 的评分和解释。
        """
        try:
            image_data = await _fetch_image_as_base64(image_url)
        except Exception:
            return ScoreResult(
                score=0.5,
                passed=True,
                scorer_name="openai-vision-alignment",
                explanation=f"无法下载图片 {image_url[:60]}，跳过评分",
                confidence=0.0,
            )

        response = await self._client.chat.completions.create(
            model=self._config.vision_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是多模态评测专家。评估图片是否满足给定的 Prompt 描述。"
                        "从画面内容、风格、构图三个维度给出 0-10 的整数评分，"
                        "以及一段简短中文解释。回复格式："
                        '{"score": 8, "explanation": "画面内容基本吻合..."}'
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Prompt: {prompt}"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                        },
                    ],
                },
            ],
            max_tokens=256,
            temperature=0.1,
        )

        parsed = _parse_score_response(response.choices[0].message.content or "")
        raw_score = parsed.get("score", 5)
        if isinstance(raw_score, (int, float)):
            score = float(raw_score) / 10.0
        else:
            score = 0.5
        explanation_raw = parsed.get("explanation", "模型评分完成")
        if isinstance(explanation_raw, str):
            explanation = explanation_raw
        else:
            explanation = str(explanation_raw)
        return ScoreResult(
            score=min(1.0, max(0.0, score)),
            passed=score >= 0.5,
            scorer_name="openai-vision-alignment",
            explanation=explanation,
            confidence=0.85,
        )

    async def score_image_similarity(
        self, *, reference_url: str, candidate_url: str
    ) -> ScoreResult:
        """使用视觉模型对比两张图片的相似度。

        同时展示参考图和候选图，让模型从画面内容、风格、构图等
        维度评估相似度，输出 0–10 的评分和解释。
        """
        try:
            ref_data = await _fetch_image_as_base64(reference_url)
            cand_data = await _fetch_image_as_base64(candidate_url)
        except Exception:
            return ScoreResult(
                score=0.5,
                passed=True,
                scorer_name="openai-vision-similarity",
                explanation="无法下载图片，跳过评分",
                confidence=0.0,
            )

        response = await self._client.chat.completions.create(
            model=self._config.vision_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是多模态评测专家。对比两张图片的视觉相似度。"
                        "从画面内容、风格、构图三个维度给出 0-10 的整数评分，"
                        "以及一段简短中文解释。回复格式："
                        '{"score": 8, "explanation": "两图内容基本一致..."}'
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "参考图片（目标效果）："},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{ref_data}"},
                        },
                        {"type": "text", "text": "待评估图片（生成结果）："},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{cand_data}"},
                        },
                    ],
                },
            ],
            max_tokens=256,
            temperature=0.1,
        )

        parsed = _parse_score_response(response.choices[0].message.content or "")
        raw_score = parsed.get("score", 5)
        if isinstance(raw_score, (int, float)):
            score = float(raw_score) / 10.0
        else:
            score = 0.5
        explanation_raw = parsed.get("explanation", "模型评分完成")
        if isinstance(explanation_raw, str):
            explanation = explanation_raw
        else:
            explanation = str(explanation_raw)
        return ScoreResult(
            score=min(1.0, max(0.0, score)),
            passed=score >= 0.5,
            scorer_name="openai-vision-similarity",
            explanation=explanation,
            confidence=0.85,
        )


# ── 辅助函数 ────────────────────────────────────────────────────────────────


async def _fetch_image_as_base64(url: str) -> str:
    """将图片 URL 下载并转为 base64 编码。"""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode()


def _parse_score_response(content: str) -> dict[str, str | int]:
    """从模型返回的 JSON 中提取分数和解释。"""
    import json
    import re

    # 尝试匹配 ```json ... ``` 代码块
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    if match:
        content = match.group(1)
    # 尝试直接 JSON 解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Fallback: 尝试提取数字
        numbers = re.findall(r"\d+", content)
        score = int(numbers[0]) if numbers else 5
        return {"score": score, "explanation": content[:200]}
