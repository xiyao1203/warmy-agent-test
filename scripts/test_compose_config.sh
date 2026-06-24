#!/usr/bin/env bash
set -euo pipefail

test -f infra/compose/compose.yaml
docker compose -f infra/compose/compose.yaml config --quiet
