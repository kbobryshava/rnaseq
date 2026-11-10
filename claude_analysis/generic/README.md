# nfrel – directed software relationships from any Nextflow DSL2 pipeline

Static analysis only: no Nextflow run, no sequencing data, no containers. Python >= 3.10 with `pyyaml` and `networkx` (`pip install -r claude_analysis/requirements.txt`).

## 1. What to download (and what not)

You need the pipeline's **code**, not its data. `fetch_pipeline.sh` does a sparse, history-free clone of just these paths:

| path | why | needed? |
|---|---|---|
| `main.nf` | entry point (an unnamed `workflow { }` that calls the pipeline workflow) | yes |
| `workflows/`, `subworkflows/` | wiring of processes (the relationships live here) | yes |
| `modules/**/main.nf` | process input/output declarations | yes |
| `modules/**/meta.yml`, `environment.yml` | software identity (tool names) | yes (otherwise software is guessed from the module name) |
| `nextflow.config`, `nextflow_schema.json`, `conf/` | parameter names and defaults, `ext.args` | recommended |
| `modules.json`, `lib/` | module versions, old-style helper code | optional |
| module/subworkflow `tests/`, `*.snap`, `assets/`, `docs/`, `bin/`, `.github/`, test data | not read | **no** |

```bash
bash claude_analysis/generic/fetch_pipeline.sh https://github.com/nf-core/<pipeline> <tag> pipelines/<pipeline>
```
For nf-core/rnaseq 3.27.0 this is 357 files, about 2 MB, and gives exactly the same 1,234 process edges as the full checkout (tested). Pin a tag or commit and keep the printed commit SHA.

Optional extra input: `*_dag.html` files from `nextflow run . -profile test -preview -with-dag x_dag.html` (needs Nextflow + Java; downloads only the small test samplesheet). They add a second opinion (hub-free DAG confirmation) but are not required.

## 2. Run

```bash
python claude_analysis/generic/nfrel.py --repo pipelines/<pipeline> --out results/<pipeline> \
       [--software-map my_map.yaml] [--previews dir_with_dags] [--curation my_decisions.csv]
```
Output in `results/<pipeline>/reference/`:

| file | content |
|---|---|
| `process_relationships.csv` | every process edge: producer/consumer process, module, emit, input slot, operation, edge class, confidence (`confidence_v1` original rule, `confidence_v2` corrected), payload check, required parameters, `file:line` of both calls, input/output declarations. `category` = `algorithmic_supported` / `algorithmic_negative_candidate` / `functional_dependency_non_data` |
| `software_relationships.csv` | one row per ordered software pair: `Algorithmic_supported`, `Dependency_gate_metadata`, `Negative_candidate` (no path + shared input, or only rejected/key-only edges); after curation also `Gold`, `Silver`, `Negative_verified` |
| `curation_template.csv` | your review worklist (see 3) |
| `validation.md/json`, `manifest.json` | checks (duplicates, acyclic, `file:line` exist, unreviewed mappings, curation conflicts), commit SHA, counts, checksums |

Non-data dependencies (QC gates, metadata such as inferred strandedness) are kept in their own category, never mixed into positives or negatives.

## 3. From algorithmic to controls (the part that needs a person)

The tool does **not** produce Gold/Silver by itself. Everything it outputs is algorithmic. To get controls:

1. **Fix software identity.** Copy `pipeline_template.yaml`, list the modules in `primary:` (tool that really does the work; a utility-only process maps to the utility), and re-run with `--software-map`. `validation.md` lists the modules still auto-guessed (`UNREVIEWED`).
2. **Review `curation_template.csv`** (sorted by confidence). For each pair read the two call sites, fill `decision` = `Gold` (named tools, payload verified), `Silver` (verified flow, utility/script end or partial payload) or `Negative_verified`, and put the `file:line` you read in `evidence`.
3. Re-run with `--curation my_decisions.csv`. Gold/Silver need a live edge and Negative_verified must have none, otherwise the run reports a conflict.

Optional rules the analysis cannot see go in the map file: `callsite_infeasible` (a subworkflow called with a literal that disables a branch) and `forbidden_flag_pairs` (options the pipeline refuses to combine). The rnaseq-specific decisions and workflow-family rules (`audit_decisions.py`, `family_rules.py`) are not generic; use them as a model.

## 4. Limits

* Nextflow DSL2 with an unnamed entry `workflow { }` in `main.nf`. `for/while/switch/try` and Groovy functions that create channels are not modelled (the run lists them as unresolved).
* Channel operators are treated as unions: merged channels are `medium` until read; the payload check removes three known false-positive patterns (dropped tuple element, `multiMap`, constant call argument) but is not a proof.
* Software identity comes from the map you give; auto-guessing from `environment.yml` is only a starting point.
* Conditions are recorded (`required_params`), not penalised: a pair counts whenever the tools can be combined in some valid configuration.
* Channels that carry only the sample `meta` map, built from a file's name or path (e.g. fetchngs downloaders -> `MULTIQC_MAPPINGS_CONFIG`), look like data edges (`merged-channel`, medium). The analyzer only recognises the `{ meta, _x -> meta }` key-only pattern, so review such edges before curating them.
* `parsed-content` edges: a file's contents are parsed (`splitCsv`, `splitText`, ...) and the values feed the consumer (fetchngs: runinfo TSV -> downloaders). They count as data dependencies (confidence medium).
* `Negative_candidate / shared-input-no-path` can also be mutually exclusive alternatives; the tool labels them `mutually-exclusive-alternatives` only when `if` conditions contradict (not for `.branch { }` splits).
* Worked example (tested): `generic/examples/fetchngs/` - nf-core/fetchngs 1.13.0, 52 files / 235 KB downloaded, 9 processes, 14 edges, curated in minutes.
* Self-test: `python claude_analysis/generic/tests/test_generic.py` (synthetic mini pipeline, no network).
