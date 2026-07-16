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
from uuid import uuid4

from pydantic import ValidationError

from agenttest.modules.datasets.application.contracts import PlatformTestCaseV1
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
    TestCaseSource,
    TestGroup,
)
from agenttest.modules.identity.public import User, UserId
from agenttest.modules.projects.public import ProjectAssetKeyAllocator

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
        case_key_allocator: ProjectAssetKeyAllocator | None = None,
    ) -> None:
        self._cases = cases
        self._project_access = project_access
        self._case_key_allocator = case_key_allocator

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
        import_ref = f"import:{uuid4()}"

        for idx, raw in enumerate(parsed):
            if not isinstance(raw, dict):
                continue
            try:
                case = _build_test_case(version.version_id, raw, sort_order=max_order + idx + 1)
                if case.owner_id is not None:
                    await self._project_access.ensure_user_member(
                        case.owner_id,
                        dataset.project_id,
                    )
                case.case_key = await self._allocate_case_key(dataset)
                case.source_ref = import_ref
                case.created_by = actor.user_id
                case.updated_by = actor.user_id
                cases.append(case)
            except ValueError as exc:
                errors.append({"line": idx + 1, "reason": str(exc)})

        if errors:
            raise ImportError(errors)

        for case in cases:
            await self._cases.add(case)

        return cases

    async def _allocate_case_key(self, dataset: Dataset) -> str:
        if self._case_key_allocator is not None:
            return await self._case_key_allocator.allocate(
                dataset.project_id,
                "test_case",
                "TC",
            )
        return f"TC-{TestCaseId.new().value.hex[:12].upper()}"

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
    "case_key",
    "case_status",
    "source",
    "objective",
    "template",
    "case_type",
    "automation_status",
    "source_ref",
    "component",
    "requirement_refs",
    "owner_id",
    "preconditions",
    "data_bindings",
    "steps",
    "assertions",
    "scorers",
    "initial_state",
    "expected_outcome",
    "security_policies",
    "artifact_requirements",
    "postconditions",
    "estimated_duration_seconds",
    "timeout_seconds",
    "retry_count",
    "custom_fields",
    "tags",
    "scenario",
    "priority",
    "risk_level",
    "difficulty",
    "test_group",
    "sort_order",
}

_FIELD_ALIASES = {
    "用例名称": "name",
    "名称": "name",
    "输入": "input",
    "输入数据": "input",
    "测试目标": "objective",
    "目标": "objective",
    "用例模板": "template",
    "模板": "template",
    "用例类型": "case_type",
    "自动化状态": "automation_status",
    "来源引用": "source_ref",
    "所属组件": "component",
    "组件": "component",
    "关联需求": "requirement_refs",
    "负责人": "owner_id",
    "前置条件": "preconditions",
    "数据绑定": "data_bindings",
    "操作步骤": "steps",
    "步骤": "steps",
    "执行模式": "execution_mode",
    "模式": "execution_mode",
    "初始状态": "initial_state",
    "初始业务状态": "initial_state",
    "期望结果": "expected_outcome",
    "预期结果": "expected_outcome",
    "断言规则": "assertions",
    "断言": "assertions",
    "评分器": "scorers",
    "评分规则": "scorers",
    "安全策略": "security_policies",
    "安全规则": "security_policies",
    "产物要求": "artifact_requirements",
    "后置条件": "postconditions",
    "预计耗时": "estimated_duration_seconds",
    "超时秒数": "timeout_seconds",
    "重试次数": "retry_count",
    "扩展字段": "custom_fields",
    "标签": "tags",
    "业务场景": "scenario",
    "场景": "scenario",
    "优先级": "priority",
    "风险等级": "risk_level",
    "风险": "risk_level",
    "难度": "difficulty",
    "测试分组": "test_group",
    "分组": "test_group",
}

_EXECUTION_MODE_ALIASES = {
    "API": ExecutionMode.API.value,
    "API测试": ExecutionMode.API.value,
    "接口": ExecutionMode.API.value,
    "接口测试": ExecutionMode.API.value,
    "浏览器": ExecutionMode.BROWSER.value,
    "浏览器测试": ExecutionMode.BROWSER.value,
    "E2E": ExecutionMode.BROWSER.value,
    "端到端": ExecutionMode.BROWSER.value,
}

_RISK_LEVEL_ALIASES = {
    "严重": RiskLevel.CRITICAL.value,
    "致命": RiskLevel.CRITICAL.value,
    "高": RiskLevel.HIGH.value,
    "高风险": RiskLevel.HIGH.value,
    "中": RiskLevel.MEDIUM.value,
    "中风险": RiskLevel.MEDIUM.value,
    "低": RiskLevel.LOW.value,
    "低风险": RiskLevel.LOW.value,
}

_PRIORITY_ALIASES = {
    "最高": Priority.P0.value,
    "紧急": Priority.P0.value,
    "高": Priority.P1.value,
    "中": Priority.P2.value,
    "低": Priority.P3.value,
}

_TEST_GROUP_ALIASES = {
    "训练": TestGroup.TRAIN.value,
    "训练集": TestGroup.TRAIN.value,
    "验证": TestGroup.VALIDATION.value,
    "验证集": TestGroup.VALIDATION.value,
    "测试": TestGroup.TEST.value,
    "测试集": TestGroup.TEST.value,
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
        normalized_item = _normalize_import_record(item)
        item_errors = _validate_import_record(index, normalized_item)
        if item_errors:
            errors.extend(item_errors)
        else:
            records.append(normalized_item)
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
                    "execution_mode must be api, browser or codex_explore",
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
    for field_name, enum_cls, valid_values in (
        ("priority", Priority, [p.value for p in Priority]),
        ("risk_level", RiskLevel, [r.value for r in RiskLevel]),
        ("test_group", TestGroup, [g.value for g in TestGroup]),
    ):
        value = raw.get(field_name)
        if value is not None:
            try:
                enum_cls(str(value))
            except ValueError:
                errors.append(
                    _import_error(
                        line,
                        field_name,
                        "invalid_enum",
                        f"{field_name} must be one of: {', '.join(valid_values)}",
                    )
                )
    if not errors:
        try:
            _validate_professional_record(raw)
        except ValidationError as error:
            for detail in error.errors(include_url=False):
                location = detail.get("loc", ())
                field = ".".join(str(part) for part in location) or "$"
                errors.append(
                    _import_error(
                        line,
                        field,
                        str(detail.get("type", "invalid_value")),
                        str(detail.get("msg", "invalid value")),
                    )
                )
    return errors


def _validate_professional_record(raw: dict[str, object]) -> PlatformTestCaseV1:
    payload = {
        key: value
        for key, value in raw.items()
        if key not in {"sort_order", "case_key", "case_status", "source"}
    }
    payload.setdefault("objective", payload.get("name"))
    payload["source"] = TestCaseSource.IMPORTED
    return PlatformTestCaseV1.model_validate(payload)


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
            normalized_key = _normalize_field_name(key)
            if normalized_key in (
                "input",
                "initial_state",
                "expected_outcome",
                "requirement_refs",
                "preconditions",
                "data_bindings",
                "steps",
                "assertions",
                "scorers",
                "security_policies",
                "artifact_requirements",
                "postconditions",
                "custom_fields",
                "tags",
            ):
                try:
                    record[normalized_key] = (
                        json.loads(value) if value else _empty_csv_value(normalized_key)
                    )
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON in field '{key}': {value}") from exc
            else:
                record[normalized_key] = _parse_csv_scalar(normalized_key, value)
        records.append(record)
    return records


def _normalize_import_record(raw: dict[str, object]) -> dict[str, object]:
    record: dict[str, object] = {}
    for field_name, value in raw.items():
        normalized_name = _normalize_field_name(field_name)
        record[normalized_name] = _normalize_field_value(normalized_name, value)
    return record


def _normalize_field_name(field_name: object) -> str:
    name = str(field_name).strip()
    return _FIELD_ALIASES.get(name, name)


def _normalize_field_value(field_name: str, value: object) -> object:
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if field_name == "execution_mode":
        return _EXECUTION_MODE_ALIASES.get(stripped, stripped.lower())
    if field_name == "risk_level":
        return _RISK_LEVEL_ALIASES.get(stripped, stripped.lower())
    if field_name == "priority":
        return _PRIORITY_ALIASES.get(stripped, stripped.upper())
    if field_name == "test_group":
        return _TEST_GROUP_ALIASES.get(stripped, stripped.lower())
    if field_name in {"template", "case_type", "automation_status"}:
        return stripped.lower()
    if field_name == "difficulty":
        return {"简单": "easy", "中等": "medium", "困难": "hard"}.get(stripped, stripped)
    return value


def _empty_csv_value(field_name: str) -> object:
    if field_name in {"input", "initial_state", "expected_outcome", "custom_fields"}:
        return {}
    return []


def _parse_csv_scalar(field_name: str, value: str) -> object:
    if field_name in {
        "estimated_duration_seconds",
        "timeout_seconds",
        "retry_count",
        "sort_order",
    }:
        if not value.strip():
            return None if field_name != "retry_count" else 0
        try:
            return int(value)
        except ValueError as error:
            raise ValueError(f"Invalid integer in field '{field_name}': {value}") from error
    return value


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

    input_value = raw.get("input")
    if not isinstance(input_value, dict):
        raise ValueError("input must be a JSON object")

    try:
        contract = _validate_professional_record(raw)
    except ValidationError as error:
        first = error.errors(include_url=False)[0]
        raise ValueError(str(first.get("msg", "invalid test case"))) from error

    return TestCase.create(
        case_id=TestCaseId.new(),
        dataset_version_id=version_id,  # type: ignore[arg-type]
        name=contract.name,
        objective=contract.objective,
        template=contract.template,
        case_type=contract.case_type,
        automation_status=contract.automation_status,
        source=contract.source,
        source_ref=contract.source_ref,
        component=contract.component,
        requirement_refs=contract.requirement_refs,
        owner_id=UserId(contract.owner_id) if contract.owner_id else None,
        preconditions=contract.preconditions,
        input=contract.input,
        data_bindings=[item.model_dump(mode="json") for item in contract.data_bindings],
        steps=[item.model_dump(mode="json") for item in contract.steps],
        execution_mode=contract.execution_mode,
        assertions=contract.assertions,
        scorers=contract.scorers,
        initial_state=contract.initial_state,
        expected_outcome=contract.expected_outcome,
        security_policies=contract.security_policies,
        artifact_requirements=[
            item.model_dump(mode="json") for item in contract.artifact_requirements
        ],
        postconditions=contract.postconditions,
        estimated_duration_seconds=contract.estimated_duration_seconds,
        timeout_seconds=contract.timeout_seconds,
        retry_count=contract.retry_count,
        custom_fields=contract.custom_fields,
        tags=contract.tags,
        scenario=contract.scenario,
        priority=contract.priority,
        risk_level=contract.risk_level,
        difficulty=contract.difficulty,
        test_group=contract.test_group,
        sort_order=sort_order,
    )


def _case_to_dict(case: TestCase) -> dict[str, object]:
    return {
        "case_key": case.case_key,
        "name": case.name,
        "objective": case.objective,
        "case_status": case.case_status.value,
        "template": case.template.value,
        "case_type": case.case_type.value,
        "automation_status": case.automation_status.value,
        "source": case.source.value,
        "source_ref": case.source_ref,
        "component": case.component,
        "requirement_refs": case.requirement_refs,
        "owner_id": case.owner_id.value if case.owner_id else None,
        "preconditions": case.preconditions,
        "input": case.input,
        "data_bindings": case.data_bindings,
        "steps": case.steps,
        "execution_mode": case.execution_mode.value,
        "assertions": case.assertions,
        "scorers": case.scorers,
        "initial_state": case.initial_state,
        "expected_outcome": case.expected_outcome,
        "security_policies": case.security_policies,
        "artifact_requirements": case.artifact_requirements,
        "postconditions": case.postconditions,
        "estimated_duration_seconds": case.estimated_duration_seconds,
        "timeout_seconds": case.timeout_seconds,
        "retry_count": case.retry_count,
        "custom_fields": case.custom_fields,
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
