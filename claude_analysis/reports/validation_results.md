# Validation results (summary)

| check | result |
|---|---|
| Static process graph acyclic | 0 SCCs among 178 instances |
| Hub-free DAG edges contradicted by static graph | 0 in 10/10 preview DAGs (`dag_only_hubfree`) |
| DAG instances missing from static analysis | 0 in 10/10 DAGs |
| Negative control FastQC -> Trim Galore | 0 edges |
| Metro-map connections backed by a data edge | 24 of 46 mappable (22 are layout order; 8 unmappable) |
| Edges dropped as logically infeasible | 25 (audit list in `static_graph.json`) |
Details per example: `validation_examples.md`. Per-configuration DAG numbers: `data/processed/dag_vs_static.json`.
Not validated: payload-level correctness of merged-channel edges (needs stub run or manual review); tier A is DAG-consistent, not manually proven.
