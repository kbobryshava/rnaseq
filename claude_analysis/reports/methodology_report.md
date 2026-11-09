# Methodology report: directed software relationships from nf-core/rnaseq 3.27.0

Pipeline commit `a1fcdddd3b826fe46eb46f0479f2ff8a7815af05` (tag 3.27.0). Nextflow 26.10.5 (preview only), Python 3.13.
Branch `claude/directed-software-analysis-3.27.0` on the fork `kbobryshava/rnaseq`. No original nf-core file was modified; nothing was executed except `nextflow -preview`.

**Labels:** **[V]** verified by running code / reading the cited file; **[H]** hypothesis, not proven.

## 1. Definition used
Software A -> B iff a channel carrying an output of a process using A is passed as an input argument of a process using B.
Implemented first at *process-instance* level (fully-qualified call path, e.g. `NFCORE_RNASEQ:RNASEQ:ALIGN_STAR:STAR_ALIGN`), then
collapsed to software. No transitive closure; no edge from source order, diagram position, shared membership or shared inputs.

## 2. Which source is reliable? (Part 4)
| source | verdict |
|---|---|
| Nextflow `-preview -with-dag` | **Partly reliable.** Process nodes and many edges are right, but see 3. Good for "which instances exist in a configuration". |
| Static analysis of `main.nf`/subworkflow code (this work) | **Primary source.** Gives edge, emit, input index, conditions, file:line. |
| nf-core `modules/*/main.nf` | Authoritative for process inputs/outputs, emit names and `topic: versions` (version tuples must not count as data). |
| `meta.yml` / `environment.yml` | Needed for software identity, but `meta.yml` `tools:` is wrong for some modules **[V]**: RSEM modules list `rseqc`, local scripts list `custom`. |
| `modules.json` | Pins versions of 75 installed modules; all 75 are instantiated at least once **[V]**, but instantiation != execution (conditions). |
| Metro map `assets/metro_map.mmd` | **Not a dependency source.** 24 of 46 mappable connections correspond to a data edge; sequential QC chains (`rseqc --> preseq --> qualimap --> dupradar --> featurecounts`, lines 211-215) are layout order **[V]** (`data/processed/metro_vs_static.csv`). Mapping from stations to processes is partial, so 22 is an upper bound on layout-only links. |
| nf-test snapshots / traces | Snapshots list executed process names for a test; no `-with-trace` exists in preview (no tasks run). Not used as edge evidence. **[H]** a real stub run would give task-level evidence; it was not run. |

## 3. DAG structure and cycles (Part 4)
* Nodes: `([NAME])` process, `(( ))` anonymous operator, `["label"]` channel/value source; subgraph titles are fully-qualified scopes **[V]** (`scripts/parse_dag.py`). Edges carry no labels.
* The default test DAG (67 processes, 544 nodes, 555 edges) has **2 strongly connected components: 47 nodes (33 process nodes) and 2 nodes** **[V]** (`data/graphs/test_dag_raw.json`).
* Removing the single anonymous operator `v132` (scope `NFCORE_RNASEQ:RNASEQ`) shrinks the large component to 3 nodes **[V]**. It has 10 in-edges and 9 out-edges and is fed by `channel.fromList` (samplesheet, `workflows/rnaseq/main.nf:155`) and by several processes.
* The static process graph has **0 strongly connected components** **[V]**. So the cycles are a representation artifact, not pipeline cycles.
* Residual small cycles (e.g. `SAMTOOLS_FAIDX <-> v27`, `CAT_FASTQ/FQ_LINT <-> v197`, `FQ_SUBSAMPLE/SALMON_QUANT <-> v262`) all sit at places where a channel variable is combined with a process output and re-used: `ch_fasta.combine(SAMTOOLS_FAIDX.out.fai)` (`subworkflows/local/prepare_genome_references/main.nf:191-196`), `CAT_FASTQ(...).reads.mix(ch_fastq.single).set { ch_filtered_reads }` and `ch_filtered_reads = ch_filtered_reads.join(FQ_LINT.out.lint...)` (`subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf:178-191`) **[V]** as source locations. **[H]** the DAG builder draws the output of a multi-input operator into the node of its first operand, which fuses the nodes.
* Consequence **[V]**: in each of 10 configurations 56-87 % of DAG process-to-process paths cross a multi-in/multi-out ("hub") node, and e.g. `CUSTOM_CATADDITIONALFASTA -> PRESEQ_LCEXTRAP` appears as DAG-derived edge although only the fasta channel is shared. Paths that avoid hubs are never contradicted by the static graph: `dag_only_hubfree = 0` in all 10 DAGs (`data/processed/dag_vs_static.json`), 85 / 85 in the default test.
* Workflow interfaces (take/emit) do not create cycles by themselves; they are resolved by binding positional arguments to `take` names and emits to channels, which the DAG shows only as anonymous operators.
* Conditional/alternative processes: the DAG contains only the instances of one configuration (e.g. 67 of 178 for the test profile); alternatives such as `SENTIEON_STAR_ALIGN`/`PARABRICKS_RNA_FQ2BAM` appear only in their own preview. Static analysis keeps all alternatives with the branch conditions (`required_param_assumptions`).

## 4. Static analysis method (`scripts/nf_static_analyzer.py`)
1. Parse includes (with `as` aliases), process declarations (inputs, outputs, emit names, `topic: versions`) and workflow `take/main/emit`.
2. Execute the entry workflow symbolically: each channel variable holds provenance = set of (producer instance, emit) with the trail of assignments/operators (file:line).
3. Operators are conservative unions (`mix/join/combine/map/...`); `ch_x = PROC` aliases (e.g. `ch_star_out = STAR_ALIGN` in `subworkflows/local/align_star/main.nf:41-60`) are tracked; closure parameters shadow variables.
4. A process call creates one edge per (provenance port, input index). Subworkflows are inlined with their call path.
5. `if/else` branches are both explored, merged values are tagged with the branch condition; edges whose condition atoms contradict each other (e.g. `trimmer == 'trimgalore'` and `trimmer == 'fastp'`) are dropped (25 emit-edges, listed in `static_graph.json`).
6. Edge classes (see data dictionary): direct, merged-channel, key-only-synchronization (`.map { meta, _x -> meta }`), metadata-dependency, gating-or-metadata, reporting-aggregation.

Result **[V]**: 178 process instances, 47 workflow instances, 1,234 emit-level edges, 1,125 process pairs, 0 process-level cycles.
Evidence tiers: A (also in a hub-free preview DAG) 174 edges, B (static only, direct/merged/reporting) 839, C (review) 221.

## 5. Software level
`process_software_map.csv` maps every instance to curated canonical software (role-annotated). Alternatives are distinct nodes with `alternative_of`
(Sentieon STAR, Parabricks rna_fq2bam -> STAR; Sentieon RSEM -> RSEM). Helper tools bundled in environments (samtools inside STAR/Bowtie2/HISAT2 modules, gawk) are recorded as secondary and
do **not** create edges; processes with several primary tools would produce edges for each (flag `multi_tool_process`; none in the curated table).
Result: 46 software nodes, 391 directed software pairs (15 are self-loops, 31 are reporting-only). `software_edges_core_tierA.csv` has 53 non-self, non-reporting pairs confirmed by hub-free DAGs.
**The software graph contains one 24-tool strongly connected component** **[V]**: software identity is reused at different stages (e.g. SAMtools consumes STAR output and produces the FASTA index consumed by STAR), so collapsing creates cycles that do not exist at process level. Keep the process-level dataset as ground truth.

## 6. Requested examples (details with file:line in `validation_examples.md`)
1. **STAR -> SAMtools [V]:** `STAR_ALIGN.bam -> BAM_SORT_STATS_SAMTOOLS:SAMTOOLS_SORT` (class direct, tier A; assumes `use_sentieon_star` and `use_parabricks_star` false; call `subworkflows/nf-core/bam_sort_stats_samtools/main.nf:15`, producer `subworkflows/local/align_star/main.nf:56`). The edge to `SAMTOOLS_SORT` in the UMI sub-workflow (`bam_transcript`) is conditional on `with_umi`. `STAR_ALIGN.log_final -> SAMTOOLS_SORT_QUALIMAP` is a gating (percent-mapped filter) dependency, class C.
2. **FastQC / Trim Galore [V]:** raw FastQC and Trim Galore both read the same channel (`CAT_FASTQ.reads` merged with `FQ_LINT` key); no FastQC -> TrimGalore edge (negative control: 0 edges). `TRIMGALORE.reads -> FASTQC` (post-trim QC) exists. The alternative fastp subworkflow is correctly separated by condition pruning.
3. **Salmon [V]:** `SALMON_QUANT.results -> CUSTOM_TX2GENE`, `TXIMETA_TXIMPORT` (direct, tier A). `SALMON_QUANT.lib_format_counts` (subsample run) feeds aligners only as inferred strandedness inside `meta`: class metadata-dependency, not a data-file dependency.
4. **Kraken2 -> Bracken [V]:** `KRAKEN2.report -> BRACKEN` direct/high with `contaminant_screening == 'kraken2_bracken'` (`workflows/rnaseq/main.nf:728-738`), plus `UNTAR_KRAKEN_DB -> BRACKEN` (database). Observed in the `kraken2_bracken` DAG.
5. **Parallel processes [V]:** no edges are created between siblings that share an input; sibling pairs that are also directly connected are listed for review.
6. **Alternatives [V]:** STAR_ALIGN, SENTIEON_STAR_ALIGN and PARABRICKS_RNA_FQ2BAM instances exist side by side with identical downstream consumers and mutually exclusive conditions; `sentieon_star` and `parabricks_star` DAGs contain the respective instance. Not assumed executed unless present in a preview DAG (`executed_matrix.csv`).

## 7. Alternative configurations (Part 7)
Ten preview DAGs: test (STAR+Salmon), hisat2, salmon_pseudo, kallisto, star_rsem, kraken2, kraken2_bracken, hisat2_kraken2_bracken, sentieon_star, parabricks_star (`data/raw/*_dag.html`, params in `data/raw/params`). No data downloaded beyond the small samplesheet/test references the preview fetches. Command-line `--flag true` was rejected by nf-schema (string, not boolean) - JSON params files are used **[V]**.

## 8. Limitations and open questions
* **Payload ambiguity [V]:** 551 merged-channel edges mean the channel mixes several sources; the analysis cannot tell which tuple element the consumer reads. Treat tier B as probable, tier C as non-control.
* Tier A means "consistent with a hub-free preview DAG", not manually verified. Several surprising core pairs (e.g. RSEM -> kallisto via transcript FASTA) need manual review.
* `for/while/switch/try` and closures calling processes are not modelled (0 such statements were reported in this pipeline: `unresolved` is empty), so 3.27.0 is fully covered syntactically, but correctness of operator semantics beyond union is **[H]**.
* Condition atoms are matched by variable name across scopes **[H]**; 25 dropped edges are logged for audit.
* Local custom processes and utility software (gzip, cat, tar, sed, gawk, Python scripts) are retained and flagged by role, not removed.
* Not run: a stub run (`-stub`) that would add trace-level execution evidence.
