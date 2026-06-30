"""Detect production code that can manufacture successful-looking results."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, order=True, slots=True)
class Violation:
    path: str
    line: int
    rule: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.rule}"


_TEXT_RULES = {
    "automatic mock fallback": re.compile(
        r"MockScanner|_mock_result|fallback[^\n]*Mock|降级为\s*mock|Promptfoo\s*或\s*Mock",
        re.IGNORECASE,
    ),
    "demo business response": re.compile(
        r"demo-project|这里使用示例数据|示例测试计划|固定创建一条模板用例"
    ),
    "in-memory business fact": re.compile(
        r"production should use DB|_sessions:\s*dict|_tasks:\s*dict"
    ),
    "silent browser dependency fallback": re.compile(
        r"browser-harness 不可用|browser-harness 未安装或 Chrome 未启动"
    ),
    "floating runtime dependency": re.compile(
        r"playwright_version:\s*str\s*=\s*[\"']latest[\"']|@playwright/mcp@latest"
    ),
    "unsafe wildcard CORS": re.compile(r"allow_origins=\[\s*[\"']\*[\"']\s*\]"),
    "hard-coded scanner target": re.compile(r"agent_endpoint\s+or\s+[\"']http://localhost"),
    "fixed generated case loop": re.compile(r"for\s+\w+\s+in\s+range\(1\).*placeholder"),
    "secondary model credential path": re.compile(
        r"CANVAS_MODEL_(?:API_KEY|BASE_URL)|OPENAI_API_KEY"
    ),
    "empty response on upstream failure": re.compile(r"if\s*\(!?res\.ok\)\s*return\s*\[\]"),
    "placeholder authenticated user": re.compile(r"placeholderUser"),
}

_ROOTS = (
    "apps/control-api/src",
    "apps/web/src",
    "workers",
    "plugins",
    "infra/compose",
)
_SUFFIXES = {".py", ".ts", ".tsx", ".yaml", ".yml"}
_EXCLUDED_PARTS = {"tests", "__tests__", "node_modules", ".next", "dist", "__pycache__"}
_EXCLUDED_FILES = {
    "apps/control-api/src/agenttest/modules/plugins/network_mock.py",
}


def _source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for relative_root in _ROOTS:
        source_root = root / relative_root
        if not source_root.exists():
            continue
        for path in source_root.rglob("*"):
            if not path.is_file() or path.suffix not in _SUFFIXES:
                continue
            relative = path.relative_to(root)
            if any(part in _EXCLUDED_PARTS for part in relative.parts):
                continue
            if relative.as_posix() in _EXCLUDED_FILES:
                continue
            files.append(path)
    return sorted(files)


def scan_repository(root: Path) -> list[Violation]:
    violations: list[Violation] = []
    for path in _source_files(root):
        relative = path.relative_to(root).as_posix()
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for rule, pattern in _TEXT_RULES.items():
                if pattern.search(line):
                    violations.append(Violation(relative, line_number, rule))
            if (
                "process.env.NEXT_PUBLIC_CONTROL_API_URL" in line
                and relative != "apps/web/src/lib/api/base-url.ts"
            ):
                violations.append(Violation(relative, line_number, "feature-local Control API URL"))
            if re.search(r"^\s*image:\s*\S+:latest\s*$", line):
                violations.append(Violation(relative, line_number, "floating container image"))
    return sorted(set(violations))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    violations = scan_repository(root)
    for violation in violations:
        print(violation)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
