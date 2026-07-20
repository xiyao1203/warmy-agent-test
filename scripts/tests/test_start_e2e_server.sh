#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FIXTURE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/agenttest-e2e-script-test.XXXXXX")"
FIXTURE_DIR="$(cd "$FIXTURE_DIR" && pwd -P)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT

mkdir -p "$FIXTURE_DIR/repo/scripts" \
    "$FIXTURE_DIR/repo/apps/control-api" \
    "$FIXTURE_DIR/repo/apps/web/.next" \
    "$FIXTURE_DIR/repo/apps/web/node_modules" \
    "$FIXTURE_DIR/repo/apps/web/src" \
    "$FIXTURE_DIR/bin" \
    "$FIXTURE_DIR/runtime"
cp "$ROOT_DIR/scripts/start_e2e_server.sh" "$FIXTURE_DIR/repo/scripts/start_e2e_server.sh"
touch "$FIXTURE_DIR/repo/apps/web/.next/lock"
for file in package.json next.config.ts next-env.d.ts postcss.config.mjs tsconfig.json; do
    printf '{}\n' >"$FIXTURE_DIR/repo/apps/web/$file"
done

cat >"$FIXTURE_DIR/bin/lsof" <<'EOF'
#!/usr/bin/env bash
exit 1
EOF
cat >"$FIXTURE_DIR/bin/curl" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
cat >"$FIXTURE_DIR/bin/uv" <<'EOF'
#!/usr/bin/env bash
if [[ "$*" == *"uvicorn"* ]]; then
  printf '%s\n' "${AGENTTEST_WEB_ORIGIN:-missing}" >"$AGENTTEST_E2E_ORIGIN_LOG"
  exec /bin/sleep 300
fi
exit 0
EOF
cat >"$FIXTURE_DIR/bin/pnpm" <<'EOF'
#!/usr/bin/env bash
printf '%s|%s\n' "$PWD" "$*" >>"$AGENTTEST_E2E_TEST_LOG"
exit 0
EOF
chmod +x "$FIXTURE_DIR/bin/"*

AGENTTEST_E2E_TEST_LOG="$FIXTURE_DIR/invocations.log" \
AGENTTEST_E2E_ORIGIN_LOG="$FIXTURE_DIR/origin.log" \
E2E_API_PORT=8182 \
E2E_WEB_PORT=5176 \
PATH="$FIXTURE_DIR/bin:$PATH" \
TMPDIR="$FIXTURE_DIR/runtime" \
    bash "$FIXTURE_DIR/repo/scripts/start_e2e_server.sh"

if [[ "$(wc -l <"$FIXTURE_DIR/invocations.log" | tr -d ' ')" -ne 2 ]]; then
    echo "expected exactly two pnpm invocations" >&2
    exit 1
fi
build_line="$(sed -n '1p' "$FIXTURE_DIR/invocations.log")"
start_line="$(sed -n '2p' "$FIXTURE_DIR/invocations.log")"
build_cwd="${build_line%%|*}"
build_command="${build_line#*|}"
start_cwd="${start_line%%|*}"
start_command="${start_line#*|}"
if [[ "$build_cwd" != "$start_cwd" || "$build_cwd" != "$FIXTURE_DIR/runtime/"agenttest-e2e.*/web ]]; then
    echo "build and start must run from an isolated Web copy" >&2
    exit 1
fi
if [[ "$build_command" != "exec next build --webpack" ]]; then
    echo "isolated build must use the Next 16 compatible Webpack path" >&2
    exit 1
fi
if [[ "$start_command" != "exec next start --port 5176 --hostname 127.0.0.1" ]]; then
    echo "isolated server did not use the configured Web port" >&2
    exit 1
fi
resolved_dist="$build_cwd/.next"
if [[ -e "$resolved_dist" ]]; then
    echo "isolated distDir was not cleaned: $resolved_dist" >&2
    exit 1
fi
if [[ "$(cat "$FIXTURE_DIR/origin.log")" != "http://localhost:5176" ]]; then
    echo "backend CORS origin did not follow the configured Web port" >&2
    exit 1
fi
if [[ ! -f "$FIXTURE_DIR/repo/apps/web/.next/lock" ]]; then
    echo "workspace .next lock was modified" >&2
    exit 1
fi

echo "start_e2e_server isolates builds and propagates configured ports"
