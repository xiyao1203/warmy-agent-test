#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FIXTURE_DIR="$(mktemp -d "${TMPDIR:-/tmp}/agenttest-e2e-script-test.XXXXXX")"
trap 'rm -rf "$FIXTURE_DIR"' EXIT

mkdir -p "$FIXTURE_DIR/repo/scripts" \
    "$FIXTURE_DIR/repo/apps/control-api" \
    "$FIXTURE_DIR/repo/apps/web/.next" \
    "$FIXTURE_DIR/bin" \
    "$FIXTURE_DIR/runtime"
cp "$ROOT_DIR/scripts/start_e2e_server.sh" "$FIXTURE_DIR/repo/scripts/start_e2e_server.sh"
touch "$FIXTURE_DIR/repo/apps/web/.next/lock"

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
  exec /bin/sleep 300
fi
exit 0
EOF
cat >"$FIXTURE_DIR/bin/pnpm" <<'EOF'
#!/usr/bin/env bash
printf '%s|%s\n' "${AGENTTEST_NEXT_DIST_DIR:-missing}" "$*" >>"$AGENTTEST_E2E_TEST_LOG"
exit 0
EOF
chmod +x "$FIXTURE_DIR/bin/"*

AGENTTEST_E2E_TEST_LOG="$FIXTURE_DIR/invocations.log" \
PATH="$FIXTURE_DIR/bin:$PATH" \
TMPDIR="$FIXTURE_DIR/runtime" \
    bash "$FIXTURE_DIR/repo/scripts/start_e2e_server.sh"

if [[ "$(wc -l <"$FIXTURE_DIR/invocations.log" | tr -d ' ')" -ne 2 ]]; then
    echo "expected exactly two pnpm invocations" >&2
    exit 1
fi
build_line="$(sed -n '1p' "$FIXTURE_DIR/invocations.log")"
start_line="$(sed -n '2p' "$FIXTURE_DIR/invocations.log")"
build_dist="${build_line%%|*}"
start_dist="${start_line%%|*}"
if [[ "$build_dist" == "missing" || "$build_dist" != "$start_dist" ]]; then
    echo "build and start must share an isolated distDir" >&2
    exit 1
fi
if [[ "$build_dist" != "$FIXTURE_DIR/runtime/"agenttest-e2e.*/next ]]; then
    echo "distDir is outside the E2E runtime directory: $build_dist" >&2
    exit 1
fi
if [[ -e "$build_dist" ]]; then
    echo "isolated distDir was not cleaned: $build_dist" >&2
    exit 1
fi
if [[ ! -f "$FIXTURE_DIR/repo/apps/web/.next/lock" ]]; then
    echo "workspace .next lock was modified" >&2
    exit 1
fi

echo "start_e2e_server uses and cleans an isolated Next distDir"
