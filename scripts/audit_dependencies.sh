#!/usr/bin/env bash
set -euo pipefail

requirements_file="$(mktemp "${TMPDIR:-/tmp}/agenttest-requirements.XXXXXX.txt")"
trap 'rm -f "$requirements_file"' EXIT

pnpm audit --prod --audit-level high
uv export --all-packages --frozen --no-dev --no-emit-workspace --quiet -o "$requirements_file"

# browser-harness 0.1.3 pins Pillow 12.2.0. The pinned package only opens PNGs
# created by CDP for optional resize/debug overlays; our code does not import
# Pillow directly. Fail closed if the version or the known call shape changes.
repository_pillow_pattern='(^|[^[:alnum:]_])(from[[:space:]]+PIL|import[[:space:]]+PIL)'
if rg -n --glob '*.py' "$repository_pillow_pattern" apps workers plugins; then
  echo "Pillow advisory mitigation invalid: repository code now imports Pillow." >&2
  exit 1
fi
browser_harness_dir="$(uv run python -c 'import browser_harness, pathlib; print(pathlib.Path(browser_harness.__file__).parent)')"
browser_harness_version="$(uv run python -c 'import importlib.metadata; print(importlib.metadata.version("browser-harness"))')"
if [[ "$browser_harness_version" != "0.1.3" ]]; then
  echo "Pillow advisory mitigation requires review for browser-harness $browser_harness_version." >&2
  exit 1
fi

vulnerable_pillow_path_pattern='PcfFontFile|BdfFontFile|FontFile|GdImageFile|ImageShow|WindowsViewer|\.show\('
if rg -n --glob '*.py' "$vulnerable_pillow_path_pattern" "$browser_harness_dir"; then
  echo "Pillow advisory mitigation invalid: browser-harness reaches a vulnerable Pillow path." >&2
  exit 1
fi

browser_pillow_files="$(rg -l --glob '*.py' 'from[[:space:]]+PIL|import[[:space:]]+PIL|Image\.open' "$browser_harness_dir" || true)"
if [[ "$browser_pillow_files" != "$browser_harness_dir/helpers.py" ]]; then
  echo "Pillow advisory mitigation invalid: browser-harness Pillow usage moved or expanded." >&2
  exit 1
fi
if [[ "$(rg -c 'from[[:space:]]+PIL' "$browser_harness_dir/helpers.py")" != "2" ]] || \
   [[ "$(rg -c 'Image\.open\(path\)' "$browser_harness_dir/helpers.py")" != "2" ]]; then
  echo "Pillow advisory mitigation invalid: browser-harness Pillow call shape changed." >&2
  exit 1
fi

uvx --from pip-audit pip-audit \
  --ignore-vuln PYSEC-2026-2253 \
  --ignore-vuln PYSEC-2026-2254 \
  --ignore-vuln PYSEC-2026-2255 \
  --ignore-vuln PYSEC-2026-2256 \
  --ignore-vuln PYSEC-2026-2257 \
  -r "$requirements_file"
