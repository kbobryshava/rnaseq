#!/usr/bin/env bash
# Usage: run_preview.sh <label> [extra nextflow args...]
# Generates a Nextflow -preview DAG for the pinned pipeline (no data processed).
set -euo pipefail
export JAVA_HOME=$HOME/tools/jdk17 PATH=$HOME/tools/jdk17/bin:$PATH
export NXF_HOME=$HOME/.nextflow NXF_OPTS="-Xmx2g"
label=$1; shift
root="$(cd "$(dirname "$0")/../.." && pwd)"
out="$root/claude_analysis/data/raw"
cd "$root"
$HOME/tools/nextflow run . -profile test -preview -with-dag "$out/${label}_dag.html" --outdir /tmp/rnaseq-preview-$label "$@" 2>&1 | tee "$root/claude_analysis/logs/preview_${label}.log"
