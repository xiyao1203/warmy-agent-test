from __future__ import annotations

import json
from pathlib import Path

CORE_LIST_PATHS = (
    "/api/v1/projects",
    "/api/v1/system/users",
    "/api/v1/projects/{project_id}/agents",
    "/api/v1/projects/{project_id}/datasets",
    "/api/v1/projects/{project_id}/test-plans",
    "/api/v1/projects/{project_id}/runs",
    "/api/v1/projects/{project_id}/environment-templates",
    "/api/v1/projects/{project_id}/browser-profiles",
    "/api/v1/projects/{project_id}/model-configs",
    "/api/v1/projects/{project_id}/test-accounts",
    "/api/v1/projects/{project_id}/scorers",
    "/api/v1/projects/{project_id}/experiments",
    "/api/v1/projects/{project_id}/reviews",
    "/api/v1/projects/{project_id}/security/scans",
    "/api/v1/projects/{project_id}/gates",
)


def test_core_management_lists_expose_standard_page_parameters() -> None:
    document = json.loads(Path("docs/api/openapi.json").read_text())
    violations: list[str] = []

    for path in CORE_LIST_PATHS:
        operation = document["paths"][path]["get"]
        parameter_names = {parameter["name"] for parameter in operation.get("parameters", [])}
        missing = {"page", "page_size"} - parameter_names
        if missing:
            violations.append(f"{path}: missing {', '.join(sorted(missing))}")

    assert violations == []
