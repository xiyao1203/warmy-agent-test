from __future__ import annotations

import ast
import sys
from importlib.util import resolve_name
from pathlib import Path

FORBIDDEN_DOMAIN_DEPENDENCIES = {
    "fastapi",
    "pydantic",
    "redis",
    "sqlalchemy",
    "temporalio",
}

FORBIDDEN_APPLICATION_DEPENDENCIES = FORBIDDEN_DOMAIN_DEPENDENCIES - {"pydantic"}
OUTWARD_DOMAIN_LAYERS = {"api", "application", "infrastructure"}
OUTWARD_APPLICATION_LAYERS = {"api", "infrastructure"}
BUSINESS_DATABASE_DEPENDENCIES = {
    "alembic",
    "asyncpg",
    "psycopg",
    "psycopg2",
    "sqlalchemy",
}


def imported_modules(tree: ast.AST, current_package: str | None = None) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level and current_package:
                relative_name = f"{'.' * node.level}{node.module or ''}"
                imported_module = resolve_name(relative_name, current_package)
                if node.module:
                    modules.append(imported_module)
                else:
                    modules.extend(f"{imported_module}.{alias.name}" for alias in node.names)
            elif node.module:
                modules.append(node.module)
    return modules


def module_name_for(path: Path) -> str | None:
    parts = path.parts
    if len(parts) < 3 or parts[0:2] != ("agenttest", "modules"):
        return None
    return parts[2]


def relative_display_path(source_root: Path, path: Path) -> str:
    return path.relative_to(source_root).as_posix()


def package_name_for(relative_path: Path) -> str:
    """返回源码文件解析相对导入时使用的包名。"""
    return ".".join(relative_path.with_suffix("").parts[:-1])


def layer_for_import(imported_module: str, source_module: str | None) -> str | None:
    """返回同一业务模块或 shared 包导入目标的架构层。"""
    segments = imported_module.split(".")
    if (
        source_module
        and len(segments) >= 4
        and segments[:2] == ["agenttest", "modules"]
        and segments[2] == source_module
    ):
        return segments[3]
    if len(segments) >= 3 and segments[:2] == ["agenttest", "shared"]:
        return segments[2]
    return None


def session_persistence_calls(tree: ast.AST) -> list[str]:
    calls: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"execute", "scalar"}:
            continue
        owner = node.func.value
        if isinstance(owner, ast.Name) and owner.id == "session":
            calls.append(f"session.{node.func.attr}")
    return calls


def find_violations(source_root: Path) -> list[str]:
    violations: list[str] = []
    for path in sorted(source_root.rglob("*.py")):
        relative_path = path.relative_to(source_root)
        display_path = relative_display_path(source_root, path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports = imported_modules(tree, package_name_for(relative_path))

        if "domain" in relative_path.parts:
            for imported_module in imports:
                top_level = imported_module.split(".", maxsplit=1)[0]
                if top_level in FORBIDDEN_DOMAIN_DEPENDENCIES:
                    violations.append(
                        f"{display_path}: domain imports forbidden dependency {top_level}"
                    )

        source_module = module_name_for(relative_path)
        if "domain" in relative_path.parts:
            for imported_module in imports:
                if layer_for_import(imported_module, source_module) in OUTWARD_DOMAIN_LAYERS:
                    violations.append(
                        f"{display_path}: domain imports outward layer {imported_module}"
                    )

        if "application" in relative_path.parts:
            for imported_module in imports:
                top_level = imported_module.split(".", maxsplit=1)[0]
                if top_level in FORBIDDEN_APPLICATION_DEPENDENCIES:
                    violations.append(
                        f"{display_path}: application imports forbidden dependency {top_level}"
                    )
                if layer_for_import(imported_module, source_module) in OUTWARD_APPLICATION_LAYERS:
                    violations.append(
                        f"{display_path}: application imports outward layer {imported_module}"
                    )

        if "api" in relative_path.parts:
            for imported_module in imports:
                if ".infrastructure.persistence.models" in imported_module:
                    violations.append(
                        f"{display_path}: API imports infrastructure persistence models"
                    )
                elif imported_module == "sqlalchemy" or imported_module.startswith("sqlalchemy."):
                    violations.append(
                        f"{display_path}: API imports forbidden dependency sqlalchemy"
                    )
                elif (
                    imported_module.startswith("agenttest.modules.")
                    and ".infrastructure" in imported_module
                ):
                    violations.append(f"{display_path}: API imports module infrastructure")
            for call in session_persistence_calls(tree):
                violations.append(f"{display_path}: API performs persistence call {call}")

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


def find_execution_surface_violations(
    source_root: Path,
    surface: str,
) -> list[str]:
    """检查 Worker 或插件是否越过控制面和业务数据库边界。"""
    violations: list[str] = []
    for path in sorted(source_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        display_path = relative_display_path(source_root, path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative_path = path.relative_to(source_root)
        for imported_module in imported_modules(tree, package_name_for(relative_path)):
            top_level = imported_module.split(".", maxsplit=1)[0]
            if imported_module.startswith("agenttest.modules."):
                violations.append(
                    f"{display_path}: {surface} imports control-plane module {imported_module}"
                )
            if top_level in BUSINESS_DATABASE_DEPENDENCIES:
                violations.append(
                    f"{display_path}: {surface} imports business database dependency {top_level}"
                )
    return violations


def main() -> int:
    source_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("apps/control-api/src")
    violations = find_violations(source_root)
    if len(sys.argv) == 1:
        violations.extend(find_execution_surface_violations(Path("workers"), "worker"))
        violations.extend(find_execution_surface_violations(Path("plugins"), "plugin"))
    if violations:
        print(*violations, sep="\n")
        return 1
    print("Architecture boundaries passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
