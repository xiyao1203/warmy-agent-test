#!/usr/bin/env bash
set -euo pipefail

requirements_file="$(mktemp "${TMPDIR:-/tmp}/agenttest-requirements.XXXXXX.txt")"
trap 'rm -f "$requirements_file"' EXIT

pnpm audit --prod --audit-level moderate
uv export --all-packages --frozen --no-dev --no-emit-workspace --quiet -o "$requirements_file"
uvx --from pip-audit pip-audit --disable-pip --no-deps -r "$requirements_file"
