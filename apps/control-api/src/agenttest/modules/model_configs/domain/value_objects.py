"""项目级大模型配置值对象。"""

from __future__ import annotations

from enum import StrEnum
from urllib.parse import urlsplit, urlunsplit


class ProviderType(StrEnum):
    """首期支持的模型供应商协议。"""

    OPENAI_COMPATIBLE = "openai_compatible"


class ModelPurpose(StrEnum):
    """项目默认模型的使用场景。"""

    TEST_AGENT_CHAT = "test_agent_chat"
    TEXT_JUDGE = "text_judge"
    VISION_JUDGE = "vision_judge"


def normalize_base_url(value: str) -> str:
    """规范化模型 API 根地址并拒绝 URL 内嵌凭证。"""

    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("模型 Base URL 必须是有效的 HTTP 或 HTTPS 地址")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("模型 Base URL 不能包含用户名或密码")
    if parsed.query or parsed.fragment:
        raise ValueError("模型 Base URL 不能包含查询参数或片段")
    path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))
