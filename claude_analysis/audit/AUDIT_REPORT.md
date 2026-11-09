# Audit of the extracted nf-core/rnaseq 3.27.0 relationship dataset

Pipeline commit `a1fcdddd3b826fe46eb46f0479f2ff8a7815af05`. Scope: nf-core/rnaseq only; no other pipeline; no workflow execution (the audit is source reading plus the existing extraction and preview DAGs).
**Nothing in `data/`, `reports/` or the earlier scripts was changed or overwritten**; everything here is new under `claude_analysis/audit/` and `claude_analysis/scripts/` (see section 9).

## 1. Result

| Set | Gold | Silver | Negative | Unresolved |
|---|---|---|---|---|
| The 53 core (tier A) software pairs | **29** | **22** | **2** | **0** |
| Separate negative-control dataset (ordered software pairs, includes the 2 above) | - | - | **146** (19 read in source, the rest graph- or rule-computed) | - |
| Pairs set aside outside the 53 (gate/metadata-only dependencies, definition-dependent) | - | - | - | **37** |

* Positive control = Gold + Silver = **51** pairs (`curated/positive_controls.csv`). Gold is the conservative set to use as ground truth.
* Why no Unresolved among the 53: every one could be decided by reading the call site and the module declarations. What stays unproven is stated in section 8, not hidden in a label.
* Edge level (all 1234 process edges, `process_edges_v2.csv`): confidence v1 {'medium': 963, 'high': 47, 'low': 224} -> v2 {'high': 382, 'medium': 547, 'rejected': 83, 'low': 222}. 83 edges are rejected as extractor artifacts or infeasible paths.

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
| **high** | 26 | 21 |
| **not high** | 148 | 1039 |

* **High but not tier A (21):** all 21 have no preview DAG that contains both endpoints (BOWTIE2 rRNA chain, UMI chain, StringTie merge, Sylph, STAR index upgrade: configurations that were not previewed). They are not contradicted; they were simply not testable.
* **Tier A but not high (148):** {'class=direct; alternative-branch flag (rule demoted it)': 69, 'class=merged-channel': 35, 'class=gating-or-metadata': 2, 'class=key-only-synchronization': 1, 'class=reporting-aggregation': 41}. So the single biggest cause is a **rule defect**: 69 tier-A edges are `direct` but were demoted to `medium` only because the consumer channel is assigned in if/else branches. Those branches are mutually exclusive and their conditions are already recorded in `required_param_assumptions`; the flag is not payload ambiguity.
* After the fix (section 3) and the payload audit (section 5): of the 174 tier-A edges, 128 are `high`, 42 `medium` (merged/reporting), 2 `low` and 2 `rejected`. Full table: `reconciliation_high_vs_tierA.csv`.

## 3. Kraken2 -> Bracken confidence bug

* The process edge `KRAKEN2.report -> BRACKEN[0]` (E01045; `workflows/rnaseq/main.nf:731` `ch_kraken_reports = KRAKEN2.out.report`, `:738-741` `BRACKEN(ch_kraken_reports, ch_kraken_db)`) was already `high`.
* The bug is in the **rule**: `confidence = high` required "no alternative-branch flag". The Kraken DB channel is built by an if/else (`subworkflows/local/prepare_genome_references/main.nf:226-230`: `.tar.gz` -> `UNTAR_KRAKEN_DB`, directory -> `channel.value(file(...))`). That flag demoted the database edges `UNTAR_KRAKEN_DB -> KRAKEN2[1]` (E01044) and `UNTAR_KRAKEN_DB -> BRACKEN[1]` (E01046) to `medium`, so the Bracken inputs were inconsistently classified (report high, database medium) although both are single-source inputs of the same call.
* Fix (`scripts/curate_audit.py`, new column `confidence_v2`; v1 left untouched): a `direct` edge is `high` regardless of the exclusive-branch flag; merged channels stay `medium` unless the merge site was read; edges whose payload/slot was verified in source are `high`. Result for the three edges: E01044 medium -> **high**, E01045 high -> **high**, E01046 medium -> **high**. The same defect affected 69 tier-A edges in total (mostly reference-resource producers: CUSTOM_CATADDITIONALFASTA 15, CUSTOM_GTFFILTER 8, SAMTOOLS_FAIDX 6, UNTAR 5, EAUTILS_GTF2BED 5, ...).
* The old `build_datasets.py` is not edited. If you want the fix in the main pipeline of scripts, change line 184-186 of `scripts/build_datasets.py` in the same way (the audit keeps both columns so the effect is auditable).

## 4. Suspicious relationships

* **RSEM -> kallisto (P14): real, Gold.** `rsem-prepare-reference` is used purely as a transcript extractor: `subworkflows/local/prepare_genome_references/main.nf:20` (`RSEM_PREPAREREFERENCE as MAKE_TRANSCRIPTS_FASTA`), `:180` `MAKE_TRANSCRIPTS_FASTA(ch_fasta, ch_gtf).transcript_fasta`; the module copies `rsem/genome.transcripts.fa` to the process output (`modules/nf-core/rsem/preparereference/main.nf:46`, emit `:16`); `subworkflows/local/prepare_genome_indices/main.nf:292` `KALLISTO_INDEX(ch_transcript_fasta.map{item -> [[:], item]})`. Direct, single-source, hub-free DAG-confirmed in the kallisto preview. It disappears with `--transcript_fasta`, `--gffread_transcript_fasta`, `--use_sentieon_star` or `--kallisto_index`. The relationship is a *reference extraction*, not RSEM quantification; the same FASTA also feeds Salmon (P13).
* **SAMtools(faidx) -> BBSplit and 5 other index builders (P18): false positive.** `subworkflows/local/prepare_genome_indices/main.nf:60`: `ch_fasta = ch_fasta_fai.map { _meta, fasta_file, _fai -> fasta_file }` discards the `.fai`. The analyzer unions all tuple elements. The same pair type is *real* for Picard (P19), where the whole tuple is the input.
* **fq -> BBSplit (P35): synchronisation only.** `fastq_qc_trim_filter_setstrandedness/main.nf:325` (also `:191, :298, :358`) joins `lint.map { meta, _lint -> meta }`; the lint report is never read.
* **STAR -> Parabricks (P24):** valid only for the `PARABRICKS_STARGENOMEGENERATE` instance (E00350). The edge from plain `STAR_GENOMEGENERATE` (E00353) is infeasible (`prepare_genome_indices/main.nf:149` vs `:168`). The Parabricks -> Sentieon index edge (E00322) is excluded because the pipeline errors when both flags are set (`subworkflows/local/utils_nfcore_rnaseq_pipeline/main.nf:323-325`).
* **Trim Galore -> BBSplit / fq (P30, P31):** only `TRIMGALORE.reads` counts. The `TRIMGALORE.log` edge is a percent-trimmed gate (class `gating-or-metadata`, low).
* **RSEM -> "sed" (P16)** is a naming artifact: `CUSTOM_RSEMMERGECOUNTS` is a coreutils shell script (`modules/nf-core/custom/rsemmergecounts/main.nf`, cut/paste/sed) whose version tuple declares sed. Kept as Silver, but the node should not be read as the sed tool.
* **"nf-core custom script (Python)" (14 Silver pairs)** merges GTF filtering, additional-FASTA concatenation, tx2gene and MultiQC biotype formatting into one software node. Process-level flows are verified; the software identity is not informative.
* **Recall problem found while reading (not fixed here):** the headline *STAR -> Salmon* (transcriptome BAM, `QUANTIFY_BAM_SALMON`, `workflows/rnaseq/main.nf:454-463`; Salmon alignment mode `modules/nf-core/salmon/quant/main.nf:28-39`) is **not among the 53 core pairs**, because its DAG path crosses a fused node and it is therefore only tier B. Tier A under-represents real relationships; use tier A as a precision filter, not as a complete list.

## 5. The 551 merged-channel edges

Method (`scripts/audit_merged.py`, outputs `payload_audit.csv`, `merged_channel_audit.csv`, `merged_sites.csv`; 79 distinct merge sites): for every direct and merged edge, compare the family of the producer's output (emit name and glob) with the consumer's input slots, and read the source statements on the channel trail for three false-positive mechanisms that a "union" analyzer cannot see.

| verdict | merged edges | direct edges | mechanism (source) |
|---|---|---|---|
| compatible (family fits a consumer slot) | 479 | 281 | not a proof of consumption; it only means the payload type fits |
| **PROJECTION-DROPPED** | 31 | 4 | a closure drops the element: `ch_fasta_fai.map { _meta, fasta_file, _fai -> fasta_file }` (`prepare_genome_indices/main.nf:60`), `ch_bam_bai.map { meta, bam, _bai -> [meta, bam] }` (`bam_qc_rnaseq/main.nf:29`), `fasta_fai.map { meta, fasta, _fai -> [meta, fasta] }` (`align_star/main.nf:51`) |
| **MULTIMAP-SPLIT** | 34 | 0 | `.multiMap { ... bam: [...]  index: [...] }` separates bam and index (`workflows/rnaseq/main.nf:495-512`); the analyzer unions the branches |
| **INFEASIBLE-CALLSITE-CONSTANT** | 6 | 4 | `QUANTIFY_BAM_SALMON` is called with the literal `'salmon'` (`workflows/rnaseq/main.nf:461`), so its `KALLISTO_QUANT` branch cannot run |
| INCOMPATIBLE (heuristic, left medium) | 1 | 49 (noisy: GTF/GFF/bed naming; not used) | E00190 gunzip rRNA FASTA -> SeqKit `fastx` is in fact compatible |

So **71 of 551 merged edges (about 13 %) are false positives**, and 8 direct edges as well. They matter for the core pairs because tier A inherited some of them (the DAG also fuses nodes there).

Merged edges that sit **inside the 53 core pairs** (34 tier-A merged edges; `core_pairs_merged_edges.csv`): verdict x corrected confidence = {('compatible', 'high'): 33, ('PROJECTION-DROPPED', 'rejected'): 1}. Adjudicated by reading the merge sites:
* `FAIDX.fai -> BBSplit/index builders` (P18): dropped -> Negative. `FAIDX.fai -> Picard` (P19): whole tuple consumed -> Gold.
* `TrimGalore.reads -> BBSplit/fq` (P30, P31): the join partner is key-only, payload = reads -> Gold (log edge excluded).
* `CUSTOM_CATADDITIONALFASTA.fasta/gtf -> STAR/RSEM/Salmon/...` (P42-P44): `combine` pairs *different* resources in distinct tuple slots (`index, gtf, transcript_fasta`; `modules/nf-core/salmon/quant/main.nf:12,55` uses `--geneMap ${gtf}`); each slot is consumed -> Silver (script identity).
* `RSEM transcript_fasta -> Salmon` (P13): third tuple slot, used as `-t` in alignment mode (`salmon/quant/main.nf:39`); also backed by the direct edge E00598 -> Gold.
* `tximeta -> SummarizedExperiment` (P53): `join` of eight sibling outputs of the same producer, `tuple(row[0], row.tail())` keeps all -> Gold.

## 6. Negative controls (`curated/negative_controls.csv`, 146 ordered pairs)

Negative means: **no directed path from any process of A to any process of B in the extracted graph (all 1234 edges, including low-confidence ones), or only payload-free edges.** It says nothing about B -> A.

| kind | n | evidence |
|---|---|---|
| shared-input | 96 | A and B consume the same producer output in at least one preview configuration (edge ids and call lines in `evidence`), and there is no path A => B; many are directional (B => A exists, e.g. FastQC -> Trim Galore) |
| reverse-of-verified-positive | 21 | the reverse of a Gold/Silver flow when B cannot reach A anywhere |
| extractor-artifact-or-sync-only | 18 | every extracted edge is a key-only join (fq lint) or a rejected artifact |
| mutually-exclusive-alternatives | 7 | contradictory conditions, or the pipeline forbids the combination (fastp vs Trim Galore; Parabricks vs Sentieon STAR `utils_nfcore_rnaseq_pipeline/main.nf:323-325`) |
| same-subworkflow-no-exchange | 2 | run in the same sub-workflow scope, no shared producer, no path |
| from the 53 core pairs | 2 | P18 (projection), P35 (key-only) |

Verification level: 19 rows were confirmed by reading the source (FastQC -> Trim Galore, `fastq_fastqc_umitools_trimgalore/main.nf:42,74`; the BAM-consumer family Preseq/Qualimap/dupRadar/featureCounts/StringTie/BEDTools; fastp vs Trim Galore; Parabricks vs Sentieon; P18; P35). The remaining rows are graph-computed and conditional: "shared input" through `CAT_FASTQ.reads` or `BBMAP_BBSPLIT.primary_fastq` holds only for configurations in which no later step intervenes (e.g. trimming skipped).

**37 pairs are Unresolved, not negative** (`curated/unresolved.csv`): all their extracted edges are gates or metadata (e.g. `STAR.log_final` filters BAMs by percent mapped, `workflows/rnaseq/main.nf:479-512`; Salmon `lib_format_counts` sets `meta` strandedness, `:655-662`). Whether a control signal counts as "data consumed" is a definition choice, so they are excluded from both control sets.

## 7. Curated outputs

| file | content |
|---|---|
| `curated/positive_controls.csv` | 51 Gold/Silver pairs with decision, supporting process edges, I/O declarations, extractor and auditor line references, required parameters, DAG configs, explanation |
| `curated/all_core_pair_decisions.csv` | all 53 decisions incl. the 2 Negative |
| `curated/negative_controls.csv` | 146 negative ordered pairs |
| `curated/unresolved.csv` | 37 definition-dependent pairs |
| `process_edges_v2.csv` | every edge: v1 and v2 confidence, reason, payload-audit verdict |
| `reconciliation_high_vs_tierA.csv`, `payload_audit.csv`, `merged_sites.csv`, `core_pairs_merged_edges.csv`, `core_pair_dossier.md`, `core_pair_edges.csv`, `summary.json` | evidence |

## 8. Limitations

1. **Gold means "verified in the source for the stated parameters", not "observed executing".** No `-stub` or real run was done, so output optionality (`optional: true` emits), empty channels, and runtime `ext.args` are read, not observed.
2. **The software layer is a lossy projection.** One software node can stand for several processes (the custom-script node, SAMtools in many roles); a pair is Gold if its verified supporting edges are Gold, but a different process pair under the same names may not be. Always join back to `supporting_process_edges`.
3. **Parameter dependence.** Several Gold pairs exist only under non-default options (Parabricks, Sentieon, UMI, Kraken/Bracken, kallisto, `--additional_fasta`). `conditions_required` lists the atoms the extractor recorded; the ternary `contaminant_screening_input` selector (`workflows/rnaseq/main.nf:716-722`) is not an extractor atom and is documented in the evidence text instead.
4. **The audit rules are source-verified patterns, not a general proof.** Three false-positive mechanisms were found and encoded; there may be a fourth. `compatible` (479 merged, 281 direct) is a type check, not a proof of consumption. v2 `high` for un-reviewed direct edges means "single-source path with no known artifact pattern". Edge-level `high (audit decision)` means the pair's call site and input slot were read; sibling edges that share that call site and slot (e.g. the three bigWig branches, the five RSeQC modules) are treated as verified without being read one by one.
5. **Tier A is biased:** it excludes real flows whose DAG path is fused (STAR -> Salmon is the clearest case) and includes the false positives above. It must not be used as a recall estimate.
6. **Negative controls assert absence of a path in the extracted graph.** Graph incompleteness (e.g. flows through Groovy functions or `ch.view`-style side channels, which the analyzer cannot see) would turn a negative into a missed positive. Shared-input negatives are conditional on the preview configuration in which both tools co-occur.
7. **Alias and utility handling.** `PARABRICKS_STARGENOMEGENERATE` is the STAR module with a Parabricks container, `MAKE_TRANSCRIPTS_FASTA` is the RSEM module; the software map follows the module, which is why "STAR -> Parabricks" and "RSEM -> kallisto" read as they do.
8. **Silver is a judgement about identity, not about truth.** All 22 Silver flows are real; merge Gold+Silver if you only care about data flow.

## 9. Change log (nothing overwritten)

New: `scripts/audit_dossier.py`, `scripts/audit_merged.py`, `scripts/audit_decisions.py`, `scripts/curate_audit.py`, `scripts/render_audit_report.py`, `scripts/reproduce_audit.sh`, and everything under `audit/`.
Unchanged: `data/**`, `reports/**`, `documentation/**`, `scripts/build_datasets.py`, `scripts/nf_static_analyzer.py`, original nf-core sources. The v1 confidence column in `data/processed/process_edges.csv` is kept as the record of the original extraction; `confidence_v2` lives only in `audit/process_edges_v2.csv`.
Reproduce: `bash claude_analysis/scripts/reproduce_audit.sh`.

## Appendix A: the 53 core pairs

| id | pair | decision | flow type | supporting edges | reason (short) |
|---|---|---|---|---|---|
| P01 | BBMap (BBSplit) -> fq | Gold | analysis-data | E00138 | BBSplit primary FASTQ is the only content of ch_filtered_reads at the lint call. Needs skip_bbsplit=false and skip_linting=false. |
| P02 | BEDTools -> UCSC bedClip | Gold | analysis-data | E01011;E01015;E01019 | bedGraph from genomecov is the first input of bedClip, three instances (forward/reverse/combined). Needs skip_bigwig=false. |
| P03 | GNU tar -> Bracken | Silver | utility staging | E01046 | Real: the untarred Kraken2 database directory is the Bracken database input. GNU tar is a staging utility, so the pair is kept as Silver. Only when kraken_db is a .tar.gz |
| P04 | GNU tar -> HISAT2 | Silver | utility staging | E00444 | Real: untarred HISAT2 index is the index input of HISAT2_ALIGN. Only when --hisat2_index is a .tar.gz archive. Utility staging. |
| P05 | GNU tar -> Kraken 2 | Silver | utility staging | E01044 | Real: untarred database is the db input of KRAKEN2. Utility staging. |
| P06 | GNU tar -> Salmon | Silver | utility staging | E00294;E01086 | Real: the untarred Salmon index is the index slot of the Salmon quant input tuple; the index is consumed whole (modules/nf-core/salmon/quant/main.nf:12,49). Utility stagi |
| P07 | HISAT2 -> Kraken 2 | Gold | analysis-data | E01040 | Unaligned reads written by HISAT2 (--un-gz) are screened by Kraken2 under the default contaminant_screening_input=unmapped. The ternary selector (main.nf:716-722) is not  |
| P08 | HISAT2 -> SAMtools | Gold | analysis-data | E00447 | HISAT2 BAM is the sort input. Single-source channel. |
| P09 | Kraken 2 -> Bracken | Gold | analysis-data | E01045 | The Kraken2 report is the Bracken report input; branch requires contaminant_screening==kraken2_bracken (main.nf:737). Confirmed in the kraken2_bracken and hisat2_kraken2_ |
| P10 | NVIDIA Parabricks rna_fq2bam (STAR-based) -> SAMtools | Gold | analysis-data | E00379 | Parabricks rna_fq2bam is an alternative STAR implementation; its BAM goes through the same samtools sort stage. Needs use_parabricks_star (preview: parabricks_star). Alte |
| P11 | Picard -> BEDTools | Gold | analysis-data | E00963;E00979;E00995 | Picard-deduplicated BAM replaces ch_genome_bam and feeds genomecov. Needs skip_markduplicates=false, with_umi=false, no Parabricks mark-duplicates, skip_bigwig=false. |
| P12 | Picard -> StringTie | Gold | analysis-data | E00682 | Picard BAM (srbam slot) goes to StringTie; needs skip_stringtie=false and the same markduplicates conditions as P11. |
| P13 | RSEM -> Salmon | Gold | reference-resource | E00304;E00598 | RSEM prepare-reference is used only to extract the transcriptome FASTA, which Salmon uses as its -t reference in alignment (star_salmon) mode and which builds the Salmon  |
| P14 | RSEM -> kallisto | Gold | reference-resource | E00101 | SUSPICIOUS BUT TRUE: no RSEM quantification is involved. The nf-core module RSEM_PREPAREREFERENCE (rsem-prepare-reference) is used as a transcript extractor and its trans |
| P15 | RSEM -> nf-core custom script (Python) | Silver | partial-payload | E00569 | Real read of one RSEM isoforms file, but only to pick the GTF transcript-id attribute; target is a local Python script. Silver. |
| P16 | RSEM -> sed | Silver | utility-script | E00561;E00563 | RSEM results files are merged by a shell script. The canonical node "sed" exists only because the module declares sed in its version tuple; the tool is a coreutils shell  |
| P17 | RSEM -> tximeta | Gold | analysis-data | E00571 | RSEM isoform results are the tximport input (quant_type rsem). Collect/sort only; no foreign source in the channel. |
| P18 | SAMtools -> BBMap (BBSplit) | Negative | extractor-false-positive | E00041 | FALSE POSITIVE: the .fai is explicitly discarded (_fai) before BBSPLIT (indices:96) and the other index builders. The analyzer unions the tuple elements of ch_fasta_fai.  |
| P19 | SAMtools -> Picard | Gold | reference-resource | E00642 | The whole [meta,fasta,fai] tuple is the second Picard input; the fai slot is consumed (tuple not projected on this path). Contrast with P18. |
| P20 | SAMtools -> Qualimap | Gold | analysis-data | E00783 | Name-sorted BAM from samtools sort is the Qualimap input (single-source). Needs qualimap in qc tools. |
| P21 | SAMtools -> UCSC bedClip | Gold | reference-resource | E01012;E01016;E01020 | chrom.sizes written by samtools faidx is the sizes input of bedClip. |
| P22 | SAMtools -> UCSC bedGraphToBigWig | Gold | reference-resource | E01014;E01018;E01022 | chrom.sizes from samtools faidx is the sizes input of bedGraphToBigWig. |
| P23 | STAR -> Kraken 2 | Gold | analysis-data | E01043 | STAR unmapped reads are screened by Kraken2 under the default contaminant_screening_input=unmapped; the module emits them only because of align_star.config:93-96. |
| P24 | STAR -> NVIDIA Parabricks rna_fq2bam (STAR-based) | Gold | reference-resource | E00350 | Only the PARABRICKS_STARGENOMEGENERATE instance (STAR genomeGenerate with Parabricks-compatible STAR 2.7.2a) is valid: edge E00350, DAG-confirmed in parabricks_star. The  |
| P25 | STAR -> SAMtools | Gold | analysis-data | E00380 | Headline example. ch_star_out is an alias of STAR_ALIGN (align_star/main.nf:41-60). |
| P26 | STAR -> Sentieon STAR | Gold | reference-resource | E00325 | Sentieon STAR is an alternative STAR implementation that uses the regular STAR index. Edge E00325 is DAG-confirmed in sentieon_star; the Parabricks-built index edge (E003 |
| P27 | Salmon -> nf-core custom script (Python) | Silver | partial-payload | E00613;E01119 | Same as P15 for Salmon quant.sf: one file is read to choose the GTF attribute; local script. |
| P28 | Salmon -> tximeta | Gold | analysis-data | E00615;E01121 | All Salmon result directories are collected (sorted) and imported by tximeta/tximport. Headline example (Salmon downstream). |
| P29 | Sentieon STAR -> SAMtools | Gold | analysis-data | E00378 | Sentieon STAR BAM is sorted by samtools exactly like STAR. Alternative-implementation pair; needs use_sentieon_star (preview sentieon_star). |
| P30 | Trim Galore -> BBMap (BBSplit) | Gold | analysis-data | E00130 | Only the TRIMGALORE.reads edge counts: the join partner is key-only (lint reduced to meta, :298), so the payload reaching BBSplit is the trimmed reads. The TRIMGALORE.log |
| P31 | Trim Galore -> fq | Gold | analysis-data | E00122 | Trimmed reads are linted by fq. The TRIMGALORE.log edge is gating-only and not counted. |
| P32 | UCSC bedClip -> UCSC bedGraphToBigWig | Gold | analysis-data | E01013;E01017;E01021 | Direct, single-source. |
| P33 | ea-utils gtf2bed -> RSeQC | Gold | reference-resource | E00845;E00865;E00885;E00905;E00925 | Gene BED generated from the GTF by ea-utils gtf2bed is the annotation input of five RSeQC modules. |
| P34 | featureCounts (Subread) -> nf-core custom script (Python) | Silver | utility-script | E00762 | featureCounts biotype counts are reformatted by a local Python script for MultiQC (reporting-oriented target). |
| P35 | fq -> BBMap (BBSplit) | Negative | key-only-synchronisation | E00135 | The lint report is reduced to the sample key (_lint dropped). Downstream tools wait for fq lint but never read its output. Not a data exchange. |
| P36 | fq -> Salmon | Gold | analysis-data | E00292 | Sub-sampled FASTQ is the Salmon reads input (strandedness inference). |
| P37 | gzip (gunzip) -> nf-core custom script (Python) | Silver | utility staging | E00002;E00009 | Decompressed GTF/FASTA is the input of local scripts. Utility to local script. |
| P38 | kallisto -> nf-core custom script (Python) | Silver | partial-payload | E01120 | Same as P15 for kallisto abundance files. |
| P39 | kallisto -> tximeta | Gold | analysis-data | E01122 | kallisto results are imported by tximeta. |
| P40 | nf-core custom script (Python) -> HISAT2 | Silver | utility-script | E00072 | The GTF (or FASTA) produced by a local nf-core script (GTF filter / add-additional-fasta) is the annotation input of the named tool. Flow verified; the source node "nf-co |
| P41 | nf-core custom script (Python) -> Qualimap | Silver | utility-script | E00784 | The GTF (or FASTA) produced by a local nf-core script (GTF filter / add-additional-fasta) is the annotation input of the named tool. Flow verified; the source node "nf-co |
| P42 | nf-core custom script (Python) -> RSEM | Silver | utility-script | E00034;E00065;E00068 | The GTF (or FASTA) produced by a local nf-core script (GTF filter / add-additional-fasta) is the annotation input of the named tool. Flow verified; the source node "nf-co |
| P43 | nf-core custom script (Python) -> STAR | Silver | utility-script | E00043;E00046;E00051;E00054;E00374 | The GTF (or FASTA) produced by a local nf-core script (GTF filter / add-additional-fasta) is the annotation input of the named tool. Flow verified; the source node "nf-co |
| P44 | nf-core custom script (Python) -> Salmon | Silver | utility-script | E00296;E00297;E00590;E00591;E01088 | The GTF (or FASTA) produced by a local nf-core script (GTF filter / add-additional-fasta) is the annotation input of the named tool. Flow verified; the source node "nf-co |
| P45 | nf-core custom script (Python) -> Sentieon STAR | Silver | utility-script | E00326 | The GTF (or FASTA) produced by a local nf-core script (GTF filter / add-additional-fasta) is the annotation input of the named tool. Flow verified; the source node "nf-co |
| P46 | nf-core custom script (Python) -> StringTie | Silver | utility-script | E00699;E00700 | The GTF (or FASTA) produced by a local nf-core script (GTF filter / add-additional-fasta) is the annotation input of the named tool. Flow verified; the source node "nf-co |
| P48 | nf-core custom script (Python) -> dupRadar | Silver | utility-script | E00805 | The GTF (or FASTA) produced by a local nf-core script (GTF filter / add-additional-fasta) is the annotation input of the named tool. Flow verified; the source node "nf-co |
| P49 | nf-core custom script (Python) -> ea-utils gtf2bed | Silver | utility-script | E00014;E00015 | The GTF (or FASTA) produced by a local nf-core script (GTF filter / add-additional-fasta) is the annotation input of the named tool. Flow verified; the source node "nf-co |
| P50 | nf-core custom script (Python) -> kallisto | Silver | utility-script | E01112 | The GTF (or FASTA) produced by a local nf-core script (GTF filter / add-additional-fasta) is the annotation input of the named tool. Flow verified; the source node "nf-co |
| P47 | nf-core custom script (Python) -> SummarizedExperiment | Silver | utility-script | E00578;E00623;E01129 | The tx2gene table (rowdata) from the local script is consumed by SummarizedExperiment. |
| P51 | nf-core custom script (Python) -> tximeta | Silver | utility-script | E00572;E00617;E01123 | The tx2gene table from the local script is a required tximport input. |
| P52 | tximeta -> DESeq2 | Gold | analysis-data | E00583;E00628;E01134 | Length-scaled gene counts from tximeta are the DESeq2 QC input. |
| P53 | tximeta -> SummarizedExperiment | Gold | analysis-data | E00573;E00574;E00575;E00576;E00577;E00579;E00580;E00581;E005 | Every joined element is a tximeta output and the whole tail becomes matrix_files; the join partners are all siblings of the same producer, so the merge adds no foreign so |
