#!/usr/bin/env bash
# Rebuild the audit layer from the existing extraction (does not touch data/processed, reports/ or the original scripts).
#   bash claude_analysis/scripts/reproduce_audit.sh
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; repo="$(cd "$here/../.." && pwd)"
cd "$repo"
python "$here/audit_dossier.py"
python "$here/audit_merged.py"
python "$here/curate_audit.py" > /dev/null
python "$here/render_audit_report.py"
echo "done: see claude_analysis/audit/AUDIT_REPORT.md"
