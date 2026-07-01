"""数据集导入/导出应用服务。

支持 JSON、JSONL、CSV 三种格式的导入导出。
导入采用全量或全无策略——任一行出错则整体回滚，
并报告每行的错误详情。
"""

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
MAX_IMPORT_BYTES = 10 * 1024 * 1024


class ImportError(Exception):
    """导入失败异常，包含每行的错误详情列表。"""

    def __init__(self, errors: list[dict[str, object]]) -> None:
        self.errors = errors
        super().__init__(f"Import failed with {len(errors)} error(s)")


class ImportExportService:
    """数据集的导入导出应用服务。

    支持 JSON/JSONL/CSV 导入和 JSON/JSONL/CSV 导出。
    导入为全量或全无——任一错误即回滚全部已导入用例。
    """

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

        validated = parse_and_validate_import(format, content)
        parsed = validated["records"]
        if not isinstance(parsed, list):
            raise ValueError("Import parser returned an invalid result")

        errors: list[dict[str, object]] = []
        cases: list[TestCase] = []
        max_order = await self._cases.get_max_sort_order(version.version_id)

        for idx, raw in enumerate(parsed):
            if not isinstance(raw, dict):
                continue
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

    async def preview_test_cases(
        self,
        *,
        actor: User,
        dataset: Dataset,
        version: DatasetVersion,
        format: str,
        content: str,
    ) -> dict[str, object]:
        if not version.is_editable:
            raise ValueError("Cannot import into a published version")
        await self._project_access.ensure_editor(actor, dataset.project_id)
        result = parse_and_validate_import(format, content, allow_errors=True)
        return {key: value for key, value in result.items() if key != "records"}

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
    "assertions",
    "scorers",
    "initial_state",
    "expected_outcome",
    "security_policies",
    "tags",
    "scenario",
    "priority",
    "risk_level",
    "difficulty",
    "test_group",
    "sort_order",
}


def parse_and_validate_import(
    format: str,
    content: str,
    *,
    allow_errors: bool = False,
) -> dict[str, object]:
    if len(content.encode("utf-8")) > MAX_IMPORT_BYTES:
        raise ValueError("Import file exceeds the 10MB limit")
    parsed: list[object]
    if format == "json":
        parsed = _parse_json(content)
    elif format == "jsonl":
        parsed = _parse_jsonl(content)
    elif format == "csv":
        parsed = list(_parse_csv(content))
    else:
        raise ValueError(f"Unsupported import format: {format}")

    records: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    for index, item in enumerate(parsed, start=1):
        if not isinstance(item, dict):
            errors.append(_import_error(index, "$", "invalid_type", "test case must be an object"))
            continue
        item_errors = _validate_import_record(index, item)
        if item_errors:
            errors.extend(item_errors)
        else:
            records.append(item)
    if errors and not allow_errors:
        raise ImportError(errors)
    return {
        "valid_count": len(records),
        "errors": errors,
        "preview": records[:20],
        "records": records,
    }


def _validate_import_record(line: int, raw: dict[str, object]) -> list[dict[str, object]]:
    errors: list[dict[str, object]] = []
    missing = _REQUIRED_FIELDS - set(raw)
    for field_name in sorted(missing):
        errors.append(_import_error(line, field_name, "required", f"{field_name} is required"))
    unknown = set(raw) - _REQUIRED_FIELDS - _OPTIONAL_FIELDS
    for field_name in sorted(unknown):
        errors.append(_import_error(line, field_name, "unknown_field", "field is not supported"))
    if "name" in raw and (not isinstance(raw["name"], str) or not raw["name"].strip()):
        errors.append(_import_error(line, "name", "invalid_value", "name must be non-empty"))
    if "input" in raw and not isinstance(raw["input"], dict):
        errors.append(_import_error(line, "input", "invalid_type", "input must be a JSON object"))
    if "execution_mode" in raw:
        try:
            ExecutionMode(str(raw["execution_mode"]))
        except ValueError:
            errors.append(
                _import_error(
                    line,
                    "execution_mode",
                    "invalid_enum",
                    "execution_mode must be api, browser, canvas, or hybrid",
                )
            )
    for field_name in ("assertions", "scorers", "security_policies"):
        value = raw.get(field_name)
        if value is not None and (
            not isinstance(value, list) or not all(isinstance(item, dict) for item in value)
        ):
            errors.append(
                _import_error(
                    line, field_name, "invalid_type", f"{field_name} must be a list of objects"
                )
            )
    for field_name in ("initial_state", "expected_outcome"):
        value = raw.get(field_name)
        if value is not None and not isinstance(value, dict):
            errors.append(
                _import_error(line, field_name, "invalid_type", f"{field_name} must be an object")
            )
    tags = raw.get("tags")
    if tags is not None and (
        not isinstance(tags, list) or not all(isinstance(item, str) for item in tags)
    ):
        errors.append(_import_error(line, "tags", "invalid_type", "tags must be a list of strings"))
    return errors


def _import_error(line: int, field: str, code: str, message: str) -> dict[str, object]:
    return {"line": line, "field": field, "code": code, "message": message}


def _parse_json(content: str) -> list[object]:
    data = json.loads(content)
    if not isinstance(data, list):
        raise ValueError("JSON content must be an array of test case objects")
    return data


def _parse_jsonl(content: str) -> list[object]:
    records: list[object] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSONL at line {line_number}: {error.msg}") from error
    return records


def _parse_csv(content: str) -> list[dict[str, object]]:
    reader = csv.DictReader(StringIO(content))
    records: list[dict[str, object]] = []
    for row in reader:
        record: dict[str, object] = {}
        for key, value in row.items():
            if key in (
                "input",
                "initial_state",
                "expected_outcome",
                "assertions",
                "scorers",
                "security_policies",
                "tags",
            ):
                try:
                    record[key] = json.loads(value) if value else []
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON in field '{key}': {value}") from exc
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
        raise ValueError(f"Invalid execution_mode: {execution_mode_raw}") from exc

    priority = None
    if raw.get("priority"):
        try:
            priority = Priority(str(raw["priority"]))
        except ValueError as exc:
            raise ValueError(f"Invalid priority: {raw['priority']}") from exc

    risk_level = None
    if raw.get("risk_level"):
        try:
            risk_level = RiskLevel(str(raw["risk_level"]))
        except ValueError as exc:
            raise ValueError(f"Invalid risk_level: {raw['risk_level']}") from exc

    test_group = None
    if raw.get("test_group"):
        try:
            test_group = TestGroup(str(raw["test_group"]))
        except ValueError as exc:
            raise ValueError(f"Invalid test_group: {raw['test_group']}") from exc

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
