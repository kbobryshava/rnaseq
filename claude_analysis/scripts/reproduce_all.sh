#!/usr/bin/env bash
# Rebuild the ENTIRE extraction, audit and frozen reference dataset from the pinned nf-core/rnaseq checkout.
#   bash claude_analysis/scripts/reproduce_all.sh                 # pure Python, uses the committed preview DAGs in data/raw
#   bash claude_analysis/scripts/reproduce_all.sh --with-previews # also re-run `nextflow -preview` (needs Java 17 + Nextflow, e.g. in WSL)
# Requirements: Python >= 3.10, `pip install -r claude_analysis/requirements.txt` (pandas+pyarrow optional: parquet copies only).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; repo="$(cd "$here/../.." && pwd)"; out="$repo/claude_analysis"
expected=a1fcdddd3b826fe46eb46f0479f2ff8a7815af05
git -C "$repo" cat-file -e "$expected^{commit}" 2>/dev/null || echo "WARNING: pinned commit $expected not found in this checkout"
git -C "$repo" merge-base --is-ancestor "$expected" HEAD 2>/dev/null || echo "WARNING: pinned commit is not an ancestor of HEAD"
if [ "${1:-}" = "--with-previews" ]; then
  mkdir -p "$out/logs"
  bash "$here/run_preview.sh" test | tee "$out/logs/preview_test.log" >/dev/null
  bash "$here/run_all_previews.sh"
fi
cd "$repo"
export PYTHONHASHSEED="${PYTHONHASHSEED:-0}"   # outputs are order-independent, this is belt and braces
py="${PYTHON:-python}"
$py -I "$here/nf_static_analyzer.py" --root . --out "$out/data/processed"          # 1 static channel-provenance analysis
$py "$here/build_datasets.py" --repo . --out "$out"                                  # 2 process/software datasets (confidence_v1 + confidence_v2)
$py "$here/validate_examples.py" --out "$out"                                        # 3 the six requested examples
$py "$here/compare_metro.py" --repo . --out "$out"                                   # 4 metro-map comparison
$py "$here/audit_dossier.py"                                                         # 5 audit: per-pair dossier of the 53 core pairs
$py "$here/audit_merged.py"                                                          # 6 audit: payload check table
$py "$here/curate_audit.py" > /dev/null                                              # 7 audit: decisions, negatives, final confidence
$py "$here/render_audit_report.py"                                                   # 8 audit report
$py "$here/build_reference.py"                                                       # 9 frozen reference dataset
$py "$here/validate_reference.py"                                                    # 10 validation (exit 1 on failure)
$py "$here/make_manifest.py"                                                         # 11 manifest + SHA256SUMS
(cd "$out/reference" && sha256sum -c SHA256SUMS --quiet && echo "checksums OK")
echo "done: claude_analysis/reference/"
