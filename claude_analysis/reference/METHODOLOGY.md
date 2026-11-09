# Methodology (frozen release)

Pipeline: nf-core/rnaseq 3.27.0, commit `a1fcdddd3b826fe46eb46f0479f2ff8a7815af05`. Everything ran locally; no workflow was executed (only `nextflow run . -profile test -preview -with-dag`, Nextflow 26.10.5, Java 17, in WSL Ubuntu 22.04).

## 1. Definition
Software A → B holds when data produced by a process that runs A is consumed as an input of a process that runs B. Relationships are derived at **process-instance level** (fully qualified call path) and then collapsed to software; process identities are kept. Not used as evidence: source order, diagram proximity (the nf-core metro map was compared and found to be layout, 24 of 46 mappable connections coincide with a data edge), shared workflow membership, co-occurrence, shared inputs. No transitive closure.

## 2. Sources and their role
| source | role |
|---|---|
| Nextflow source (`main.nf`, `workflows/`, `subworkflows/`, `modules/`) | primary; read by a static channel-provenance analyzer and, for decisions, by hand |
| `-preview -with-dag` DAGs (10 configurations: test, hisat2, salmon_pseudo, kallisto, star_rsem, kraken2, kraken2_bracken, hisat2_kraken2_bracken, sentieon_star, parabricks_star) | corroboration and "which instances exist in a configuration"; **partly unreliable**: fused operator nodes create a 47-node cycle that does not exist at process level; 56–87 % of DAG process-to-process paths cross such a node |
| module `meta.yml`, `environment.yml`, `modules.json` | software identity; `meta.yml` tools are wrong for some modules (RSEM modules list `rseqc`) so the mapping is curated |
| `conf/modules/*.config`, `nextflow.config`, `utils_nfcore_rnaseq_pipeline` | parameters, ext.args, validation rules (e.g. Parabricks and Sentieon STAR cannot be combined) |

## 3. Pipeline of scripts (`scripts/reproduce_all.sh`)
1. `nf_static_analyzer.py` – symbolic execution of the entry workflow: each channel variable carries the set of (producer instance, emit) ports and its trail (variable, `file:line`, operators). Subworkflows are inlined; both branches of every `if/else` are explored and tagged with their condition; combinations with contradictory condition atoms are dropped (25 emit-edges, logged). Result: 178 process instances, 1,234 edges, 0 unresolved statements, process graph acyclic.
2. `build_datasets.py` – edge classes, evidence tiers, process→software map (curated `PRIMARY`/`CANON`), software collapse, **both confidence columns** (`confidence_v1` original, `confidence_v2` corrected) and the payload check.
3. `validate_examples.py`, `compare_metro.py` – the six requested examples; metro-map comparison.
4. Audit (`audit_dossier.py`, `audit_merged.py`, `curate_audit.py`, `audit_decisions.py`, `render_audit_report.py`) – manual adjudication of the 53 core pairs, payload audit of merged channels, negative controls, reconciliation (`audit/AUDIT_REPORT.md`).
5. `build_reference.py` → `reference/`; `validate_reference.py` → 44 checks; `make_manifest.py` → manifest and checksums.

## 4. Edge classes and evidence tiers
`direct` (single-source path), `merged-channel` (path includes `mix/join/combine/…`: payload attribution ambiguous), `reporting-aggregation` (consumer is MultiQC), `key-only-synchronization` (`.map { meta, _x -> meta }`), `metadata-dependency` and `gating-or-metadata` (output used as a gate / carried in `meta`).
Tier A = the process pair is also in a preview DAG without crossing a fused node; B = static only; C = sync/gate/metadata. Tier and confidence are independent axes (audit §2).

## 5. Confidence
* `confidence_v1` – original rule, preserved: high = `direct` and no alternative-branch flag. **Defect:** an if/else that assigns the same channel (e.g. tar vs directory for the Kraken2 database) demoted single-source edges to medium (69 tier-A edges, including `UNTAR → KRAKEN2/BRACKEN`). Exclusive branches are already recorded as conditions.
* `confidence_v2_rule` – canonical corrected rule: `rejected` if the payload check proves an extractor artifact or the pipeline forbids the flag combination; `low` for sync/gate/metadata; `high` for `direct`; `medium` for merged and reporting.
* `confidence_final` – v2 plus manual audit (edges of Gold/Silver pairs `high`; verified negatives `rejected`).
* **Payload check** (`payload_checks.py`): three source-verified false-positive mechanisms of a union-semantics analysis: (i) a closure drops the element (`_fai`, `_bai` underscore parameters), (ii) `multiMap` separates bam and index, (iii) a subworkflow called with a literal argument that disables a branch. Merged channels that survive are only *type-compatible*, not proven.

## 6. Decisions on the 53 core pairs
Pairs with a tier-A supporting edge were adjudicated by reading the producer's output declaration, the channel path and the consumer's input slot, and the module script where the consumed payload mattered. Gold/Silver/Negative rules: `reference/README.md`, full reasoning with `file:line`: `audit/curated/all_core_pair_decisions.csv`. Result: 29 Gold, 22 Silver, 2 Negative, 0 Unresolved.

## 7. Negative controls
Negative = no directed path from any process of A to any process of B in the extracted graph (all edges, including low-confidence ones) or only payload-free/rejected edges. Kinds: shared input (A and B consume the same producer output in a co-executed preview configuration), reverse of a verified flow (B cannot reach A anywhere), extractor artifact / key-only sync, mutually exclusive alternatives (contradictory conditions or pipeline validation), same sub-workflow scope. 19 were confirmed by reading the source (the BAM-consumer QC family, FastQC → Trim Galore, fastp vs Trim Galore, Parabricks vs Sentieon, the two extractor false positives); 127 are graph-computed. 37 pairs whose only edges are gates/metadata are Unresolved.

## 8. Limitations
1. **No execution.** Gold means verified in source for stated parameters; optional emits, empty channels and runtime `ext.args` are read, not observed. A `-stub` run would add task-level evidence.
2. **Single reviewer.** All adjudications and the curated software map were made by one reviewer (an AI assistant) against the source. No independent second annotation, no inter-annotator agreement.
3. **Software identity is a lossy projection** (one node, several operations; the "custom script" node merges distinct scripts; "sed" for `CUSTOM_RSEMMERGECOUNTS` is a version-reporting artifact). Use the `*_operations` columns and the process level.
4. **Coverage/recall is unknown and biased.** Gold derives from tier-A pairs; real flows whose DAG path is fused (STAR → Salmon via the transcriptome BAM) are only `algorithmic_supported`. 282 software pairs are unadjudicated.
5. **Parameter dependence.** Several positives exist only under non-default options; one derived selector (`contaminant_screening_input`) is documented in text, not as a condition atom. Condition atoms are matched by name across scopes.
6. **Negatives** assert absence in the extracted graph; flows through Groovy code not modelled (`for/while/switch/try`, closures calling processes: none occur in 3.27.0) would be missed. 127 negatives are unverified and some "shared input" claims hold only for configurations where no later step intervenes.
7. **Payload check is pattern-based**; there may be a further false-positive mechanism. The constant-argument rule is specific to `QUANTIFY_BAM_SALMON`.
8. **Single pipeline, single version.** Nothing here generalises beyond nf-core/rnaseq 3.27.0.
9. The first release's narrative reports (`../reports/`) describe the original v1 numbers (e.g. 53 "core" pairs, confidence classification) and are kept as history.
