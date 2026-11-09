#!/usr/bin/env bash
# Reproduce every dataset in claude_analysis/ from the pinned repository checkout.
#   bash claude_analysis/scripts/reproduce.sh [--with-previews]
# Previews need Java 17 + Nextflow (run inside WSL/Linux); everything else is pure Python (pyyaml, networkx).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; repo="$(cd "$here/../.." && pwd)"; out="$repo/claude_analysis"
test "$(git -C "$repo" rev-parse HEAD~0 2>/dev/null | head -c0)" = "" || true
expected=a1fcdddd3b826fe46eb46f0479f2ff8a7815af05
if ! git -C "$repo" merge-base --is-ancestor $expected HEAD 2>/dev/null; then echo "WARNING: pinned commit $expected is not an ancestor of HEAD"; fi
if [ "${1:-}" = "--with-previews" ]; then
  bash "$here/run_preview.sh" test | tee "$out/logs/preview_test.log" >/dev/null
  bash "$here/run_all_previews.sh"
fi
cd "$repo"
python -I "$here/nf_static_analyzer.py" --root . --out "$out/data/processed"
python "$here/build_datasets.py" --repo . --out "$out"
python "$here/validate_examples.py" --out "$out"
python "$here/compare_metro.py" --repo . --out "$out"
echo "done: see $out/data/processed and $out/reports"
