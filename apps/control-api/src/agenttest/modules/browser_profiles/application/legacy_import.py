from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from uuid import UUID

from agenttest.modules.browser_profiles.domain.entities import BrowserProfile


class LegacyImportRepository(Protocol):
    def list(self, project_id: UUID) -> Awaitable[list[BrowserProfile]]: ...

    def add(self, item: BrowserProfile) -> Awaitable[None]: ...


async def import_legacy_browser_profiles(
    *,
    registry_path: Path,
    project_id: UUID,
    actor_id: UUID,
    controlled_root: Path,
    repository: LegacyImportRepository,
) -> int:
    raw = await asyncio.to_thread(registry_path.read_text, encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError("旧浏览器实例注册表不是有效 JSON") from error
    if not isinstance(payload, list):
        raise ValueError("旧浏览器实例注册表必须是数组")
    resolved_root = await asyncio.to_thread(lambda: controlled_root.expanduser().resolve())
    existing = await repository.list(project_id)
    existing_ids = {item.id for item in existing}
    existing_names = {item.name for item in existing}
    imported = 0
    now = datetime.now(UTC)
    for value in payload:
        if not isinstance(value, dict):
            continue
        try:
            profile_id = UUID(str(value.get("profile_id") or ""))
            legacy_project_id = UUID(str(value.get("project_id") or project_id))
        except ValueError:
            continue
        name = str(value.get("name") or "").strip()
        if legacy_project_id != project_id or not name:
            continue
        if profile_id in existing_ids or name in existing_names:
            continue
        item = BrowserProfile.create(
            project_id=project_id,
            name=name,
            target_domain=str(value.get("target_domain") or "").strip(),
            created_by=actor_id,
            now=now,
        )
        item.id = profile_id
        item.user_data_dir = str(resolved_root / str(profile_id) / "profile")
        await repository.add(item)
        existing_ids.add(item.id)
        existing_names.add(item.name)
        imported += 1
    return imported
