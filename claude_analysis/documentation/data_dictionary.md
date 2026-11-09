# Data dictionary

All paths are relative to `claude_analysis/`. Pipeline: nf-core/rnaseq **3.27.0**, commit `a1fcdddd3b826fe46eb46f0479f2ff8a7815af05`.

## data/raw
| file | content |
|---|---|
| `<label>_dag.html` | Nextflow 26.10.5 `-preview -with-dag` output (Mermaid flowchart). `test` = default `-profile test` (STAR + Salmon). |
| `params/<label>.json` | Parameters used for each alternative-configuration preview. |

## data/graphs
| file | content |
|---|---|
| `<label>_dag_raw.json` | Parsed Nextflow DAG: nodes (`process` / `operator` / `channel`, scope path) and edges. Faithful to the HTML; includes the fused nodes that cause false cycles. |
| `process_graph.graphml` | Instance-level static process graph (MultiDiGraph, one edge per source-emit -> consumer-input). |
| `software_graph.graphml` | Software-level directed graph (collapsed after process identities were preserved), self-loops included and flagged. |
| `full_graph.json` | Process nodes, process edges with evidence, software nodes and edges in one JSON. |

## data/processed
| file | content |
|---|---|
| `static_graph.json` | Raw analyzer output: instances (process + workflow), emit-level edges with channel trails, `unresolved`, `infeasible_edges_dropped`. |
| `process_instances.csv` | One row per process/workflow instance (fully-qualified call path, module file:line, call site, enclosing conditions, preview configs in which it appears). |
| `process_edges.csv` | One row per (source instance, source emit) -> (target instance, input index). Columns below. |
| `process_edges_evidence.jsonl` | Same rows plus declarations, condition lists and the complete channel trail (variable, file:line, operators). |
| `process_pairs.csv` | Edges collapsed over emits (instance pairs). |
| `process_software_map.csv` | Process instance -> primary canonical software, with meta.yml tools, environment.yml dependencies, topic version tools, mapping method and notes. |
| `canonical_software.csv`, `software_nodes.csv` | Canonical names, roles, `alternative_of`. |
| `software_edges.csv` | Software-level relationships with supporting process-edge counts, edge-class counts, confidence, self-loop flag, `only_reporting`, preview configs. |
| `manual_review.csv` | Low-confidence edges requiring review. |
| `dag_vs_static.json` | Per-configuration comparison between DAG-derived and static process pairs, including fused-node ("hub") analysis. |
| `executed_matrix.csv` | Instance x preview-configuration presence matrix (evidence that an instance is part of that configuration's DAG). |
| `validation_examples.csv`, `metro_vs_static.csv` | Validation outputs. |
| `summary_stats.json` | Headline counts. |

### process_edges.csv columns
`edge_id`, `src_instance`, `src_module`, `src_emit`, `dst_instance`, `dst_module`, `dst_input_index`,
`edge_class` (`direct`, `merged-channel`, `reporting-aggregation`, `key-only-synchronization`, `metadata-dependency`, `gating-or-metadata`),
`confidence` (`high`/`medium`/`low`), `evidence_tier` (`A-dag-confirmed`, `B-static-only`, `C-review`), `src_software`, `dst_software`,
`required_param_assumptions` (parameter atoms that must hold for the path to be live), `conditional`, `crosses_subworkflow_interface`,
`operators` (channel operators on the path), `consumer_call` / `producer_call` (`file:line`), `both_endpoints_in_configs`, `confirmed_by_hubfree_dag_in`.

### Definitions
* **direct** - the producer's channel reaches the consumer call through assignments, `map/filter/collect/...` and workflow take/emit only; no other process output is merged into it.
* **merged-channel** - the path includes `mix/join/combine/...`, so the consumed channel also carries other sources; the edge is real for at least the merge partner, payload attribution is ambiguous.
* **key-only-synchronization** - the producer channel was reduced to the sample key (`.map { meta, _x -> meta }`); the consumer waits for the producer but does not consume its data.
* **metadata-dependency** - producer output travels into `meta` (e.g. inferred strandedness) or acts as a gate.
* **reporting-aggregation** - consumer is MultiQC.
