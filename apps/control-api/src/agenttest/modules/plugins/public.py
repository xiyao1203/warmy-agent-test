"""插件模块公开接口。

其他模块只能从此文件导入插件相关类型。
"""

from __future__ import annotations

from agenttest.modules.plugins.domain.registry import (
    PluginCapability,
    PluginManifest,
    PluginRegistry,
)

__all__ = [
    "PluginCapability",
    "PluginManifest",
    "PluginRegistry",
]
