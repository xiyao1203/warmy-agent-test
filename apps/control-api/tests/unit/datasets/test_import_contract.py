import json

import pytest
from agenttest.modules.datasets.application.import_export import (
    ImportError,
    _build_test_case,
    parse_and_validate_import,
)

# ── 核心契约：非对象 input 必须被拒绝，不允许静默变成 {} ──────────────


def test_import_rejects_non_object_input_instead_of_replacing_it() -> None:
    content = '[{"name":"bad","input":"hello","execution_mode":"api"}]'

    with pytest.raises(ImportError) as caught:
        parse_and_validate_import("json", content)

    assert caught.value.errors == [
        {
            "line": 1,
            "field": "input",
            "code": "invalid_type",
            "message": "input must be a JSON object",
        }
    ]


def test_build_test_case_raises_on_non_dict_input_instead_of_defaulting_to_empty() -> None:
    """Step 2: 验证 _build_test_case 不会把非 dict 的 input 静默变成 {}。"""
    from uuid import uuid4

    with pytest.raises(ValueError, match="input must be a JSON object"):
        _build_test_case(
            version_id=uuid4(),
            raw={"name": "bad", "input": "hello", "execution_mode": "api"},
            sort_order=1,
        )


# ── JSONL 行号与枚举错误 ──────────────────────────────────────────────


def test_import_reports_jsonl_line_and_enum_errors() -> None:
    content = "\n".join(
        [
            '{"name":"ok","input":{},"execution_mode":"api"}',
            '{"name":"bad","input":{},"execution_mode":"unknown"}',
        ]
    )

    preview = parse_and_validate_import("jsonl", content, allow_errors=True)

    assert preview["valid_count"] == 1
    assert preview["errors"][0]["line"] == 2
    assert preview["errors"][0]["field"] == "execution_mode"


# ── 10MB 上限 ─────────────────────────────────────────────────────────


def test_import_rejects_files_larger_than_ten_megabytes() -> None:
    with pytest.raises(ValueError, match="10MB"):
        parse_and_validate_import("json", " " * (10 * 1024 * 1024 + 1))


# ── 严格对象/列表类型 ─────────────────────────────────────────────────


def test_import_rejects_assertions_that_are_not_list_of_objects() -> None:
    content = json.dumps(
        [
            {
                "name": "ok",
                "input": {},
                "execution_mode": "api",
                "assertions": [1, 2, 3],
            }
        ]
    )

    with pytest.raises(ImportError) as caught:
        parse_and_validate_import("json", content)

    err = caught.value.errors[0]
    assert err["field"] == "assertions"
    assert err["code"] == "invalid_type"
    assert "list of objects" in err["message"]


def test_import_rejects_scorers_that_are_not_list_of_objects() -> None:
    content = json.dumps(
        [
            {
                "name": "ok",
                "input": {},
                "execution_mode": "api",
                "scorers": "not-a-list",
            }
        ]
    )

    with pytest.raises(ImportError) as caught:
        parse_and_validate_import("json", content)

    err = caught.value.errors[0]
    assert err["field"] == "scorers"
    assert err["code"] == "invalid_type"


def test_import_rejects_initial_state_that_is_not_object() -> None:
    content = json.dumps(
        [
            {
                "name": "ok",
                "input": {},
                "execution_mode": "api",
                "initial_state": "not-an-object",
            }
        ]
    )

    with pytest.raises(ImportError) as caught:
        parse_and_validate_import("json", content)

    err = caught.value.errors[0]
    assert err["field"] == "initial_state"
    assert err["code"] == "invalid_type"


def test_import_rejects_tags_that_are_not_list_of_strings() -> None:
    content = json.dumps(
        [
            {
                "name": "ok",
                "input": {},
                "execution_mode": "api",
                "tags": [1, 2, 3],
            }
        ]
    )

    with pytest.raises(ImportError) as caught:
        parse_and_validate_import("json", content)

    err = caught.value.errors[0]
    assert err["field"] == "tags"
    assert err["code"] == "invalid_type"


# ── 枚举错误（priority / risk_level / test_group）───────────────────


def test_import_rejects_invalid_priority_with_structured_error() -> None:
    content = json.dumps(
        [
            {
                "name": "ok",
                "input": {},
                "execution_mode": "api",
                "priority": "P99",
            }
        ]
    )

    with pytest.raises(ImportError) as caught:
        parse_and_validate_import("json", content)

    err = caught.value.errors[0]
    assert err["field"] == "priority"
    assert err["code"] == "invalid_enum"
    assert "P0" in err["message"]


def test_import_rejects_invalid_risk_level_with_structured_error() -> None:
    content = json.dumps(
        [
            {
                "name": "ok",
                "input": {},
                "execution_mode": "api",
                "risk_level": "extreme",
            }
        ]
    )

    with pytest.raises(ImportError) as caught:
        parse_and_validate_import("json", content)

    err = caught.value.errors[0]
    assert err["field"] == "risk_level"
    assert err["code"] == "invalid_enum"


def test_import_rejects_invalid_test_group_with_structured_error() -> None:
    content = json.dumps(
        [
            {
                "name": "ok",
                "input": {},
                "execution_mode": "api",
                "test_group": "production",
            }
        ]
    )

    with pytest.raises(ImportError) as caught:
        parse_and_validate_import("json", content)

    err = caught.value.errors[0]
    assert err["field"] == "test_group"
    assert err["code"] == "invalid_enum"


# ── 未知字段拒绝 ─────────────────────────────────────────────────────


def test_import_rejects_unknown_fields() -> None:
    content = json.dumps(
        [
            {
                "name": "ok",
                "input": {},
                "execution_mode": "api",
                "made_up_field": "should be rejected",
            }
        ]
    )

    with pytest.raises(ImportError) as caught:
        parse_and_validate_import("json", content)

    err = caught.value.errors[0]
    assert err["field"] == "made_up_field"
    assert err["code"] == "unknown_field"


# ── 多错误汇总 ───────────────────────────────────────────────────────


def test_import_collects_multiple_errors_per_line() -> None:
    content = json.dumps(
        [
            {
                "name": "",
                "execution_mode": "unknown",
                "made_up": True,
            }
        ]
    )

    with pytest.raises(ImportError) as caught:
        parse_and_validate_import("json", content)

    fields = {e["field"] for e in caught.value.errors}
    assert "name" in fields
    assert "execution_mode" in fields
    assert "made_up" in fields
    assert "input" in fields  # missing required


# ── 预览模式（dry-run）────────────────────────────────────────────────


def test_preview_mode_returns_valid_count_and_errors_without_raising() -> None:
    content = "\n".join(
        [
            '{"name":"ok","input":{},"execution_mode":"api"}',
            '{"name":"bad","input":{},"execution_mode":"unknown"}',
        ]
    )

    result = parse_and_validate_import("jsonl", content, allow_errors=True)

    assert result["valid_count"] == 1
    assert len(result["errors"]) == 1
    assert result["errors"][0]["line"] == 2
    assert "preview" in result
    assert len(result["preview"]) == 1


# ── CSV 格式对等 ─────────────────────────────────────────────────────


def test_csv_import_produces_same_result_as_json() -> None:
    json_content = json.dumps(
        [
            {
                "name": "csv test",
                "input": {"q": "hello"},
                "execution_mode": "api",
                "priority": "P0",
                "tags": ["smoke"],
            }
        ]
    )
    csv_content = (
        "name,input,execution_mode,priority,tags\n"
        'csv test,"{""q"":""hello""}",api,P0,"[""smoke""]"\n'
    )

    json_result = parse_and_validate_import("json", json_content, allow_errors=True)
    csv_result = parse_and_validate_import("csv", csv_content, allow_errors=True)

    assert json_result["valid_count"] == csv_result["valid_count"] == 1
    assert json_result["preview"][0]["name"] == csv_result["preview"][0]["name"]
    assert json_result["preview"][0]["input"] == csv_result["preview"][0]["input"]
    assert json_result["preview"][0]["execution_mode"] == csv_result["preview"][0]["execution_mode"]
    assert json_result["preview"][0]["priority"] == csv_result["preview"][0]["priority"]


# ── 非数组 JSON 拒绝 ─────────────────────────────────────────────────


def test_json_import_rejects_non_array_root() -> None:
    with pytest.raises(ValueError, match="array"):
        parse_and_validate_import("json", '{"name":"not array"}')


# ── 空内容有效导入 ───────────────────────────────────────────────────


def test_empty_json_array_imports_zero_cases() -> None:
    result = parse_and_validate_import("json", "[]", allow_errors=True)
    assert result["valid_count"] == 0
    assert result["errors"] == []
    assert result["preview"] == []
