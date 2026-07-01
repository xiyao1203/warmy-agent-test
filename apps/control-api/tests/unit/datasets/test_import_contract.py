import pytest
from agenttest.modules.datasets.application.import_export import (
    ImportError,
    parse_and_validate_import,
)


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


def test_import_rejects_files_larger_than_ten_megabytes() -> None:
    with pytest.raises(ValueError, match="10MB"):
        parse_and_validate_import("json", " " * (10 * 1024 * 1024 + 1))
