"""Family-level adjudication of the software pairs that are not among the 53 individually adjudicated core pairs.

A *family* is a part of the workflow whose channel structure was read once in the source and is the same for every member:
  reads      - ch_filtered_reads is reassigned stage by stage (subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf:178-358); every stage has its
               own skip/enable flag, so any earlier-stage tool can hand its reads directly to any later consumer. Final channel: emit `reads` (:438).
  unaligned  - unaligned reads of an aligner go to contaminant screening (workflows/rnaseq/main.nf:291,369,716-725,749; conf/modules/align_star.config:93-96).
  bam        - the genome/transcriptome BAM channels are reassigned aligner -> samtools sort -> [UMI dedup | Picard] (workflows/rnaseq/main.nf:274-410,521-525)
               and consumed by StringTie :551, RustQC :571, genomecov :670, BAM_QC_RNASEQ :623, BAM_RSEQC, QUANTIFY_* :424-460.
  reference  - references/indices are produced once and passed to every tool that needs them (prepare_genome_references/main.nf:55-241,
               prepare_genome_indices/main.nf:60-292).
A pair is promoted only if the extractor has a live (not rejected) edge of that family; for reads, the producer stage must precede the consumer stage.
Decision: Gold when both endpoints are named tools, Silver when an end is a generic utility / local script (tar, gzip, cat, sed, gawk, custom scripts).
`verification_level` records that these were verified per family, not pair by pair.
"""
import re

WEAK_NAMES = {'GNU tar', 'gzip (gunzip)', 'cat (GNU coreutils)', 'sed', 'gawk', 'nf-core custom script (Python)'}
READ_EMITS = {'reads', 'primary_fastq', 'fastq'}
PROD_STAGE = {'CAT_FASTQ': 0, 'UMITOOLS_EXTRACT': 1, 'TRIMGALORE': 2, 'FASTP': 2, 'BBMAP_BBSPLIT': 3, 'SORTMERNA': 4, 'RIBODETECTOR': 4, 'BOWTIE2_ALIGN': 4, 'SAMTOOLS_FASTQ': 4}
ALIGNER_UNALIGNED = {'STAR_ALIGN', 'SENTIEON_STARALIGN', 'PARABRICKS_RNAFQ2BAM', 'HISAT2_ALIGN', 'BOWTIE2_ALIGN'}
DST_STAGE = {'FASTQC': 1, 'FQ_LINT': 1, 'UMITOOLS_EXTRACT': 1, 'TRIMGALORE': 2, 'FASTP': 2, 'FASTQC_TRIM': 3, 'FQ_LINT_AFTER_TRIMMING': 3, 'BBMAP_BBSPLIT': 3,
             'FQ_LINT_AFTER_BBSPLIT': 4, 'SORTMERNA': 4, 'RIBODETECTOR': 4, 'SEQKIT_STATS': 5, 'FQ_LINT_AFTER_RIBO_REMOVAL': 5, 'FASTQC_FILTERED': 5,
             'STAR_ALIGN': 6, 'SENTIEON_STAR_ALIGN': 6, 'PARABRICKS_RNA_FQ2BAM': 6, 'HISAT2_ALIGN': 6, 'SALMON_QUANT': 6, 'KALLISTO_QUANT': 6, 'FQ_SUBSAMPLE': 6,
             'KRAKEN2': 9, 'SYLPH_PROFILE': 9}
BAM_EMITS = {'bam', 'bam_transcript', 'cram', 'index'}
BAM_PROD = {'SAMTOOLS_SORT', 'SAMTOOLS_INDEX', 'SAMTOOLS_VIEW', 'UMITOOLS_DEDUP', 'UMICOLLAPSE', 'PICARD_MARKDUPLICATES', 'UMITOOLS_PREPAREFORRSEM', 'STAR_ALIGN',
            'SENTIEON_STARALIGN', 'PARABRICKS_RNAFQ2BAM', 'HISAT2_ALIGN', 'BOWTIE2_ALIGN'}
BAM_CONS = {'SAMTOOLS_SORT', 'SAMTOOLS_INDEX', 'SAMTOOLS_STATS', 'SAMTOOLS_FLAGSTAT', 'SAMTOOLS_IDXSTATS', 'SAMTOOLS_VIEW', 'UMITOOLS_DEDUP', 'UMICOLLAPSE', 'UMITOOLS_PREPAREFORRSEM',
            'PICARD_MARKDUPLICATES', 'STRINGTIE_STRINGTIE', 'BEDTOOLS_GENOMECOV', 'PRESEQ_LCEXTRAP', 'SUBREAD_FEATURECOUNTS', 'QUALIMAP_RNASEQ', 'DUPRADAR', 'RUSTQC',
            'RSEM_CALCULATEEXPRESSION', 'SENTIEON_RSEMCALCULATEEXPRESSION', 'SALMON_QUANT'} | {f'RSEQC_{x}' for x in ('BAMSTAT', 'INNERDISTANCE', 'INFEREXPERIMENT', 'JUNCTIONANNOTATION', 'JUNCTIONSATURATION', 'READDISTRIBUTION', 'READDUPLICATION', 'TIN')}
REF_PROD = {'GFFREAD', 'GUNZIP', 'CUSTOM_GTFFILTER', 'CUSTOM_CATADDITIONALFASTA', 'RSEM_PREPAREREFERENCE', 'SENTIEON_RSEMPREPAREREFERENCE', 'SAMTOOLS_FAIDX', 'UNTAR', 'SEQKIT_REPLACE',
            'PREPROCESS_TRANSCRIPTS_FASTA_GENCODE', 'STAR_GENOMEPARAMS_UPGRADE', 'STAR_GENOMEGENERATE', 'HISAT2_BUILD', 'HISAT2_EXTRACTSPLICESITES', 'BOWTIE2_BUILD', 'SALMON_INDEX', 'KALLISTO_INDEX', 'EAUTILS_GTF2BED'}
REJECT = {'PROJECTION-DROPPED', 'MULTIMAP-SPLIT', 'INFEASIBLE-CALLSITE-CONSTANT'}

EVIDENCE = {
    'reads': 'subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf:178 CAT_FASTQ, :187 FQ_LINT, :200/:235 trimmers, :307 BBMAP_BBSPLIT, :333 FASTQ_REMOVE_RRNA, :438 emit reads; each stage is guarded by its own skip/enable flag',
    'unaligned': 'workflows/rnaseq/main.nf:291 and :369 (ch_unaligned_sequences), :716-722 selector, :725 KRAKEN2, :749 SYLPH_PROFILE; conf/modules/align_star.config:93-96',
    'bam': 'workflows/rnaseq/main.nf:274 ALIGN_STAR, :359 FASTQ_ALIGN_HISAT2, :397-409 BAM_DEDUP_UMI, :521-525 Picard, :551 StringTie, :571 RustQC, :623 BAM_QC_RNASEQ, :670 genomecov, :424-460 QUANTIFY_*',
    'reference': 'subworkflows/local/prepare_genome_references/main.nf:55-241 and subworkflows/local/prepare_genome_indices/main.nf:60-292 (resources produced once, passed to every consumer)',
    'rsem_downstream': 'subworkflows/nf-core/quantify_rsem/main.nf:58 CUSTOM_RSEMMERGECOUNTS(counts_gene, counts_transcript), :79-87 QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT(..., ch_counts_transcript, ..., rsem) -> CUSTOM_TX2GENE + TXIMETA_TXIMPORT; the Sentieon and the plain RSEM process are alternatives inside the same if/else (:29-35)',
    'sylph': 'workflows/rnaseq/main.nf:749-757 SYLPH_PROFILE(...).profile_out.filter{...} -> SYLPHTAX_TAXPROF',
}
WHY = {
    'reads': 'Reads handed from one pre-processing stage to a later consumer. Intermediate stages are optional, so the tools can be used back to back.',
    'unaligned': 'Unaligned reads of the aligner are screened for contamination (contaminant_screening_input = unmapped, the default selector).',
    'bam': 'BAM (or BAM index / transcriptome BAM) produced by one tool is consumed by the next tool of the alignment-processing, QC or quantification chain.',
    'reference': 'Reference resource (annotation, transcripts, FASTA, index, chrom.sizes) produced by one step is the input resource of another tool.',
    'rsem_downstream': 'RSEM results are merged / imported downstream (same code path as the plain-RSEM pairs P15-P17).',
    'sylph': 'Sylph profile is the input of sylph-tax.',
}


def stage_of_dst(leaf, inst):
    if leaf.startswith('BOWTIE2_ALIGN'): return 4 if 'FASTQ_REMOVE_RRNA' in inst else 6
    return DST_STAGE.get(leaf)


def classify(e):
    """return family name or None for one process edge (dict from process_edges.csv)"""
    if e['confidence_v2'] == 'rejected' or e['payload_check'] in REJECT or e['edge_class'] not in ('direct', 'merged-channel'): return None
    sm, dm, emit = e['src_module'], e['dst_module'], e['src_emit']
    sleaf, dleaf = e['src_instance'].split(':')[-1], e['dst_instance'].split(':')[-1]
    if sm == 'SYLPH_PROFILE' and dm == 'SYLPHTAX_TAXPROF': return 'sylph'
    if sm in ('SENTIEON_RSEMCALCULATEEXPRESSION', 'RSEM_CALCULATEEXPRESSION') and dm in ('CUSTOM_TX2GENE', 'CUSTOM_RSEMMERGECOUNTS', 'TXIMETA_TXIMPORT'): return 'rsem_downstream'
    if emit in READ_EMITS and sm in PROD_STAGE | {k: 0 for k in ALIGNER_UNALIGNED}:
        in_rrna = 'FASTQ_REMOVE_RRNA' in e['src_instance']
        if sm in ALIGNER_UNALIGNED and not (sm in ('BOWTIE2_ALIGN',) and in_rrna):
            return 'unaligned' if dm in ('KRAKEN2_KRAKEN2', 'SYLPH_PROFILE') and e['dst_input_index'] == '0' else None
        if sm == 'BOWTIE2_ALIGN' and not in_rrna: return None
        if sm in ('BOWTIE2_ALIGN', 'SAMTOOLS_FASTQ') and not in_rrna and 'ALIGN_BOWTIE2' not in e['src_instance']: return None
        if e['dst_input_index'] != '0': return None
        if dm in ('KRAKEN2_KRAKEN2', 'SYLPH_PROFILE'): return 'reads'      # ordering: any reads stage precedes contaminant screening
        d = stage_of_dst(dleaf, e['dst_instance'])
        p = PROD_STAGE.get(sm)
        if d is None or p is None or not (p < d): return None
        return 'reads'
    if emit in BAM_EMITS and sm in BAM_PROD and dm in BAM_CONS and e['payload_check'] == 'compatible': return 'bam'
    if sm in REF_PROD and emit not in READ_EMITS and not (sm in BAM_PROD and emit in BAM_EMITS): return 'reference'
    return None


def adjudicate(edges, already):
    """edges: process_edges rows; already: set of (src_software, dst_software) names decided elsewhere.  Returns {pair: record}."""
    by = {}
    for e in edges:
        key = (e['src_software'], e['dst_software'])
        if key[0] == key[1] or key in already: continue
        fam = classify(e)
        if fam: by.setdefault(key, {}).setdefault(fam, []).append(e['edge_id'])
    out = {}
    for key, fams in by.items():
        fam = sorted(fams, key=lambda f: -len(fams[f]))[0]
        ids = sorted({i for v in fams.values() for i in v})
        weak = key[0] in WEAK_NAMES or key[1] in WEAK_NAMES
        out[key] = {'decision': 'Silver' if weak else 'Gold', 'family': fam if len(fams) == 1 else '+'.join(sorted(fams)), 'edge_ids': ids,
                    'flow_type': {'reads': 'analysis-data', 'unaligned': 'analysis-data', 'bam': 'analysis-data', 'sylph': 'analysis-data', 'rsem_downstream': 'analysis-data', 'reference': 'reference-resource'}[fam] if not weak else 'utility-script',
                    'evidence': '; '.join(EVIDENCE[f] for f in sorted(fams)), 'explanation': ' '.join(WHY[f] for f in sorted(fams))}
    return out
