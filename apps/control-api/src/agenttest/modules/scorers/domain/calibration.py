from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CalibrationMetrics:
    accuracy: float
    false_positive_rate: float
    false_negative_rate: float
    agreement: float

    @classmethod
    def from_labels(
        cls, *, predicted: tuple[bool, ...], actual: tuple[bool, ...]
    ) -> CalibrationMetrics:
        if not predicted or len(predicted) != len(actual):
            raise ValueError("calibration labels must be non-empty and aligned")
        true_positive = sum(p and a for p, a in zip(predicted, actual, strict=True))
        true_negative = sum(not p and not a for p, a in zip(predicted, actual, strict=True))
        false_positive = sum(p and not a for p, a in zip(predicted, actual, strict=True))
        false_negative = sum(not p and a for p, a in zip(predicted, actual, strict=True))
        total = len(actual)
        negatives = false_positive + true_negative
        positives = false_negative + true_positive
        accuracy = (true_positive + true_negative) / total
        return cls(
            accuracy=accuracy,
            false_positive_rate=false_positive / negatives if negatives else 0.0,
            false_negative_rate=false_negative / positives if positives else 0.0,
            agreement=accuracy,
        )

    @property
    def calibrated(self) -> bool:
        return (
            self.accuracy >= 0.8
            and self.false_positive_rate <= 0.2
            and self.false_negative_rate <= 0.2
        )
