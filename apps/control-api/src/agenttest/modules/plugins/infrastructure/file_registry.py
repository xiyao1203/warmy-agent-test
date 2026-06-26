"""基于文件系统的插件发现和注册。

扫描 plugins/ 目录下包含 manifest.json 的子目录，加载并缓存插件清单。
"""

from __future__ import annotations

import json
from pathlib import Path

from agenttest.modules.plugins.domain.registry import (
    PluginCapability,
    PluginManifest,
)


class FileBasedPluginRegistry:
    """从文件系统发现和加载插件清单。"""

    def __init__(self, plugins_root: Path) -> None:
        self._root = plugins_root
        self._cache: dict[str, PluginManifest] = {}

    async def discover(self) -> list[PluginManifest]:
        """扫描 plugins/ 目录，发现所有包含 manifest.json 的插件。"""
        discovered: list[PluginManifest] = []
        if not self._root.exists():
            return discovered

        for plugin_dir in self._root.iterdir():
            if not plugin_dir.is_dir():
                continue
            manifest_path = plugin_dir / "manifest.json"
            if not manifest_path.exists():
                continue
            try:
                raw = json.loads(manifest_path.read_text(encoding="utf-8"))
                capabilities = [PluginCapability(c) for c in raw.get("capabilities", [])]
                default_ep = f"agenttest_plugin_{raw['id'].replace('-', '_')}"
                manifest = PluginManifest(
                    plugin_id=raw["id"],
                    name=raw["name"],
                    version=raw["version"],
                    sdk_version=raw["sdk_version"],
                    capabilities=capabilities,
                    entry_point=raw.get("entry_point", default_ep),
                    config_schema=raw.get("config_schema", {}),
                )
                self._cache[manifest.plugin_id] = manifest
                discovered.append(manifest)
            except (KeyError, json.JSONDecodeError, ValueError):
                continue

        return discovered

    async def get(self, plugin_id: str) -> PluginManifest | None:
        """按 ID 获取插件，优先使用缓存。"""
        if plugin_id in self._cache:
            return self._cache[plugin_id]
        await self.discover()
        return self._cache.get(plugin_id)

    async def has_capability(
        self, plugin_id: str, capability: PluginCapability
    ) -> bool:
        manifest = await self.get(plugin_id)
        return manifest is not None and capability in manifest.capabilities

    async def list_by_capability(
        self, capability: PluginCapability
    ) -> list[PluginManifest]:
        manifests = await self.discover()
        return [m for m in manifests if capability in m.capabilities]
