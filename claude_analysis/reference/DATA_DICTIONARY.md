# Data dictionary (reference/)

All CSVs: UTF-8, `\n` line endings, comma separated, header row, sorted deterministically. Multi-valued cells use `;` (ids, processes) or ` | ` (operations). Booleans are `True`/`False`. Parquet copies hold the same columns as strings.

## software_level/*.csv  (one row per **ordered** software pair; key = `source_software` + `target_software`, also `software_pair_id`)

| column | meaning |
|---|---|
| `software_pair_id` | `SW0001…`, stable only within one build (key on the software names) |
| `source_software`, `target_software` | canonical software names; the producer is the source. Nodes are curated per process module (`data/processed/process_software_map.csv`) |
| `category` | `Gold`, `Silver`, `Negative_verified`, `Negative_unverified`, `Unresolved`, `Algorithmic_supported` (see below) |
| `validation_category` | `source_verified_positive` · `source_verified_negative` · `algorithmic_negative_candidate` · `unresolved` · `algorithmic_supported` |
| `validation_subtype` | Gold/Silver: `analysis-data`, `reference-resource`, `utility-script`, `utility staging`, `partial-payload`. Negatives: `shared-input`, `reverse-of-verified-positive`, `extractor-artifact-or-sync-only`, `extractor-false-positive`, `key-only-synchronisation`, `mutually-exclusive-alternatives`, `same-subworkflow-no-exchange`. Unresolved: `information-dependency`. Other: `static_channel_provenance`, `self_loop` |
| `decision_confidence` | confidence in the *label* (high/medium/low) |
| `pair_id` | `P01…P53` for the 53 core (tier A) pairs of the audit, else empty |
| `flow_type` | what moves: `analysis-data`, `reference-resource` (index, FASTA, GTF, chrom.sizes), `utility-script`, `utility staging`, `partial-payload` |
| `identity_flag` | `weak-identity (utility / local script)` when an end is tar/gzip/sed/custom script |
| `is_self_loop` | source = target (different processes of the same software) |
| `only_reporting` | every supporting edge goes into MultiQC |
| `n_process_edges`, `process_edge_ids` | supporting process-level edges (`edge_id` in `process_level/`). For Gold/Silver only the source-verified ones; for negatives the extracted edges between the two tools (all rejected / payload-free), possibly none |
| `source_processes`, `target_processes` | process (call) names of the supporting edges |
| `source_operations`, `target_operations` | **the operation actually performed** (e.g. `rsem-prepare-reference used only to extract the transcriptome FASTA (no RSEM quantification)`); software identity alone is not the operation |
| `required_params` | parameter atoms that must hold (Gold/Silver; first supporting edge) |
| `hubfree_dag_configs` | preview configurations (`data/raw/<label>_dag.html`) whose Nextflow DAG contains the process pair without crossing a fused operator node |
| `in_default_test_profile` | informational only: some supporting edge has both endpoints in the default `-profile test` DAG. Does not affect `category` |
| `evidence_basis` | for Gold/Silver/Negative_verified: the source lines read (`file:line`); for unverified negatives: rule and evidence |
| `explanation` | one-paragraph rationale (conditions, caveats) |

### Categories
* **Gold** – payload verified to reach the consumer's input slot; both ends named tools; feasible under stated parameters.
* **Silver** – real, verified flow; an end is a generic utility / local script, or only part of the payload is consumed.
* **Negative_verified** – no data exchange, confirmed by reading the source (19).
* **Negative_unverified** – candidate negative from the algorithm: no directed path from any process of A to any process of B in the extracted graph (all 1,234 edges, incl. low-confidence), plus one of: shared input in a co-executed preview configuration / reverse of a verified flow / only payload-free or rejected edges / contradictory conditions / same sub-workflow scope. It says nothing about B → A.
* **Unresolved** – only gate / metadata dependencies (e.g. `STAR.log_final` filters BAMs by percent mapped; Salmon `lib_format_counts` sets `meta` strandedness).
* **Algorithmic_supported** – extracted and not rejected, not adjudicated; **not a control**.

## process_level/process_relationships_all.csv  (one row per edge: source instance + emit → target instance + input slot)

| column | meaning |
|---|---|
| `edge_id` | `E00001…`, stable for a given source commit and analyzer version |
| `validation_category`, `validation_subtype`, `validation_basis` | `source_verified_positive` (115) · `source_verified_negative` (5) · `algorithmic_supported` (814) · `algorithmic_negative_candidate` (172: `payload_check_rejected` 78, `key_only_synchronisation` 94) · `unresolved` (128: `gate_or_metadata`) |
| `pair_id` | core pair `P01…P53` the edge supports (verified edges only) |
| `src_instance`, `dst_instance` | fully qualified call path, e.g. `NFCORE_RNASEQ:RNASEQ:ALIGN_STAR:STAR_ALIGN` |
| `src_process`, `dst_process` | last path element (call alias, e.g. `MAKE_TRANSCRIPTS_FASTA`) |
| `src_module`, `dst_module` | underlying nf-core/local module (e.g. `RSEM_PREPAREREFERENCE`) |
| `src_emit`, `dst_input_index` | output name of the producer; 0-based input slot of the consumer |
| `src_software`, `dst_software` | canonical software of the process (curated) |
| `src_operation`, `dst_operation` | operation performed by the process |
| `edge_class` | `direct`, `merged-channel`, `reporting-aggregation`, `key-only-synchronization`, `metadata-dependency`, `gating-or-metadata` |
| `evidence_tier` | `A-dag-confirmed`, `B-static-only`, `C-review` (see `documentation/data_dictionary.md`) |
| `confidence_v1` | **original** rule (kept for comparison): high = direct and no alternative-branch flag. Known defect: exclusive if/else branches demoted direct edges |
| `confidence_v2_rule` | corrected canonical rule (`build_datasets.py`): rejected (payload check / pipeline-forbidden flag combination) · low (sync/gate/metadata) · high (direct) · medium (merged / reporting) |
| `confidence_final` | `confidence_v2_rule` plus the manual audit: verified edges `high`, verified-negative `rejected` |
| `payload_check` | `compatible`, `unknown-producer-family`, `INCOMPATIBLE` (heuristic, never used to reject), `PROJECTION-DROPPED`, `MULTIMAP-SPLIT`, `INFEASIBLE-CALLSITE-CONSTANT`, `not-checked` (only direct and merged edges are checked) |
| `required_params`, `conditional` | parameter atoms under which the edge exists; whether any condition applies |
| `producer_call`, `consumer_call` | `file:line` of the producer's / consumer's call (repo-relative) |
| `src_module_file`, `dst_module_file` | `file:line` of the module declarations |
| `src_output_decl`, `dst_input_decl` | the output / input declarations read from the module |
| `operators` | channel operators on the path |
| `hubfree_dag_configs`, `configs_with_both_endpoints` | preview configurations confirming the pair / containing both processes |
| `in_default_test_profile` | informational only: both endpoints are in the default `-profile test` DAG. Does not affect the category |

## Other
* `MANIFEST.json` – pipeline, commit, date, tool versions, record counts, checksums, preview-DAG input hashes.
* `SHA256SUMS` – checksums of all frozen text outputs (not parquet, not the manifest).
* `VALIDATION_SUMMARY.md`, `validation.json` – results of the validation checks (44 at freeze).
* `_build_counts.json` – counts written by the build.
* Audit evidence: `../audit/` (decisions with `file:line`, payload audit, reconciliation of high-confidence vs tier A, negative-control construction). Original results: `../data/processed_v1_original/` (frozen v1 snapshot).
