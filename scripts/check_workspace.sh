#!/usr/bin/env bash
set -euo pipefail

test -f package.json
test -f pnpm-workspace.yaml
test -f pyproject.toml
test -d apps/web
test -d apps/control-api
test -d apps/admin-cli
test -d packages/generated-api-client
