# Directed software relationships from nf-core/rnaseq 3.27.0

Positive-control dataset of directed software relationships (A -> B: data produced by a process using A is consumed by a process using B).
Pipeline commit `a1fcdddd3b826fe46eb46f0479f2ff8a7815af05` (3.27.0). Original nf-core files are unchanged; everything lives in this folder.

## Start here
* `reports/methodology_report.md` - what was investigated, which sources are reliable, why the DAG has cycles, results, limitations (verified vs hypothesis labelled).
* `reports/validation_examples.md` - the six requested examples with file:line evidence and negative controls.
* `documentation/data_dictionary.md` - every file and column. `documentation/apply_to_other_pipelines.md` - reuse on other nf-core pipelines.

## Key datasets (`data/processed`)
| file | content |
|---|---|
| `process_edges.csv`, `process_edges_evidence.jsonl` | 1,234 process-instance edges, classes, tiers, conditions, channel trails |
| `process_instances.csv`, `process_software_map.csv`, `canonical_software.csv` | 178 process instances -> canonical software |
| `software_edges.csv`, `software_edges_core_tierA.csv`, `software_nodes.csv` | software-level relationships (self-loops flagged) |
| `manual_review.csv` | low-confidence edges needing review |
| `dag_vs_static.json`, `metro_vs_static.csv` | validation against Nextflow DAGs and the metro map |
Graphs: `data/graphs/*.graphml`, `full_graph.json`, parsed DAGs. Raw preview DAGs: `data/raw`.

## Headline results
* Static channel-provenance analysis gives an acyclic process graph (0 SCCs); the Nextflow DAG has a 47-node SCC caused by fused operator nodes.
* In all 10 preview DAGs every edge that avoids fused nodes is also found statically (0 contradictions); 56-87 % of DAG paths need fused nodes.
* Use evidence tier A (174 edges) and B (839) for controls; C (221) is gating/metadata/key-only. Software-level collapse creates a 24-tool cycle: use process level as ground truth.

## Reproduce
```bash
pip install -r claude_analysis/requirements.txt
bash claude_analysis/scripts/reproduce.sh                  # Python only
bash claude_analysis/scripts/reproduce.sh --with-previews  # also regenerates preview DAGs (Java 17 + Nextflow, WSL/Linux)
```
Environment used: Windows 11 + WSL Ubuntu 22.04, JDK 17, Nextflow 26.10.5, Python 3.13. Preview DAGs only; the pipeline was never run on data.
