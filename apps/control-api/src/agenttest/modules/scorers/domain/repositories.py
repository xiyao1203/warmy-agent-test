"""Scorer 领域仓库接口。"""

from __future__ import annotations

from typing import Protocol

from agenttest.modules.projects.public import ProjectId
from agenttest.modules.scorers.domain.entities import Scorer, ScorerId


class ScorerRepository(Protocol):
    """评分器持久化仓库接口。"""

    async def get_by_id(self, scorer_id: ScorerId) -> Scorer | None: ...

    async def get_by_id_and_project(
        self, scorer_id: ScorerId, project_id: ProjectId
    ) -> Scorer | None: ...

    async def list_by_project(
        self,
        project_id: ProjectId,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Scorer], int]: ...

    async def add(self, scorer: Scorer) -> None: ...

    async def save(self, scorer: Scorer) -> None: ...

    async def delete(self, scorer_id: ScorerId) -> None: ...
