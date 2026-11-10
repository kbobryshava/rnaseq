> **Superseded by `claude_analysis/generic/README.md`** (one command, sparse download, software-map and curation files, self-test). The text below is the first-release manual procedure.

# Applying the method to another nf-core pipeline

The scripts are pipeline-agnostic for any Nextflow DSL2 repository whose entry script is `main.nf` with an
unnamed `workflow { ... }` block that calls named workflows/processes (all nf-core pipelines follow this).

## 0. Requirements
* Python >= 3.10 with `pyyaml` and `networkx` (`pip install -r claude_analysis/requirements.txt`).
* Only for preview DAGs: Java 17+ and Nextflow >= the pipeline's `nextflowVersion` (on Windows run it inside WSL).
  The static analyzer itself needs **neither Java nor Nextflow**.

## 1. Pin the pipeline
```bash
git clone https://github.com/nf-core/<pipeline> && cd <pipeline>
git checkout <tag-or-commit>          # record the commit hash in your report
mkdir -p claude_analysis/{scripts,data/{raw,processed,graphs},reports,documentation,logs}
cp <this repo>/claude_analysis/scripts/*.py claude_analysis/scripts/
```

## 2. Static process-level graph (authoritative source of directed edges)
```bash
python -I claude_analysis/scripts/nf_static_analyzer.py --root . --out claude_analysis/data/processed
```
Inspect `unresolved` and `infeasible_edges_dropped` in `static_graph.json`. `unresolved` lists statements the
parser could not model (`for`/`while`/`switch`/`try`) and argument-count mismatches: add support or review manually.

## 3. Preview DAGs for executed-instance evidence (optional but recommended)
Write one JSON params file per configuration in `data/raw/params/<label>.json` (use JSON so booleans stay
booleans; `--flag true` on the command line is validated as a *string* by nf-schema) and run
`scripts/run_all_previews.sh`. Each run: `nextflow run . -profile test -preview -with-dag ...`. No data is processed.
DAGs of failed runs are empty and are skipped automatically.

## 4. Software mapping (the only manual step)
Edit `PRIMARY` and `CANON` in `scripts/build_datasets.py`:
* `PRIMARY[<PROCESS NAME>] = [software keys]` - the tool(s) that actually transform the data in that module.
  Read `main.nf` (script block, `topic: versions` tuples), `environment.yml` and `meta.yml`; nf-core `meta.yml`
  `tools:` entries are **not reliable** (RSEM modules list `rseqc`; local scripts list `custom`).
* `CANON[key] = (canonical name, role)`; roles are used to separate analysis software from reporting/utility software.
* Modules missing from `PRIMARY` are auto-mapped from `environment.yml` and marked
  `mapping_method = auto-from-environment-yml (UNREVIEWED)`: review them before using the dataset.

## 5. Build datasets and validate
```bash
python claude_analysis/scripts/build_datasets.py --repo . --out claude_analysis
python claude_analysis/scripts/validate_examples.py --out claude_analysis      # adapt the example filters
python claude_analysis/scripts/compare_metro.py --repo . --out claude_analysis  # only if assets/metro_map.mmd exists
```

## 6. Choosing which edges to treat as positive controls
| column | meaning | use |
|---|---|---|
| `evidence_tier = A-dag-confirmed` | static edge also present in a preview DAG without crossing a fused multi-input/multi-output DAG node | strongest |
| `B-static-only` | `direct`/`merged-channel`/`reporting-aggregation` edge from channel provenance only | usable, check `conditional` and `required_param_assumptions` |
| `C-review` | key-only synchronisation, metadata or gating dependency | exclude from positive controls unless manually verified |
| `edge_class = reporting-aggregation` | consumed by MultiQC-like aggregators | keep in a separate "reporting" layer |

Software-level edges (`software_edges.csv`) keep `n_supporting_process_edges`, `classes` and `self_loop`; filter on
`only_reporting`, `best_confidence` and `observed_in_preview_configs` for the control set. Software-level cycles are
expected (a tool can appear at several stages) and are **not** errors; the process-level graph is acyclic.

## 7. Known limitations to re-check per pipeline
* `for`, `while`, `switch`, `try` blocks and closures that call processes are not modelled.
* `.map {}` closures that drop part of a tuple are only detected for the key-only pattern (`{ meta, _x -> meta }`).
* Condition pruning uses name-based atoms (`x == 'v'`, `!x`, `x`); same-named variables in different scopes could prune wrongly - audit `infeasible_edges_dropped`.
* Plugins/functions that create channels from other processes' outputs through Groovy code are invisible.
