"""产物模块公开接口。"""

from __future__ import annotations

from agenttest.modules.artifacts.domain.models import (
    Artifact,
    ArtifactId,
    ArtifactRepository,
    ArtifactStorage,
)

__all__ = [
    "Artifact",
    "ArtifactId",
    "ArtifactRepository",
    "ArtifactStorage",
]
