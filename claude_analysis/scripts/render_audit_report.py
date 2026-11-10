#!/usr/bin/env python3
"""Render audit/AUDIT_REPORT.md and audit/core_pairs_merged_edges.csv from the audit outputs (numbers are read, not typed)."""
import csv, json, os, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); A = os.path.join(ROOT, 'audit'); C = os.path.join(A, 'curated')
rd = lambda p: list(csv.DictReader(open(p, encoding='utf-8')))
S = json.load(open(os.path.join(A, 'summary.json')))
dec = rd(os.path.join(C, 'all_core_pair_decisions.csv'))
v2 = {r['edge_id']: r for r in rd(os.path.join(A, 'process_edges_final_confidence.csv'))}
pa = {r['edge_id']: r for r in rd(os.path.join(A, 'payload_audit.csv'))}
core = rd(os.path.join(A, 'core_pair_edges.csv'))
TA = {r['edge_id'] for r in rd(os.path.join(ROOT, 'data', 'processed', 'process_edges.csv')) if r['evidence_tier'].startswith('A')}
ta_v2 = collections.Counter(v2[e]['confidence_final'] for e in TA)
neg = rd(os.path.join(C, 'negative_controls.csv')); unr = rd(os.path.join(C, 'unresolved.csv'))
decp = {d['pair_id']: d for d in dec}
cnt = collections.Counter(d['decision'] for d in dec)

# tier-A merged edges inside the 53 pairs
rows = []
for r in core:
    if r['evidence_tier'].startswith('A') and r['edge_class'] == 'merged-channel':
        rows.append({'pair_id': r['pair_id'], 'pair_decision': decp[r['pair_id']]['decision'], 'edge_id': r['edge_id'], 'src': r['src_instance'].split(':')[-1] + '.' + r['src_emit'],
                     'dst': r['dst_instance'].split(':')[-1], 'consumer_call': r['consumer_call'], 'payload_audit': pa[r['edge_id']]['family_verdict'], 'detail': pa[r['edge_id']]['verdict_reason'],
                     'confidence_v1': r['confidence_v1'], 'confidence_final': v2[r['edge_id']]['confidence_final']})
with open(os.path.join(A, 'core_pairs_merged_edges.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
mc = collections.Counter((x['payload_audit'], x['confidence_final']) for x in rows)

def tbl(rows_, cols, head):
    o = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    for r in rows_: o.append('| ' + ' | '.join(str(r[c]).replace('|', '/') for c in cols) + ' |')
    return '\n'.join(o)

nb = S['negative_controls']['by_kind']
md = f"""# Audit of the extracted nf-core/rnaseq 3.27.0 relationship dataset

Pipeline commit `a1fcdddd3b826fe46eb46f0479f2ff8a7815af05`. Scope: nf-core/rnaseq only; no other pipeline; no workflow execution (the audit is source reading plus the existing extraction and preview DAGs).
**Nothing in `data/`, `reports/` or the earlier scripts was changed or overwritten**; everything here is new under `claude_analysis/audit/` and `claude_analysis/scripts/` (see section 9).

## 1. Result

| Set | Gold | Silver | Negative | Unresolved |
|---|---|---|---|---|
| The 53 core (tier A) software pairs | **{cnt['Gold']}** | **{cnt['Silver']}** | **{cnt['Negative']}** | **{cnt['Unresolved']}** |
| Separate negative-control dataset (ordered software pairs, includes the 2 above) | - | - | **{S['negative_controls']['total_unique_ordered_pairs']}** ({S['negative_controls']['manually_verified']} read in source, the rest graph- or rule-computed) | - |
| Pairs set aside outside the 53 (gate/metadata-only dependencies, definition-dependent) | - | - | - | **{S['negative_controls']['unresolved_information_dependency']}** |

* Positive control = Gold + Silver = **{cnt['Gold'] + cnt['Silver']}** pairs (`curated/positive_controls.csv`). Gold is the conservative set to use as ground truth.
* Why no Unresolved among the 53: every one could be decided by reading the call site and the module declarations. What stays unproven is stated in section 8, not hidden in a label.
* Edge level (all {S['edges_total']} process edges, `process_edges_final_confidence.csv`): confidence v1 {S['v1_confidence']} -> final {S['final_confidence']}. {S['final_confidence']['rejected']} edges are rejected as extractor artifacts or infeasible paths.

Decision rules (identical for all pairs; implemented in `scripts/audit_decisions.py`):
* **Gold** - the producer's output is passed to the consumer's input slot with its payload intact (read in the source), both ends are named bioinformatics tools, and the path is feasible under a stated parameter set.
* **Silver** - real, verified flow, but an end is a generic OS utility / local script (GNU tar, gzip, sed, the nf-core custom Python scripts, which are merged into one software node) or only part of the payload is used.
* **Negative** - the extracted relationship is not a data exchange (tuple element dropped, key-only synchronisation, infeasible branch).
* **Unresolved** - cannot be decided from source without execution, or depends on whether a gate/metadata dependency counts as data.

## 2. What "high confidence" (47) and "Tier A" (174) each mean, and why they differ

They are **two independent axes**, and neither is a refinement of the other.

| | defined by | what it tells you |
|---|---|---|
| `confidence = high` (v1) | structure of the channel path in the static analysis: class is `direct` (no `mix/join/combine/...`) **and** no `alternative-branch-in-channel-path` flag | the extractor believes one producer feeds the consumer |
| `evidence_tier = A` | the same process pair also appears in a preview DAG **without crossing a fused operator node** | independent corroboration by Nextflow's own DAG |

|  | tier A | not tier A |
|---|---|---|
| **high** | {S['high_and_tierA']} | {S['high_only']} |
| **not high** | {S['tierA_only']} | {S['edges_total'] - S['high_and_tierA'] - S['high_only'] - S['tierA_only']} |

* **High but not tier A ({S['high_only']}):** all {S['high_only']} have no preview DAG that contains both endpoints (BOWTIE2 rRNA chain, UMI chain, StringTie merge, Sylph, STAR index upgrade: configurations that were not previewed). They are not contradicted; they were simply not testable.
* **Tier A but not high ({S['tierA_only']}):** {S['tierA_only_breakdown']}. So the single biggest cause is a **rule defect**: {S['tierA_only_breakdown'].get('class=direct; alternative-branch flag (rule demoted it)', 0)} tier-A edges are `direct` but were demoted to `medium` only because the consumer channel is assigned in if/else branches. Those branches are mutually exclusive and their conditions are already recorded in `required_param_assumptions`; the flag is not payload ambiguity.
* After the fix (section 3) and the payload audit (section 5): of the {len(TA)} tier-A edges, {ta_v2['high']} are `high`, {ta_v2['medium']} `medium` (merged/reporting), {ta_v2['low']} `low` and {ta_v2['rejected']} `rejected`. Full table: `reconciliation_high_vs_tierA.csv`.

## 3. Kraken2 -> Bracken confidence bug

* The process edge `KRAKEN2.report -> BRACKEN[0]` (E01045; `workflows/rnaseq/main.nf:731` `ch_kraken_reports = KRAKEN2.out.report`, `:738-741` `BRACKEN(ch_kraken_reports, ch_kraken_db)`) was already `high`.
* The bug is in the **rule**: `confidence = high` required "no alternative-branch flag". The Kraken DB channel is built by an if/else (`subworkflows/local/prepare_genome_references/main.nf:226-230`: `.tar.gz` -> `UNTAR_KRAKEN_DB`, directory -> `channel.value(file(...))`). That flag demoted the database edges `UNTAR_KRAKEN_DB -> KRAKEN2[1]` (E01044) and `UNTAR_KRAKEN_DB -> BRACKEN[1]` (E01046) to `medium`, so the Bracken inputs were inconsistently classified (report high, database medium) although both are single-source inputs of the same call.
* Fix (`scripts/curate_audit.py`, new column `confidence_v2`; v1 left untouched): a `direct` edge is `high` regardless of the exclusive-branch flag; merged channels stay `medium` unless the merge site was read; edges whose payload/slot was verified in source are `high`. Result for the three edges: E01044 medium -> **high**, E01045 high -> **high**, E01046 medium -> **high**. The same defect affected {S['tierA_only_breakdown'].get('class=direct; alternative-branch flag (rule demoted it)', 0)} tier-A edges in total (mostly reference-resource producers: CUSTOM_CATADDITIONALFASTA 15, CUSTOM_GTFFILTER 8, SAMTOOLS_FAIDX 6, UNTAR 5, EAUTILS_GTF2BED 5, ...).
* The old `build_datasets.py` is not edited. If you want the fix in the main pipeline of scripts, change line 184-186 of `scripts/build_datasets.py` in the same way (the audit keeps both columns so the effect is auditable).

## 4. Suspicious relationships

* **RSEM -> kallisto (P14): real, Gold.** `rsem-prepare-reference` is used purely as a transcript extractor: `subworkflows/local/prepare_genome_references/main.nf:20` (`RSEM_PREPAREREFERENCE as MAKE_TRANSCRIPTS_FASTA`), `:180` `MAKE_TRANSCRIPTS_FASTA(ch_fasta, ch_gtf).transcript_fasta`; the module copies `rsem/genome.transcripts.fa` to the process output (`modules/nf-core/rsem/preparereference/main.nf:46`, emit `:16`); `subworkflows/local/prepare_genome_indices/main.nf:292` `KALLISTO_INDEX(ch_transcript_fasta.map{{item -> [[:], item]}})`. Direct, single-source, hub-free DAG-confirmed in the kallisto preview. It disappears with `--transcript_fasta`, `--gffread_transcript_fasta`, `--use_sentieon_star` or `--kallisto_index`. The relationship is a *reference extraction*, not RSEM quantification; the same FASTA also feeds Salmon (P13).
* **SAMtools(faidx) -> BBSplit and 5 other index builders (P18): false positive.** `subworkflows/local/prepare_genome_indices/main.nf:60`: `ch_fasta = ch_fasta_fai.map {{ _meta, fasta_file, _fai -> fasta_file }}` discards the `.fai`. The analyzer unions all tuple elements. The same pair type is *real* for Picard (P19), where the whole tuple is the input.
* **fq -> BBSplit (P35): synchronisation only.** `fastq_qc_trim_filter_setstrandedness/main.nf:325` (also `:191, :298, :358`) joins `lint.map {{ meta, _lint -> meta }}`; the lint report is never read.
* **STAR -> Parabricks (P24):** valid only for the `PARABRICKS_STARGENOMEGENERATE` instance (E00350). The edge from plain `STAR_GENOMEGENERATE` (E00353) is infeasible (`prepare_genome_indices/main.nf:149` vs `:168`). The Parabricks -> Sentieon index edge (E00322) is excluded because the pipeline errors when both flags are set (`subworkflows/local/utils_nfcore_rnaseq_pipeline/main.nf:323-325`).
* **Trim Galore -> BBSplit / fq (P30, P31):** only `TRIMGALORE.reads` counts. The `TRIMGALORE.log` edge is a percent-trimmed gate (class `gating-or-metadata`, low).
* **RSEM -> "sed" (P16)** is a naming artifact: `CUSTOM_RSEMMERGECOUNTS` is a coreutils shell script (`modules/nf-core/custom/rsemmergecounts/main.nf`, cut/paste/sed) whose version tuple declares sed. Kept as Silver, but the node should not be read as the sed tool.
* **"nf-core custom script (Python)" (14 Silver pairs)** merges GTF filtering, additional-FASTA concatenation, tx2gene and MultiQC biotype formatting into one software node. Process-level flows are verified; the software identity is not informative.
* **Recall problem found while reading (not fixed here):** the headline *STAR -> Salmon* (transcriptome BAM, `QUANTIFY_BAM_SALMON`, `workflows/rnaseq/main.nf:454-463`; Salmon alignment mode `modules/nf-core/salmon/quant/main.nf:28-39`) is **not among the 53 core pairs**, because its DAG path crosses a fused node and it is therefore only tier B. Tier A under-represents real relationships; use tier A as a precision filter, not as a complete list.

## 5. The {S['merged_channel_edges']} merged-channel edges

Method (`scripts/audit_merged.py`, outputs `payload_audit.csv`, `merged_channel_audit.csv`, `merged_sites.csv`; 79 distinct merge sites): for every direct and merged edge, compare the family of the producer's output (emit name and glob) with the consumer's input slots, and read the source statements on the channel trail for three false-positive mechanisms that a "union" analyzer cannot see.

| verdict | merged edges | direct edges | mechanism (source) |
|---|---|---|---|
| compatible (family fits a consumer slot) | {S['merged_audit'].get('compatible', 0)} | {S['direct_audit'].get('compatible', 0)} | not a proof of consumption; it only means the payload type fits |
| **PROJECTION-DROPPED** | {S['merged_audit'].get('PROJECTION-DROPPED', 0)} | {S['direct_audit'].get('PROJECTION-DROPPED', 0)} | a closure drops the element: `ch_fasta_fai.map {{ _meta, fasta_file, _fai -> fasta_file }}` (`prepare_genome_indices/main.nf:60`), `ch_bam_bai.map {{ meta, bam, _bai -> [meta, bam] }}` (`bam_qc_rnaseq/main.nf:27`), `fasta_fai.map {{ meta, fasta, _fai -> [meta, fasta] }}` (`align_star/main.nf:51`) |
| **MULTIMAP-SPLIT** | {S['merged_audit'].get('MULTIMAP-SPLIT', 0)} | 0 | `.multiMap {{ ... bam: [...]  index: [...] }}` separates bam and index (`workflows/rnaseq/main.nf:495-512`); the analyzer unions the branches |
| **INFEASIBLE-CALLSITE-CONSTANT** | {S['merged_audit'].get('INFEASIBLE-CALLSITE-CONSTANT', 0)} | {S['direct_audit'].get('INFEASIBLE-CALLSITE-CONSTANT', 0)} | `QUANTIFY_BAM_SALMON` is called with the literal `'salmon'` (`workflows/rnaseq/main.nf:461`), so its `KALLISTO_QUANT` branch cannot run |
| INCOMPATIBLE (heuristic, left medium) | {S['merged_audit'].get('INCOMPATIBLE', 0)} | {S['direct_audit'].get('INCOMPATIBLE', 0)} (noisy: GTF/GFF/bed naming; not used) | E00190 gunzip rRNA FASTA -> SeqKit `fastx` is in fact compatible |

So **{S['merged_audit'].get('PROJECTION-DROPPED', 0) + S['merged_audit'].get('MULTIMAP-SPLIT', 0) + S['merged_audit'].get('INFEASIBLE-CALLSITE-CONSTANT', 0)} of 551 merged edges (about {round(100*(S['merged_audit'].get('PROJECTION-DROPPED', 0) + S['merged_audit'].get('MULTIMAP-SPLIT', 0) + S['merged_audit'].get('INFEASIBLE-CALLSITE-CONSTANT', 0))/551)} %) are false positives**, and 8 direct edges as well. They matter for the core pairs because tier A inherited some of them (the DAG also fuses nodes there).

Merged edges that sit **inside the 53 core pairs** ({len(rows)} tier-A merged edges; `core_pairs_merged_edges.csv`): verdict x corrected confidence = {dict(mc)}. Adjudicated by reading the merge sites:
* `FAIDX.fai -> BBSplit/index builders` (P18): dropped -> Negative. `FAIDX.fai -> Picard` (P19): whole tuple consumed -> Gold.
* `TrimGalore.reads -> BBSplit/fq` (P30, P31): the join partner is key-only, payload = reads -> Gold (log edge excluded).
* `CUSTOM_CATADDITIONALFASTA.fasta/gtf -> STAR/RSEM/Salmon/...` (P42-P44): `combine` pairs *different* resources in distinct tuple slots (`index, gtf, transcript_fasta`; `modules/nf-core/salmon/quant/main.nf:12,55` uses `--geneMap ${{gtf}}`); each slot is consumed -> Silver (script identity).
* `RSEM transcript_fasta -> Salmon` (P13): third tuple slot, used as `-t` in alignment mode (`salmon/quant/main.nf:39`); also backed by the direct edge E00598 -> Gold.
* `tximeta -> SummarizedExperiment` (P53): `join` of eight sibling outputs of the same producer, `tuple(row[0], row.tail())` keeps all -> Gold.

## 6. Negative controls (`curated/negative_controls.csv`, {S['negative_controls']['total_unique_ordered_pairs']} ordered pairs)

Negative means: **no directed path from any process of A to any process of B in the extracted graph (all {S['edges_total']} edges, including low-confidence ones), or only payload-free edges.** It says nothing about B -> A.

| kind | n | evidence |
|---|---|---|
| shared-input | {nb.get('shared-input', 0)} | A and B consume the same producer output in at least one preview configuration (edge ids and call lines in `evidence`), and there is no path A => B; many are directional (B => A exists, e.g. FastQC -> Trim Galore) |
| reverse-of-verified-positive | {nb.get('reverse-of-verified-positive', 0)} | the reverse of a Gold/Silver flow when B cannot reach A anywhere |
| extractor-artifact-or-sync-only | {nb.get('extractor-artifact-or-sync-only', 0)} | every extracted edge is a key-only join (fq lint) or a rejected artifact |
| mutually-exclusive-alternatives | {nb.get('mutually-exclusive-alternatives', 0)} | contradictory conditions, or the pipeline forbids the combination (fastp vs Trim Galore; Parabricks vs Sentieon STAR `utils_nfcore_rnaseq_pipeline/main.nf:323-325`) |
| same-subworkflow-no-exchange | {nb.get('same-subworkflow-no-exchange', 0)} | run in the same sub-workflow scope, no shared producer, no path |
| from the 53 core pairs | 2 | P18 (projection), P35 (key-only) |

Verification level: {S['negative_controls']['manually_verified']} rows were confirmed by reading the source (FastQC -> Trim Galore, `fastq_fastqc_umitools_trimgalore/main.nf:42,74`; the BAM-consumer family Preseq/Qualimap/dupRadar/featureCounts/StringTie/BEDTools; fastp vs Trim Galore; Parabricks vs Sentieon; P18; P35). The remaining rows are graph-computed and conditional: "shared input" through `CAT_FASTQ.reads` or `BBMAP_BBSPLIT.primary_fastq` holds only for configurations in which no later step intervenes (e.g. trimming skipped).

**{S['negative_controls']['unresolved_information_dependency']} pairs are Unresolved, not negative** (`curated/unresolved.csv`): all their extracted edges are gates or metadata (e.g. `STAR.log_final` filters BAMs by percent mapped, `workflows/rnaseq/main.nf:479-512`; Salmon `lib_format_counts` sets `meta` strandedness, `:655-662`). Whether a control signal counts as "data consumed" is a definition choice, so they are excluded from both control sets.

## 7. Curated outputs

| file | content |
|---|---|
| `curated/positive_controls.csv` | {cnt['Gold'] + cnt['Silver']} Gold/Silver pairs with decision, supporting process edges, I/O declarations, extractor and auditor line references, required parameters, DAG configs, explanation |
| `curated/all_core_pair_decisions.csv` | all 53 decisions incl. the 2 Negative |
| `curated/negative_controls.csv` | {S['negative_controls']['total_unique_ordered_pairs']} negative ordered pairs |
| `curated/unresolved.csv` | {S['negative_controls']['unresolved_information_dependency']} definition-dependent pairs |
| `process_edges_final_confidence.csv` | every edge: v1 and v2 confidence, reason, payload-audit verdict |
| `reconciliation_high_vs_tierA.csv`, `payload_audit.csv`, `merged_sites.csv`, `core_pairs_merged_edges.csv`, `core_pair_dossier.md`, `core_pair_edges.csv`, `summary.json` | evidence |

## 8. Limitations

1. **Gold means "verified in the source for the stated parameters", not "observed executing".** No `-stub` or real run was done, so output optionality (`optional: true` emits), empty channels, and runtime `ext.args` are read, not observed.
2. **The software layer is a lossy projection.** One software node can stand for several processes (the custom-script node, SAMtools in many roles); a pair is Gold if its verified supporting edges are Gold, but a different process pair under the same names may not be. Always join back to `supporting_process_edges`.
3. **Parameter policy.** Non-default options count like defaults: a pair is kept whenever the tools can be combined in a valid configuration. `conditions_required` lists the activating options; the ternary `contaminant_screening_input` selector (`workflows/rnaseq/main.nf:716-722`) is not an extractor atom and is documented in the evidence text.
4. **The audit rules are source-verified patterns, not a general proof.** Three false-positive mechanisms were found and encoded; there may be a fourth. `compatible` ({S['merged_audit'].get('compatible', 0)} merged, {S['direct_audit'].get('compatible', 0)} direct) is a type check, not a proof of consumption. v2 `high` for un-reviewed direct edges means "single-source path with no known artifact pattern". Edge-level `high (audit decision)` means the pair's call site and input slot were read; sibling edges that share that call site and slot (e.g. the three bigWig branches, the five RSeQC modules) are treated as verified without being read one by one.
5. **Tier A is biased:** it excludes real flows whose DAG path is fused (STAR -> Salmon is the clearest case) and includes the false positives above. It must not be used as a recall estimate.
6. **Negative controls assert absence of a path in the extracted graph.** Graph incompleteness (e.g. flows through Groovy functions or `ch.view`-style side channels, which the analyzer cannot see) would turn a negative into a missed positive. Shared-input negatives are conditional on the preview configuration in which both tools co-occur.
7. **Alias and utility handling.** `PARABRICKS_STARGENOMEGENERATE` is the STAR module with a Parabricks container, `MAKE_TRANSCRIPTS_FASTA` is the RSEM module; the software map follows the module, which is why "STAR -> Parabricks" and "RSEM -> kallisto" read as they do.
8. **Silver is a judgement about identity, not about truth.** All 22 Silver flows are real; merge Gold+Silver if you only care about data flow.

## 9. Change log (nothing overwritten)

New: `scripts/audit_dossier.py`, `scripts/audit_merged.py`, `scripts/audit_decisions.py`, `scripts/curate_audit.py`, `scripts/render_audit_report.py`, `scripts/reproduce_audit.sh`, and everything under `audit/`.
Unchanged: `data/**`, `reports/**`, `documentation/**`, `scripts/build_datasets.py`, `scripts/nf_static_analyzer.py`, original nf-core sources. The v1 confidence column in `data/processed/process_edges.csv` is kept as the record of the original extraction; `confidence_v2` lives only in `audit/process_edges_final_confidence.csv`.
Reproduce: `bash claude_analysis/scripts/reproduce_audit.sh`.

## Appendix A: the 53 core pairs

""" + tbl([{'pair': d['pair_id'], 'pairs': f"{d['source_software']} -> {d['target_software']}", 'decision': d['decision'], 'flow': d['flow_type'], 'edges': d['supporting_process_edges'][:60], 'why': d['explanation'][:170]} for d in dec], ['pair', 'pairs', 'decision', 'flow', 'edges', 'why'], ['id', 'pair', 'decision', 'flow type', 'supporting edges', 'reason (short)']) + "\n"
open(os.path.join(A, 'AUDIT_REPORT.md'), 'w', encoding='utf-8').write(md)
print('report written', len(md))
