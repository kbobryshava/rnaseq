#!/usr/bin/env bash
# Generates preview DAGs for alternative configurations (no data processed; -preview only).
set -u
here="$(cd "$(dirname "$0")" && pwd)"
run() { label=$1; shift; echo "=== $label: $*"; bash "$here/run_preview.sh" "$label" "$@" > /dev/null 2>&1 && echo ok || echo "FAILED (see logs/preview_$label.log)"; }
run hisat2            --aligner hisat2 --skip_bigwig --skip_pseudo_alignment
run salmon_pseudo     --pseudo_aligner salmon --skip_qc --skip_alignment
run kallisto -params-file "$here/../data/raw/params/kallisto.json"
run star_rsem         --aligner star_rsem --skip_pseudo_alignment
run kraken2           --contaminant_screening kraken2
run kraken2_bracken   --contaminant_screening kraken2_bracken
run hisat2_kraken2_bracken --aligner hisat2 --skip_bigwig --contaminant_screening kraken2_bracken
run sentieon_star     --use_sentieon_star
run parabricks_star   --use_parabricks_star
