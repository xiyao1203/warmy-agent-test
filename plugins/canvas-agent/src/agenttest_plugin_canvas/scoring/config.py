"""模型评分配置。

管理模型 API 的地址、密钥和参数。
支持通过环境变量覆盖，不硬编码凭证。
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    """多模态评分使用的模型配置。"""

    base_url: str
    api_key: str
    vision_model: str = "gpt-4o"

    @classmethod
    def from_env(cls) -> ModelConfig:
        """从环境变量加载配置。"""
        return cls(
            base_url=os.environ.get(
                "CANVAS_MODEL_BASE_URL",
                "https://api.openai.com/v1",
            ),
            api_key=os.environ.get("CANVAS_MODEL_API_KEY", ""),
            vision_model=os.environ.get("CANVAS_MODEL_VISION", "gpt-4o"),
        )
