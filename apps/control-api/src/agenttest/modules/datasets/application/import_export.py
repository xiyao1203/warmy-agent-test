"""Dataset import / export application service."""

from __future__ import annotations

import csv
import json
from io import StringIO
from typing import Literal

from agenttest.modules.datasets.application.ports import ProjectAccessPort
from agenttest.modules.datasets.domain.entities import (
    Dataset,
    DatasetVersion,
    TestCase,
    TestCaseId,
)
from agenttest.modules.datasets.domain.repositories import TestCaseRepository
from agenttest.modules.datasets.domain.value_objects import (
    ExecutionMode,
    Priority,
    RiskLevel,
    TestGroup,
)
from agenttest.modules.identity.public import User

ExportFormat = Literal["json", "jsonl", "csv"]


class ImportError(Exception):
    """Import failure with structured error details."""

    def __init__(self, errors: list[dict[str, object]]) -> None:
        self.errors = errors
        super().__init__(f"Import failed with {len(errors)} error(s)")


class ImportExportService:
    def __init__(
        self,
        *,
        cases: TestCaseRepository,
        project_access: ProjectAccessPort,
    ) -> None:
        self._cases = cases
        self._project_access = project_access

    # ── Import ────────────────────────────────────────────────────────────

    async def import_test_cases(
        self,
        *,
        actor: User,
        dataset: Dataset,
        version: DatasetVersion,
        format: str,
        content: str,
    ) -> list[TestCase]:
        """Import test cases from a string in the specified format.

        All-or-nothing: on any error the entire import is rolled back.
        """
        if not version.is_editable:
            raise ValueError("Cannot import into a published version")

        await self._project_access.ensure_editor(actor, dataset.project_id)

        if format == "json":
            parsed = _parse_json(content)
        elif format == "jsonl":
            parsed = _parse_jsonl(content)
        elif format == "csv":
            parsed = _parse_csv(content)
        else:
            raise ValueError(f"Unsupported import format: {format}")

        errors: list[dict[str, object]] = []
        cases: list[TestCase] = []
        max_order = await self._cases.get_max_sort_order(version.version_id)

        for idx, raw in enumerate(parsed):
            try:
                case = _build_test_case(version.version_id, raw, sort_order=max_order + idx + 1)
                cases.append(case)
            except ValueError as exc:
                errors.append({"line": idx + 1, "reason": str(exc)})

        if errors:
            raise ImportError(errors)

        for case in cases:
            await self._cases.add(case)

        return cases

    # ── Export ────────────────────────────────────────────────────────────

    async def export_test_cases(
        self,
        *,
        version: DatasetVersion,
        format: ExportFormat,
    ) -> str:
        """Export all test cases in a version to the specified format."""
        cases, _ = await self._cases.list_by_version(version.version_id, limit=10000)

        records = [_case_to_dict(c) for c in cases]

        if format == "json":
            return json.dumps(records, ensure_ascii=False, indent=2, default=str)
        elif format == "jsonl":
            return "\n".join(json.dumps(r, ensure_ascii=False, default=str) for r in records) + "\n"
        elif format == "csv":
            if not records:
                return ""
            output = StringIO()
            fieldnames = list(records[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for r in records:
                writer.writerow({k: _csv_value(v) for k, v in r.items()})
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")


# ── Parsers ──────────────────────────────────────────────────────────────────


_REQUIRED_FIELDS = {"name", "input", "execution_mode"}
_OPTIONAL_FIELDS = {
    "assertions", "scorers", "initial_state", "expected_outcome",
    "security_policies", "tags", "scenario", "priority",
    "risk_level", "difficulty", "test_group", "sort_order",
}


def _parse_json(content: str) -> list[dict[str, object]]:
    data = json.loads(content)
    if not isinstance(data, list):
        raise ValueError("JSON content must be an array of test case objects")
    return data


def _parse_jsonl(content: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for line in content.strip().split("\n"):
        if not line.strip():
            continue
        records.append(json.loads(line))
    return records


def _parse_csv(content: str) -> list[dict[str, object]]:
    reader = csv.DictReader(StringIO(content))
    records: list[dict[str, object]] = []
    for row in reader:
        record: dict[str, object] = {}
        for key, value in row.items():
            if key in ("input", "initial_state", "expected_outcome", "assertions",
                       "scorers", "security_policies", "tags"):
                try:
                    record[key] = json.loads(value) if value else []
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid JSON in field '{key}': {value}"
                    ) from exc
            else:
                record[key] = value
        records.append(record)
    return records


def _build_test_case(
    version_id: object,
    raw: dict[str, object],
    sort_order: int,
) -> TestCase:
    missing = _REQUIRED_FIELDS - set(raw.keys())
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(sorted(missing))}")

    name = str(raw.get("name", ""))
    if not name.strip():
        raise ValueError("name is required")

    execution_mode_raw = str(raw["execution_mode"])
    try:
        execution_mode = ExecutionMode(execution_mode_raw)
    except ValueError as exc:
        raise ValueError(
            f"Invalid execution_mode: {execution_mode_raw}"
        ) from exc

    priority = None
    if raw.get("priority"):
        try:
            priority = Priority(str(raw["priority"]))
        except ValueError as exc:
            raise ValueError(
                f"Invalid priority: {raw['priority']}"
            ) from exc

    risk_level = None
    if raw.get("risk_level"):
        try:
            risk_level = RiskLevel(str(raw["risk_level"]))
        except ValueError as exc:
            raise ValueError(
                f"Invalid risk_level: {raw['risk_level']}"
            ) from exc

    test_group = None
    if raw.get("test_group"):
        try:
            test_group = TestGroup(str(raw["test_group"]))
        except ValueError as exc:
            raise ValueError(
                f"Invalid test_group: {raw['test_group']}"
            ) from exc

    return TestCase.create(
        case_id=TestCaseId.new(),
        dataset_version_id=version_id,  # type: ignore[arg-type]
        name=name,
        input=raw["input"] if isinstance(raw["input"], dict) else {},
        execution_mode=execution_mode,
        assertions=_as_list(raw.get("assertions")),
        scorers=_as_list(raw.get("scorers")),
        initial_state=_as_dict(raw.get("initial_state")),
        expected_outcome=_as_dict(raw.get("expected_outcome")),
        security_policies=_as_list(raw.get("security_policies")),
        tags=_as_str_list(raw.get("tags")),
        scenario=str(raw["scenario"]) if raw.get("scenario") else None,
        priority=priority,
        risk_level=risk_level,
        difficulty=str(raw["difficulty"]) if raw.get("difficulty") else None,
        test_group=test_group,
        sort_order=sort_order,
    )


def _as_list(value: object) -> list[dict[str, object]] | None:
    return value if isinstance(value, list) else None  # type: ignore[return-value]


def _as_dict(value: object) -> dict[str, object] | None:
    return value if isinstance(value, dict) else None  # type: ignore[return-value]


def _as_str_list(value: object) -> list[str] | None:
    return value if isinstance(value, list) else None  # type: ignore[return-value]


def _case_to_dict(case: TestCase) -> dict[str, object]:
    return {
        "name": case.name,
        "input": case.input,
        "execution_mode": case.execution_mode.value,
        "assertions": case.assertions,
        "scorers": case.scorers,
        "initial_state": case.initial_state,
        "expected_outcome": case.expected_outcome,
        "security_policies": case.security_policies,
        "tags": case.tags,
        "scenario": case.scenario,
        "priority": case.priority.value if case.priority else None,
        "risk_level": case.risk_level.value if case.risk_level else None,
        "difficulty": case.difficulty,
        "test_group": case.test_group.value if case.test_group else None,
        "sort_order": case.sort_order,
    }


def _csv_value(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)
