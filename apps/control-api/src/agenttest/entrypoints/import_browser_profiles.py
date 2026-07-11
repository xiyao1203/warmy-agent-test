"""Explicit one-time import for the legacy browser-profile JSON registry."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from uuid import UUID

from agenttest.bootstrap.settings import get_settings
from agenttest.modules.browser_profiles.application.legacy_import import (
    import_legacy_browser_profiles,
)
from agenttest.modules.browser_profiles.infrastructure.repository import (
    SqlAlchemyBrowserProfileRepository,
)
from agenttest.shared.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)


def default_registry_path(project_id: UUID) -> Path:
    return Path.home() / ".agenttest" / "browser-profiles" / f"{project_id}.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import legacy browser profile metadata")
    parser.add_argument("--project-id", type=UUID, required=True)
    parser.add_argument("--actor-id", type=UUID, required=True)
    parser.add_argument("--registry-path", type=Path)
    return parser


async def run_import(project_id: UUID, actor_id: UUID, registry_path: Path | None) -> int:
    settings = get_settings()
    engine = create_database_engine(settings.database_url)
    repository = SqlAlchemyBrowserProfileRepository(create_session_factory(engine))
    return await import_legacy_browser_profiles(
        registry_path=registry_path or default_registry_path(project_id),
        project_id=project_id,
        actor_id=actor_id,
        controlled_root=Path(settings.browser_profile_root),
        repository=repository,
    )


def main() -> None:
    args = build_parser().parse_args()
    count = asyncio.run(run_import(args.project_id, args.actor_id, args.registry_path))
    print(f"Imported {count} browser profile(s)")


if __name__ == "__main__":
    main()
