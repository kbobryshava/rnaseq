#!/usr/bin/env bash
# Download ONLY what the analysis needs from a Nextflow pipeline repository (no test data, no docs, no module tests, no assets, no git history).
#   bash fetch_pipeline.sh <git-url> <tag-or-branch> <dest-dir>
#   e.g. bash fetch_pipeline.sh https://github.com/nf-core/rnaseq 3.27.0 pipelines/rnaseq
# Typically a few MB instead of the whole repository.
set -euo pipefail
export MSYS_NO_PATHCONV=1   # Git Bash on Windows would otherwise rewrite the leading "/" of the patterns
url="$1"; ref="$2"; dest="$3"
git clone --quiet --filter=blob:none --no-checkout --depth 1 --branch "$ref" "$url" "$dest"
cd "$dest"
git sparse-checkout init --no-cone
git sparse-checkout set \
  '/main.nf' '/nextflow.config' '/nextflow_schema.json' '/modules.json' \
  '/workflows/' '/subworkflows/' '/modules/' '/conf/' '/lib/' \
  '!/modules/**/tests/' '!/subworkflows/**/tests/' '!/workflows/**/tests/' '!*.snap' '!*.nf.test'
git checkout --quiet
echo "pipeline:  $url @ $ref"
echo "commit:    $(git rev-parse HEAD)"
echo "files:     $(git ls-files | wc -l) tracked, $(find . -path ./.git -prune -o -type f -print | wc -l) on disk, $(du -sh --exclude=.git . | cut -f1)"
