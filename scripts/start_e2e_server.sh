#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$(mktemp -d "${TMPDIR:-/tmp}/agenttest-e2e.XXXXXX")"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    local status=$?
    trap - EXIT INT TERM
    if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        kill "$FRONTEND_PID" 2>/dev/null || true
        wait "$FRONTEND_PID" 2>/dev/null || true
    fi
    if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        kill "$BACKEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
    fi
    if [[ -d "$RUNTIME_DIR" ]]; then
        find "$RUNTIME_DIR" -depth -delete
    fi
    exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

for port in 5175 8181; do
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "E2E port $port is already in use" >&2
        exit 1
    fi
done

export AGENTTEST_DATABASE_URL="sqlite+aiosqlite:///$RUNTIME_DIR/e2e.db"
uv run alembic -c "$ROOT_DIR/apps/control-api/alembic.ini" upgrade head

(
    cd "$ROOT_DIR/apps/control-api"
    exec uv run uvicorn agenttest.main:app \
        --host 127.0.0.1 \
        --port 8181 \
        --log-level warning
) &
BACKEND_PID=$!

backend_ready=false
for _attempt in {1..120}; do
    if curl --fail --silent "http://127.0.0.1:8181/api/v1/health" >/dev/null; then
        backend_ready=true
        break
    fi
    sleep 0.25
done
if [[ "$backend_ready" != "true" ]]; then
    echo "E2E Control API did not become ready" >&2
    exit 1
fi

(
    cd "$ROOT_DIR/apps/web"
    NEXT_PUBLIC_CONTROL_API_URL="http://127.0.0.1:8181" \
        pnpm build
    NEXT_PUBLIC_CONTROL_API_URL="http://127.0.0.1:8181" \
        exec pnpm exec next start --port 5175 --hostname 127.0.0.1
) &
FRONTEND_PID=$!

wait "$FRONTEND_PID"
