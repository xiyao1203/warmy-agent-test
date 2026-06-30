"""插件注册表领域模型。

定义插件清单、能力和注册表接口。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class PluginCapability(StrEnum):
    """插件能力类型。"""

    AGENT_ADAPTER = "agent_adapter"
    ARTIFACT_ADAPTER = "artifact_adapter"
    ENVIRONMENT_ADAPTER = "environment_adapter"
    SCORER = "scorer"
    SECURITY_POLICY = "security_policy"


@dataclass
class PluginManifest:
    """插件清单，描述插件元数据和能力。"""

    plugin_id: str
    name: str
    version: str
    sdk_version: int
    capabilities: list[PluginCapability]
    entry_point: str
    config_schema: dict[str, object] = field(default_factory=dict)


class PluginRegistry(Protocol):
    """插件注册表协议。

    负责发现、加载和查询已安装的插件。
    """

    async def discover(self) -> list[PluginManifest]:
        """扫描并返回所有已安装插件的清单。"""
        ...

    async def get(self, plugin_id: str) -> PluginManifest | None:
        """按 ID 获取单个插件清单。"""
        ...

    async def has_capability(self, plugin_id: str, capability: PluginCapability) -> bool:
        """检查插件是否具备某项能力。"""
        ...

    async def list_by_capability(self, capability: PluginCapability) -> list[PluginManifest]:
        """列出所有具备某项能力的插件。"""
        ...
