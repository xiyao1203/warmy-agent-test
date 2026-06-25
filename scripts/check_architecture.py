from __future__ import annotations

import ast
import sys
from pathlib import Path

FORBIDDEN_DOMAIN_DEPENDENCIES = {
    "fastapi",
    "redis",
    "sqlalchemy",
    "temporalio",
}


def imported_modules(tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def module_name_for(path: Path) -> str | None:
    parts = path.parts
    try:
        modules_index = parts.index("modules")
    except ValueError:
        return None
    if len(parts) <= modules_index + 1:
        return None
    return parts[modules_index + 1]


def relative_display_path(source_root: Path, path: Path) -> str:
    return path.relative_to(source_root).as_posix()


def find_violations(source_root: Path) -> list[str]:
    violations: list[str] = []
    for path in sorted(source_root.rglob("*.py")):
        relative_path = path.relative_to(source_root)
        display_path = relative_display_path(source_root, path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports = imported_modules(tree)

        if "domain" in relative_path.parts:
            for imported_module in imports:
                top_level = imported_module.split(".", maxsplit=1)[0]
                if top_level in FORBIDDEN_DOMAIN_DEPENDENCIES:
                    violations.append(
                        f"{display_path}: domain imports forbidden dependency {top_level}"
                    )

        if "api" in relative_path.parts:
            if any(
                ".infrastructure.persistence.models" in imported_module
                for imported_module in imports
            ):
                violations.append(
                    f"{display_path}: API imports infrastructure persistence models"
                )

        source_module = module_name_for(relative_path)
        if source_module:
            for imported_module in imports:
                prefix = "agenttest.modules."
                if not imported_module.startswith(prefix):
                    continue
                segments = imported_module.split(".")
                if len(segments) < 4:
                    continue
                target_module = segments[2]
                target_export = segments[3]
                if target_module != source_module and target_export != "public":
                    violations.append(
                        f"{display_path}: cross-module import must use "
                        f"agenttest.modules.{target_module}.public"
                    )

    return violations


def main() -> int:
    source_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("apps/control-api/src")
    violations = find_violations(source_root)
    if violations:
        print(*violations, sep="\n")
        return 1
    print("Architecture boundaries passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
