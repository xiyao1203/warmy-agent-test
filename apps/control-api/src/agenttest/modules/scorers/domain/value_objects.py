"""Scorer 领域值对象。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ScorerType(StrEnum):
    """评分器类型。"""
    RULE = "rule"
    MODEL = "model"
    REFERENCE = "reference"


@dataclass(frozen=True, slots=True)
class ScorerResult:
    """评分结果值对象。

    Attributes:
        score: 评分值（0.0-1.0）。
        passed: 是否通过阈值。
        explanation: 评分说明。
        evidence: 评分依据。
        confidence: 置信度（0.0-1.0）。
        scorer_version: 评分器版本。
    """
    score: float
    passed: bool
    explanation: str = ""
    evidence: str = ""
    confidence: float = 1.0
    scorer_version: str = "1.0"

    def to_dict(self) -> dict[str, object]:
        return {
            "score": self.score,
            "passed": self.passed,
            "explanation": self.explanation,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "scorer_version": self.scorer_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ScorerResult:
        return cls(
            score=float(data.get("score", 0)),  # type: ignore[arg-type]
            passed=bool(data.get("passed", False)),
            explanation=str(data.get("explanation", "")),
            evidence=str(data.get("evidence", "")),
            confidence=float(data.get("confidence", 1.0)),  # type: ignore[arg-type]
            scorer_version=str(data.get("scorer_version", "1.0")),
        )
