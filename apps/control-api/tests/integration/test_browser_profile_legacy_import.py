import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from agenttest.entrypoints.import_browser_profiles import default_registry_path
from agenttest.modules.browser_profiles.application.legacy_import import (
    import_legacy_browser_profiles,
)
from agenttest.modules.browser_profiles.domain.entities import BrowserProfile


class Repository:
    def __init__(self) -> None:
        self.items: list[BrowserProfile] = []

    async def list(self, project_id: UUID) -> list[BrowserProfile]:
        return [item for item in self.items if item.project_id == project_id]

    async def add(self, item: BrowserProfile) -> None:
        self.items.append(item)


def test_import_command_uses_the_legacy_registry_only_when_explicitly_invoked() -> None:
    project_id = uuid4()

    assert default_registry_path(project_id) == (
        Path.home() / ".agenttest" / "browser-profiles" / f"{project_id}.json"
    )


@pytest.mark.asyncio
async def test_legacy_import_is_explicit_idempotent_and_does_not_reuse_secret_paths(
    tmp_path: Path,
) -> None:
    project_id = uuid4()
    actor_id = uuid4()
    registry = tmp_path / f"{project_id}.json"
    registry.write_text(
        json.dumps(
            [
                {
                    "profile_id": str(uuid4()),
                    "project_id": str(project_id),
                    "name": "Legacy TapNow",
                    "target_domain": "app.tapnow.ai",
                    "user_data_dir": "/legacy/contains/cookies",
                    "storage_state_path": "/legacy/storage_state.json",
                }
            ]
        )
    )
    repository = Repository()
    controlled_root = tmp_path / "controlled"

    first = await import_legacy_browser_profiles(
        registry_path=registry,
        project_id=project_id,
        actor_id=actor_id,
        controlled_root=controlled_root,
        repository=repository,
    )
    second = await import_legacy_browser_profiles(
        registry_path=registry,
        project_id=project_id,
        actor_id=actor_id,
        controlled_root=controlled_root,
        repository=repository,
    )

    assert first == 1
    assert second == 0
    assert len(repository.items) == 1
    imported = repository.items[0]
    assert imported.auth_state_status == "missing"
    assert imported.user_data_dir.startswith(str(controlled_root))
    assert imported.user_data_dir != "/legacy/contains/cookies"
