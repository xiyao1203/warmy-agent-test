from __future__ import annotations

from enum import StrEnum


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self in {
            RunStatus.PASSED,
            RunStatus.FAILED,
            RunStatus.ERROR,
            RunStatus.CANCELLED,
        }


class RunCaseStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self in {
            RunCaseStatus.PASSED,
            RunCaseStatus.FAILED,
            RunCaseStatus.ERROR,
            RunCaseStatus.CANCELLED,
        }


class RunErrorType(StrEnum):
    VALIDATION = "ValidationError"
    PERMISSION = "PermissionError"
    ENVIRONMENT = "EnvironmentError"
    TARGET_PRODUCT = "TargetProductError"
    TRANSIENT = "TransientError"
    PLATFORM = "PlatformError"
    CANCELLED = "CancelledError"

