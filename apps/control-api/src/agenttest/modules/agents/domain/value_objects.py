"""Agent domain value objects and enums."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from urllib.parse import urlparse


class AgentType(StrEnum):
    GENERIC_HTTP = "generic_http"
    CANVAS = "canvas"


class VersionStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


@dataclass(frozen=True, slots=True)
class AgentConfig:
    """Configuration for an agent version.

    For ``generic_http`` agents, ``api_url`` is required and points to the
    agent's HTTP endpoint.  ``model``, ``system_prompt``, ``tools`` and other
    fields describe the agent's capabilities and constraints.
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

    def __post_init__(self) -> None:
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
        """Serialize to a plain dict for JSONB storage."""
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
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> AgentConfig:
        """Deserialize from a plain dict (e.g. JSONB column)."""
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
            cost_limit=float(cost_limit_raw) if isinstance(cost_limit_raw, (int, float, str)) else None,
        )
