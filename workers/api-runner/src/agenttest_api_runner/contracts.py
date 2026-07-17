from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

REDACTED_SECRET = "[REDACTED]"
_SENSITIVE_KEYS = frozenset(
    {
        "api_key",
        "authorization",
        "cookie",
        "credentials",
        "password",
        "passwd",
        "proxy_authorization",
        "secret",
        "secret_key",
        "set_cookie",
        "token",
        "x_api_key",
    }
)
_SENSITIVE_SUFFIXES = (
    "_api_key",
    "_cookie",
    "_credential",
    "_password",
    "_passwd",
    "_secret",
    "_token",
)
_SENSITIVE_COLLAPSED_KEYS = frozenset(key.replace("_", "") for key in _SENSITIVE_KEYS)
_SENSITIVE_COLLAPSED_SUFFIXES = tuple(
    suffix.removeprefix("_").replace("_", "") for suffix in _SENSITIVE_SUFFIXES
)


@dataclass(frozen=True, slots=True)
class PlatformTestCaseSnapshotV1:
    schema_version: str
    case_key: str | None
    objective: str
    preconditions: list[str]
    initial_state: dict[str, Any] | None
    input: dict[str, Any]
    data_bindings: list[dict[str, Any]]
    steps: list[dict[str, Any]]
    expected_outcome: dict[str, Any] | None
    assertions: list[dict[str, Any]]
    scorers: list[dict[str, Any]]
    security_policies: list[dict[str, Any]]
    artifact_requirements: list[dict[str, Any]]
    postconditions: list[str]
    execution_mode: str
    timeout_seconds: int | None
    retry_count: int

    @classmethod
    def from_payload(cls, raw: dict[str, Any]) -> PlatformTestCaseSnapshotV1:
        if raw.get("schema_version") != "platform-test-case/v1":
            raise ValueError("Unsupported case_spec schema_version")
        bindings = _object_list(raw.get("data_bindings", []), "data_bindings")
        for binding in bindings:
            if (binding.get("sensitive") or binding.get("source") == "credential") and (
                "value" in binding
            ):
                raise ValueError("Credential binding snapshot must not contain a value")
        if _contains_unredacted_sensitive_field(raw):
            raise ValueError("Professional case snapshot contains sensitive fields")
        return cls(
            schema_version="platform-test-case/v1",
            case_key=str(raw["case_key"]) if raw.get("case_key") else None,
            objective=str(raw.get("objective") or "").strip(),
            preconditions=_string_list(raw.get("preconditions", []), "preconditions"),
            initial_state=(
                dict(raw["initial_state"]) if isinstance(raw.get("initial_state"), dict) else None
            ),
            input=_object(raw.get("input", {}), "input"),
            data_bindings=bindings,
            steps=_object_list(raw.get("steps", []), "steps"),
            expected_outcome=(
                dict(raw["expected_outcome"])
                if isinstance(raw.get("expected_outcome"), dict)
                else None
            ),
            assertions=_object_list(raw.get("assertions", []), "assertions"),
            scorers=_object_list(raw.get("scorers", []), "scorers"),
            security_policies=_object_list(raw.get("security_policies", []), "security_policies"),
            artifact_requirements=_object_list(
                raw.get("artifact_requirements", []), "artifact_requirements"
            ),
            postconditions=_string_list(raw.get("postconditions", []), "postconditions"),
            execution_mode=str(raw.get("execution_mode") or "api"),
            timeout_seconds=(
                int(raw["timeout_seconds"]) if isinstance(raw.get("timeout_seconds"), int) else None
            ),
            retry_count=int(raw.get("retry_count", 0)),
        )

    @property
    def executable_assertions(self) -> list[dict[str, Any]]:
        return [
            *self.assertions,
            *[
                dict(assertion)
                for step in self.steps
                for assertion in _object_list(step.get("assertions", []), "step.assertions")
            ],
        ]


@dataclass(frozen=True, slots=True)
class ResultCallbackConfig:
    base_url: str
    internal_token: str
    project_id: str


@dataclass(frozen=True, slots=True)
class RunCaseTask:
    run_case_id: str
    input: dict[str, Any]
    assertions: list[dict[str, Any]]
    execution_mode: str = "api"
    case_spec: PlatformTestCaseSnapshotV1 | None = None


@dataclass(frozen=True, slots=True)
class RunTask:
    run_id: str
    idempotency_key: str
    cases: list[RunCaseTask]
    agent_config: dict[str, Any]
    agent_type: str = "generic_http"
    environment: dict[str, Any] = field(default_factory=dict)
    execution_policy: dict[str, Any] = field(default_factory=dict)
    scorer_configs: list[dict[str, Any]] = field(default_factory=list)
    browser_profile_snapshot: dict[str, Any] = field(default_factory=dict)
    callback: ResultCallbackConfig | None = None


@dataclass(frozen=True, slots=True)
class ReportArtifact:
    name: str
    content_type: str
    content: str


@dataclass(frozen=True, slots=True)
class CaseScore:
    scorer_version_id: str
    scorer_type: str
    score: float
    passed: bool
    explanation: str = ""
    confidence: float = 1.0


@dataclass(frozen=True, slots=True)
class RunCaseResult:
    run_case_id: str
    status: str
    output: dict[str, Any] | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)
    error_type: str | None = None
    error_message: str | None = None
    duration_ms: int | None = None
    scores: list[CaseScore] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RunResult:
    run_id: str
    status: str
    cases: list[RunCaseResult]
    reports: list[ReportArtifact] = field(default_factory=list)


def _object(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object")
    return dict(value)


def _object_list(value: Any, field_name: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"{field_name} must be a list of objects")
    return [dict(item) for item in value]


def _string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a list of strings")
    return list(value)


def _contains_unredacted_sensitive_field(value: object) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = "".join(
                character if character.isalnum() else "_" for character in str(key).lower()
            ).strip("_")
            collapsed = normalized.replace("_", "")
            if (
                normalized in _SENSITIVE_KEYS
                or normalized.endswith(_SENSITIVE_SUFFIXES)
                or collapsed in _SENSITIVE_COLLAPSED_KEYS
                or collapsed.endswith(_SENSITIVE_COLLAPSED_SUFFIXES)
            ) and item != REDACTED_SECRET:
                return True
            if _contains_unredacted_sensitive_field(item):
                return True
        return False
    if isinstance(value, list | tuple):
        return any(_contains_unredacted_sensitive_field(item) for item in value)
    return False
