"""Agent 领域值对象和枚举。

定义 AgentType、VersionStatus 枚举和 AgentConfig 值对象。
AgentConfig 是不可变的配置快照，创建时校验，支持 JSONB 序列化。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from urllib.parse import urlparse


class AgentType(StrEnum):
    """Agent 类型枚举。

    - GENERIC_HTTP: 通用 HTTP Agent，通过 api_url 调用。
    - CANVAS: 画布 Agent，通过 Canvas 插件适配。
    """

    GENERIC_HTTP = "generic_http"
    CANVAS = "canvas"


class VersionStatus(StrEnum):
    """版本状态枚举。

    - DRAFT: 草稿，可编辑。
    - PUBLISHED: 已发布，不可修改。
    """

    DRAFT = "draft"
    PUBLISHED = "published"


@dataclass(frozen=True, slots=True)
class AgentConfig:
    """Agent 版本配置值对象（不可变）。

    保存 Agent 的运行时配置快照。对于 generic_http 类型，
    api_url 是必填字段，指向 Agent 的 HTTP 端点。

    创建时校验所有字段合法性，发布后不可修改——任何变更
    必须通过创建新 AgentVersion 实现。

    Attributes:
        api_url: Agent HTTP API 地址，必填且需为合法 URL。
        code_version: 代码版本号（可选）。
        git_commit: Git 提交 SHA（可选）。
        model: 使用的模型名称（可选）。
        model_params: 模型参数，如 temperature、max_tokens。
        system_prompt: 系统提示词（可选）。
        tools: 工具定义列表。
        timeout: 请求超时秒数，必须为正数。
        max_steps: 最大执行步数（可选）。
        cost_limit: 费用上限（可选）。
        system_prompt_version: System Prompt 版本标识（可选）。
        knowledge_version: 知识库或数据版本（可选）。
        adapter_version: AgentAdapter 版本（可选）。
    """

    api_url: str
    code_version: str | None = None
    git_commit: str | None = None
    model: str | None = None
    model_params: dict[str, str | int | float | bool] = field(default_factory=dict)
    system_prompt: str | None = None
    tools: list[dict[str, str]] = field(default_factory=list)
    timeout: int = 30
    max_steps: int | None = None
    cost_limit: float | None = None
    system_prompt_version: str | None = None
    knowledge_version: str | None = None
    adapter_version: str | None = None

    def __post_init__(self) -> None:
        """创建后校验：api_url 必填且合法，timeout 为正数，
        max_steps 为正数，cost_limit 为非负。"""
        if not self.api_url or not self.api_url.strip():
            raise ValueError("api_url is required")
        parsed = urlparse(self.api_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("api_url must be a valid URL")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.max_steps is not None and self.max_steps <= 0:
            raise ValueError("max_steps must be positive")
        if self.cost_limit is not None and self.cost_limit < 0:
            raise ValueError("cost_limit must be non-negative")

    def to_dict(self) -> dict[str, object]:
        """序列化为普通字典，用于 PostgreSQL JSONB 列存储。"""
        return {
            "api_url": self.api_url,
            "code_version": self.code_version,
            "git_commit": self.git_commit,
            "model": self.model,
            "model_params": dict(self.model_params),
            "system_prompt": self.system_prompt,
            "tools": list(self.tools),
            "timeout": self.timeout,
            "max_steps": self.max_steps,
            "cost_limit": self.cost_limit,
            "system_prompt_version": self.system_prompt_version,
            "knowledge_version": self.knowledge_version,
            "adapter_version": self.adapter_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> AgentConfig:
        """从字典反序列化（例如从 JSONB 列读取）。

        对每个字段做类型检查和默认值处理，避免数据库数据异常导致
        运行时崩溃。
        """
        raw_model_params = data.get("model_params") or {}
        raw_tools = data.get("tools") or []
        timeout_raw = data.get("timeout", 30)
        max_steps_raw = data.get("max_steps")
        cost_limit_raw = data.get("cost_limit")
        return cls(
            api_url=str(data["api_url"]),
            code_version=str(data["code_version"]) if data.get("code_version") else None,
            git_commit=str(data["git_commit"]) if data.get("git_commit") else None,
            model=str(data["model"]) if data.get("model") else None,
            model_params=dict(raw_model_params) if isinstance(raw_model_params, dict) else {},  # type: ignore[arg-type]
            system_prompt=str(data["system_prompt"]) if data.get("system_prompt") else None,
            tools=list(raw_tools) if isinstance(raw_tools, list) else [],  # type: ignore[arg-type]
            timeout=int(timeout_raw) if isinstance(timeout_raw, (int, float, str)) else 30,
            max_steps=int(max_steps_raw) if isinstance(max_steps_raw, (int, float, str)) else None,
            cost_limit=(
                float(cost_limit_raw) if isinstance(cost_limit_raw, (int, float, str)) else None
            ),
            system_prompt_version=str(data.get("system_prompt_version") or "") or None,
            knowledge_version=str(data.get("knowledge_version") or "") or None,
            adapter_version=str(data.get("adapter_version") or "") or None,
        )
