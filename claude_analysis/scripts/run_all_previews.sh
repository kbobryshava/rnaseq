#!/usr/bin/env bash
# Generates preview DAGs for alternative configurations (no data processed; -preview only).
# Parameters live in data/raw/params/<label>.json (JSON keeps booleans typed; CLI flags were validated as strings).
set -u
here="$(cd "$(dirname "$0")" && pwd)"
for pf in "$here"/../data/raw/params/*.json; do
  label=$(basename "$pf" .json)
  echo "=== $label: $(cat "$pf")"
  bash "$here/run_preview.sh" "$label" -params-file "$pf" > /dev/null 2>&1 && echo ok || echo "FAILED (see logs/preview_$label.log)"
done
