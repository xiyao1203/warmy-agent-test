"""Unit tests for dataset domain entities and import/export."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from agenttest.modules.datasets.application.import_export import (
    ImportError,
    ImportExportService,
    _build_test_case,
)
from agenttest.modules.datasets.domain.entities import (
    Dataset,
    DatasetId,
    DatasetVersion,
    DatasetVersionId,
    TestCase,
    TestCaseId,
)
from agenttest.modules.datasets.domain.value_objects import (
    ExecutionMode,
    Priority,
    RiskLevel,
    TestGroup,
    VersionStatus,
)
from agenttest.modules.identity.public import Email, SystemRole, User, UserId
from agenttest.modules.projects.public import ProjectId

# ── Helpers ────────────────────────────────────────────────────────────────


def _make_project_id() -> ProjectId:
    return ProjectId(uuid4())


def _make_dataset_id() -> DatasetId:
    return DatasetId(uuid4())


def _make_version_id() -> DatasetVersionId:
    return DatasetVersionId(uuid4())


def _make_user() -> User:
    return User.create(
        user_id=UserId.new(),
        email=Email("dev@example.com"),
        display_name="Dev",
        role=SystemRole.DEVELOPER,
    )


# ── Dataset ────────────────────────────────────────────────────────────────


def test_dataset_requires_name() -> None:
    with pytest.raises(ValueError, match="Dataset name is required"):
        Dataset.create(
            dataset_id=_make_dataset_id(),
            project_id=_make_project_id(),
            name="   ",
            created_by=_make_user().user_id,
        )


def test_dataset_create() -> None:
    project_id = _make_project_id()
    ds = Dataset.create(
        dataset_id=_make_dataset_id(),
        project_id=project_id,
        name="My Dataset",
        created_by=_make_user().user_id,
    )
    assert ds.project_id == project_id
    assert ds.name == "My Dataset"


def test_dataset_rename() -> None:
    ds = Dataset.create(
        dataset_id=_make_dataset_id(),
        project_id=_make_project_id(),
        name="Old",
        created_by=_make_user().user_id,
    )
    ds.rename("New")
    assert ds.name == "New"

    with pytest.raises(ValueError, match="Dataset name is required"):
        ds.rename("")


# ── DatasetVersion ─────────────────────────────────────────────────────────


def test_version_starts_as_draft() -> None:
    version = DatasetVersion.create_draft(
        version_id=_make_version_id(),
        dataset_id=_make_dataset_id(),
        version_number=1,
        created_by=_make_user().user_id,
    )
    assert version.is_editable is True
    assert version.status is VersionStatus.DRAFT


def test_version_publish() -> None:
    version = DatasetVersion.create_draft(
        version_id=_make_version_id(),
        dataset_id=_make_dataset_id(),
        version_number=1,
        created_by=_make_user().user_id,
    )
    version.publish()
    assert version.is_published is True
    assert version.is_editable is False
    assert version.published_at is not None

    with pytest.raises(ValueError, match="already published"):
        version.publish()


# ── TestCase ───────────────────────────────────────────────────────────────


def test_test_case_create() -> None:
    case = TestCase.create(
        case_id=TestCaseId(uuid4()),
        dataset_version_id=_make_version_id(),
        name="Test 1",
        input={"prompt": "Hello"},
        execution_mode=ExecutionMode.API,
        assertions=[{"type": "contains", "value": "world"}],
        tags=["smoke"],
        priority=Priority.P1,
        test_group=TestGroup.TEST,
    )
    assert case.name == "Test 1"
    assert case.input == {"prompt": "Hello"}
    assert case.execution_mode is ExecutionMode.API
    assert len(case.assertions) == 1
    assert case.tags == ["smoke"]
    assert case.priority is Priority.P1
    assert case.test_group is TestGroup.TEST
    assert case.sort_order == 0


def test_test_case_requires_name() -> None:
    with pytest.raises(ValueError, match="Test case name is required"):
        TestCase.create(
            case_id=TestCaseId(uuid4()),
            dataset_version_id=_make_version_id(),
            name="",
            input={"key": "val"},
            execution_mode=ExecutionMode.API,
        )


def test_test_case_requires_input() -> None:
    with pytest.raises(ValueError, match="Test case input is required"):
        TestCase.create(
            case_id=TestCaseId(uuid4()),
            dataset_version_id=_make_version_id(),
            name="Test",
            input={},
            execution_mode=ExecutionMode.API,
        )


def test_test_case_update() -> None:
    case = TestCase.create(
        case_id=TestCaseId(uuid4()),
        dataset_version_id=_make_version_id(),
        name="Test 1",
        input={"prompt": "Hello"},
        execution_mode=ExecutionMode.API,
    )
    case.update(name="Updated", sort_order=5)
    assert case.name == "Updated"
    assert case.sort_order == 5


# ── Import / Export ────────────────────────────────────────────────────────


def test_build_test_case_from_dict() -> None:
    raw: dict[str, object] = {
        "name": "My Test",
        "input": {"prompt": "hi"},
        "execution_mode": "api",
        "assertions": [{"type": "eq"}],
        "priority": "P0",
        "risk_level": "high",
        "test_group": "train",
    }
    case = _build_test_case(_make_version_id(), raw, sort_order=0)
    assert case.name == "My Test"
    assert case.execution_mode is ExecutionMode.API
    assert case.priority is Priority.P0
    assert case.risk_level is RiskLevel.HIGH
    assert case.test_group is TestGroup.TRAIN


def test_build_test_case_missing_required() -> None:
    raw: dict[str, object] = {"name": "Test"}
    with pytest.raises(ValueError, match="Missing required fields"):
        _build_test_case(_make_version_id(), raw, sort_order=0)


def test_import_json_parse_errors() -> None:
    content = json.dumps(
        [
            {"name": "OK", "input": {"x": 1}, "execution_mode": "api"},
            {"name": "", "input": {"x": 1}, "execution_mode": "api"},
        ]
    )
    with pytest.raises(ImportError) as exc_info:
        _parse_json_and_build(content, "json")
    errors = exc_info.value.errors
    assert len(errors) == 1
    assert errors[0]["line"] == 2


def test_import_json_invalid_enum() -> None:
    content = json.dumps(
        [
            {"name": "Test", "input": {"x": 1}, "execution_mode": "invalid_mode"},
        ]
    )
    with pytest.raises(ImportError) as exc_info:
        _parse_json_and_build(content, "json")
    assert len(exc_info.value.errors) == 1


def test_export_to_json() -> None:
    from agenttest.modules.datasets.application.import_export import (
        _case_to_dict,
    )

    case = TestCase.create(
        case_id=TestCaseId(uuid4()),
        dataset_version_id=_make_version_id(),
        name="Export Test",
        input={"q": "?"},
        execution_mode=ExecutionMode.BROWSER,
        assertions=[{"type": "ok"}],
        scorers=[{"name": "exact"}],
        tags=["export"],
        priority=Priority.P2,
    )
    d = _case_to_dict(case)
    assert d["name"] == "Export Test"
    assert d["execution_mode"] == "browser"
    assert d["tags"] == ["export"]
    assert d["priority"] == "P2"


# ── Helpers ────────────────────────────────────────────────────────────────


def _parse_json_and_build(content: str, format: str) -> None:
    """Helper that mirrors ImportExportService.import_test_cases logic."""
    from agenttest.modules.datasets.application.import_export import (
        _parse_json,
    )

    parsed = _parse_json(content)
    errors: list[dict[str, object]] = []
    for idx, raw in enumerate(parsed):
        try:
            _build_test_case(_make_version_id(), raw, sort_order=idx + 1)
        except ValueError as exc:
            errors.append({"line": idx + 1, "reason": str(exc)})
    if errors:
        raise ImportError(errors)
