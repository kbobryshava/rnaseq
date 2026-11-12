# nf-core software pairs

Directed software pairs ("A → B") taken from the nf-core pipelines, with a bio.tools ID for every tool.

A pair means: a process that uses software A is followed by a process that uses software B in the same workflow, either because B reads an output of A, or because B depends on A (a key, a verdict or metadata), or because A and B run side by side on the same input.

## Source

- **Catalogue:** the nf-core pipeline catalogue (`nfcore_pipelines_catalogue.json`), downloaded with `scripts/1_download/downloader.py`. Archived pipelines are included, and old-style (DSL1) pipelines are read too.
- **Workflows processed: 158**, every workflow version in the catalogue. All workflows, including nf-core/rnaseq, go through exactly the same steps.
- **Tool identifiers:** the bio.tools dump `biotools_raw_14-10-2026.jsonl` (34,488 records) and the bio.tools API.

## Method (short)

1. **Download.** Only the text files that describe a pipeline are fetched from each repository (`main.nf`, `workflows/`, `subworkflows/`, `modules/**/*.nf`, config, `meta.yml` and `environment.yml` files). Nothing is run.
2. **Static analysis.** For every workflow, the Nextflow code is read to build a graph of which process output goes into which process input. Conditions are used to drop paths that can never happen together.
3. **Software per process.** Each process is mapped to one software: the tool named in the module `meta.yml`, otherwise the conda package of its `environment.yml`, otherwise the module name. Old-style pipelines have no modules, so the software is taken from the container and conda directives and the commands in the script.
4. **Software pairs per workflow.** Process edges are checked (an edge that cannot carry data, for example because a `map` drops the element or a `multiMap` splits it, is rejected) and collapsed to software pairs. Every pair gets a `pair_type`:
   - `data_flow`: an output of A is an input of B;
   - `gate_metadata`: B depends on A only through a key, a verdict or metadata;
   - `parallel_co_use`: A and B read the same upstream output, no path between them, same run (stored in both directions);
   - `rejected`: every edge between them was rejected (not a valid pair).

   Mutually exclusive alternatives (A or B, never both, for example `--aligner star` or `hisat2`) are dropped.
5. **Merge over all workflows.** Pairs are merged by tool, and the number of workflows where each pair is valid is counted. Tools with the same bio.tools ID are one tool (`star_align` counts as `star`).
6. **bio.tools IDs.** From the module `meta.yml`, then from the local dump by DOI, other IDs (PMID, PMCID, RRID), homepage URL and last by name. Stronger evidence wins over weaker. Generic words (`cat`, `find`, `filter`, `gzip` ...) never get an ID by name.
7. **Filter.** Only pairs where both tools have a bio.tools ID and that are valid in at least one workflow are kept.
8. **Tables.** The notebook `scripts/3_nodes_edges/build_biotools_tables.ipynb` writes the three data files.

### `direction_type`

| value | meaning |
|---|---|
| `one_direction` | A → B happens in a sequence, B → A never does |
| `both_directions` | A → B and B → A both happen in sequences (in the same or in different workflows) |
| `parallel` | A and B only run side by side, no path between them |

If a pair is a sequence in some workflows and parallel in others, it is `one_direction` or `both_directions`: the sequence is the stronger information.

## Data (`data/`)

| file | one row per | main columns |
|---|---|---|
| `biotools_pairs.csv` | workflow and tool pair | `workflow_id`, `source`, `target`, `direction_type`, `source_biotools_name`, `target_biotools_name` |
| `biotools_edges.csv` | tool pair | `source`, `target`, `direction_type`, `n_workflows`, `workflow_ids` |
| `biotools_nodes.csv` | tool | `biotoolsID`, `biotools_name`, `n_workflows`, `matching_method` |

`source` and `target` in the edges and pairs are bio.tools IDs. `matching_method` says how the ID was found: `biotool_id` (written in the module `meta.yml`), `doi`, `url` or `name`.

## Limits

- The analysis is static: a pair means the code allows it, not that it was seen in a run.
- No pair was checked by hand. The software of a process is read from the module metadata or guessed from the environment, the container or the script (old-style pipelines), so some names are not the tool a researcher would name.
- `name` matches to bio.tools are the weakest and can be wrong for tools with a common name.
- Utilities and reporting tools (for example MultiQC) are in the tables. They can be filtered by hand.

## Scripts (`scripts/`)

| folder | content |
|---|---|
| `1_download/` | `downloader.py`: downloads the pipeline files from GitHub. Edit the paths and options at the top of the file, run it with `DRY_RUN = True` first. |
| `2_pairs/` | the analysis, in five files. `run.py` is the entry point; `pairs.py` builds the pairs of one pipeline (using `graph_dsl2.py` for modern and `graph_dsl1.py` for old-style pipelines); `tool_ids.py` finds the bio.tools IDs; `merge_pairs.py` merges all pipelines and writes `direction_type`. |
| `3_nodes_edges/` | `build_biotools_tables.ipynb`: filters the pairs and writes the three data files. |

Python 3.10 or newer and `pip install -r requirements.txt` (pyyaml, networkx; the notebook also needs pandas).

### How to reproduce

```bash
# 1. download (edit the settings at the top first)
python scripts/1_download/downloader.py

# 2. pairs, run from the folder with the downloaded pipelines (<pipeline>/<version>/main.nf)
cd nfcore_catalogue_code
python <path>/scripts/2_pairs/run.py setup
python <path>/scripts/2_pairs/run.py survey                # what is in the catalogue
python <path>/scripts/2_pairs/run.py analyze               # software pairs of every pipeline, a few minutes
python <path>/scripts/2_pairs/run.py ids --lookup          # tool identifiers (needs internet)
python <path>/scripts/2_pairs/run.py match                 # bio.tools dump: put biotools_raw*.jsonl in the results folder
python <path>/scripts/2_pairs/run.py idtable               # tools_with_ids.csv
python <path>/scripts/2_pairs/run.py merge                 # pairs_merged_unique.csv, control_pool.csv

# 3. open scripts/3_nodes_edges/build_biotools_tables.ipynb in the results folder and run all cells
```

`run.py all --lookup` runs the five analysis steps one after the other. Results go to `<catalogue>/../../processed/nfrel_results` if that folder exists, otherwise to `./nfrel_results` (change with `--out`).
