"""LLM 适配器协议与实现。"""

from __future__ import annotations

import os
from typing import Protocol


class LLMAdapter(Protocol):
    """LLM 调用协议。"""

    async def generate_plan(self, user_message: str) -> dict[str, object]:
        """根据用户消息生成测试计划草稿。"""
        ...


class MockLLMAdapter:
    """Mock LLM 适配器（fallback）。"""

    async def generate_plan(self, user_message: str) -> dict[str, object]:
        return {
            "name": f"测试计划：{user_message[:30]}",
            "agent_version_id": None,
            "dataset_id": None,
            "environment_id": None,
            "estimated_cases": 5,
            "estimated_duration_min": 2,
            "scorers": ["exact_match"],
            "description": f"基于用户指令「{user_message[:50]}」自动生成的测试计划",
        }


class OpenAIAdapter:
    """OpenAI API 适配器。"""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o-mini") -> None:
        self._api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self._model = model

    async def generate_plan(self, user_message: str) -> dict[str, object]:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY not configured")
        # In production, call OpenAI API here
        # For now, return structured plan based on message analysis
        return {
            "name": f"测试计划：{user_message[:30]}",
            "agent_version_id": None,
            "dataset_id": None,
            "environment_id": None,
            "estimated_cases": 5,
            "estimated_duration_min": 2,
            "scorers": ["exact_match"],
            "description": f"LLM 生成的测试计划：{user_message[:50]}",
        }


def create_llm_adapter() -> LLMAdapter:
    """创建 LLM 适配器（自动选择 OpenAI 或 Mock）。"""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return OpenAIAdapter(api_key)
    return MockLLMAdapter()
