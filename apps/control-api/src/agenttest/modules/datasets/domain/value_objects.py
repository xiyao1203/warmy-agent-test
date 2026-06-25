"""Dataset domain value objects and enums."""

from __future__ import annotations

from enum import StrEnum


class VersionStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class ExecutionMode(StrEnum):
    API = "api"
    BROWSER = "browser"


class Priority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class RiskLevel(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TestGroup(StrEnum):
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"
