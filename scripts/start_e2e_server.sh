#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$(mktemp -d "${TMPDIR:-/tmp}/agenttest-e2e.XXXXXX")"
WEB_RUNTIME_DIR="$RUNTIME_DIR/web"
API_PORT="${E2E_API_PORT:-8181}"
WEB_PORT="${E2E_WEB_PORT:-5175}"
BACKEND_PID=""
FRONTEND_PID=""

export AGENTTEST_CONTROL_API_BASE_URL="http://127.0.0.1:$API_PORT"
export AGENTTEST_WEB_ORIGIN="http://localhost:$WEB_PORT"

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

for port in "$WEB_PORT" "$API_PORT"; do
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "E2E port $port is already in use" >&2
        exit 1
    fi
done

export AGENTTEST_DATABASE_URL="sqlite+aiosqlite:///$RUNTIME_DIR/e2e.db"
uv run alembic -c "$ROOT_DIR/apps/control-api/alembic.ini" upgrade head

mkdir -p "$WEB_RUNTIME_DIR"
cp \
    "$ROOT_DIR/apps/web/package.json" \
    "$ROOT_DIR/apps/web/next.config.ts" \
    "$ROOT_DIR/apps/web/next-env.d.ts" \
    "$ROOT_DIR/apps/web/postcss.config.mjs" \
    "$ROOT_DIR/apps/web/tsconfig.json" \
    "$WEB_RUNTIME_DIR/"
cp -R "$ROOT_DIR/apps/web/src" "$WEB_RUNTIME_DIR/"
if [[ -d "$ROOT_DIR/apps/web/public" ]]; then
    cp -R "$ROOT_DIR/apps/web/public" "$WEB_RUNTIME_DIR/"
fi
ln -s "$ROOT_DIR/apps/web/node_modules" "$WEB_RUNTIME_DIR/node_modules"

(
    cd "$ROOT_DIR/apps/control-api"
    exec uv run uvicorn agenttest.main:app \
        --host 127.0.0.1 \
        --port "$API_PORT" \
        --log-level warning
) &
BACKEND_PID=$!

backend_ready=false
for _attempt in {1..120}; do
    if curl --fail --silent "http://127.0.0.1:$API_PORT/api/v1/health" >/dev/null; then
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
    cd "$WEB_RUNTIME_DIR"
    NEXT_PUBLIC_CONTROL_API_URL="http://127.0.0.1:$API_PORT" \
        pnpm exec next build --webpack
    NEXT_PUBLIC_CONTROL_API_URL="http://127.0.0.1:$API_PORT" \
        exec pnpm exec next start --port "$WEB_PORT" --hostname 127.0.0.1
) &
FRONTEND_PID=$!

wait "$FRONTEND_PID"
