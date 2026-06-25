"""Environment template domain value objects."""

from __future__ import annotations

from enum import StrEnum


class TemplateType(StrEnum):
    BLANK = "blank"
    PRESET = "preset"
