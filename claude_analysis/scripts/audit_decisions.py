"""Hand-made adjudication of the 53 core software pairs (audit of nf-core/rnaseq 3.27.0, commit a1fcdddd).

Every entry was decided after reading the cited Nextflow source in this checkout. File:line references in `evidence` are the
lines that were read to take the decision; the process-level edge ids, declarations and call lines are added automatically by
curate_audit.py from data/processed (nothing in data/processed is modified).

Decision rules (applied identically to all pairs):
  Gold       - the producer's *output* is passed, unchanged in payload, to the consumer's *input slot* (read in the source), both ends are
               named bioinformatics tools (not a generic OS utility / local script), and the path is feasible under a stated parameter set.
  Silver     - the data flow is real and verified, but one end is a generic utility/local script (tar, gzip, sed, nf-core custom Python
               scripts - several distinct scripts are merged into one software node) or only part of the payload is used.
  Negative   - the extracted relationship is NOT a data exchange (tuple element dropped, key-only synchronisation, infeasible branch).
  Unresolved - cannot be decided from source without execution.
Fields: pid, decision, flow_type, edge_filter (python predicate name or None = all tier-A edges of the pair), confidence, evidence, explanation
"""

TAR = 'utility staging'
D = []


def add(pid, decision, flow, conf, filt, evidence, why):
    D.append(dict(pid=pid, decision=decision, flow_type=flow, decision_confidence=conf, edge_filter=filt, evidence=evidence, explanation=why))


add('P01', 'Gold', 'analysis-data', 'high', None,
    'subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf:315 (BBMAP_BBSPLIT.out.primary_fastq.set{ch_filtered_reads}); :321 FQ_LINT_AFTER_BBSPLIT(ch_filtered_reads)',
    'BBSplit primary FASTQ is the only content of ch_filtered_reads at the lint call. Needs skip_bbsplit=false and skip_linting=false.')
add('P02', 'Gold', 'analysis-data', 'high', None,
    'workflows/rnaseq/main.nf:674-686 (BEDTOOLS_GENOMECOV_FW/REV/COMBINED), :696-708 pass .out.genomecov; subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:18 UCSC_BEDCLIP(bedgraph, sizes)',
    'bedGraph from genomecov is the first input of bedClip, three instances (forward/reverse/combined). Needs skip_bigwig=false.')
add('P03', 'Silver', TAR, 'high', None,
    'subworkflows/local/prepare_genome_references/main.nf:226-228 (UNTAR_KRAKEN_DB.untar.map{tuple[1]}); workflows/rnaseq/main.nf:738-741 BRACKEN(ch_kraken_reports, ch_kraken_db)',
    'Real: the untarred Kraken2 database directory is the Bracken database input. GNU tar is a staging utility, so the pair is kept as Silver. Only when kraken_db is a .tar.gz.')
add('P04', 'Silver', TAR, 'high', None,
    'subworkflows/local/prepare_genome_indices/main.nf:215 (UNTAR_HISAT2_INDEX); subworkflows/nf-core/fastq_align_hisat2/main.nf:16 HISAT2_ALIGN(reads, index, ...)',
    'Real: untarred HISAT2 index is the index input of HISAT2_ALIGN. Only when --hisat2_index is a .tar.gz archive. Utility staging.')
add('P05', 'Silver', TAR, 'high', None,
    'subworkflows/local/prepare_genome_references/main.nf:228; workflows/rnaseq/main.nf:725-730 KRAKEN2(ch_contaminant_sequences, ch_kraken_db, ...)',
    'Real: untarred database is the db input of KRAKEN2. Utility staging.')
add('P06', 'Silver', TAR, 'high', None,
    'subworkflows/local/prepare_genome_indices/main.nf:259 (UNTAR_SALMON_INDEX.untar.first()); subworkflows/nf-core/fastq_subsample_fq_salmon/main.nf:48; subworkflows/nf-core/quantify_pseudo_alignment/main.nf:31 index.combine(gtf).combine(transcript_fasta)',
    'Real: the untarred Salmon index is the index slot of the Salmon quant input tuple; the index is consumed whole (modules/nf-core/salmon/quant/main.nf:12,49). Utility staging.')
add('P07', 'Gold', 'analysis-data', 'high', None,
    'workflows/rnaseq/main.nf:369 (ch_unaligned_sequences = FASTQ_ALIGN_HISAT2.out.fastq); :364 save_unaligned arg; :716-722 selection; :725 KRAKEN2(ch_contaminant_sequences,...); nextflow.config:114 contaminant_screening_input = unmapped',
    'Unaligned reads written by HISAT2 (--un-gz) are screened by Kraken2 under the default contaminant_screening_input=unmapped. The ternary selector (workflows/rnaseq/main.nf:716-722) is not part of the extractor\'s condition atoms, so this requirement is documented here.')
add('P08', 'Gold', 'analysis-data', 'high', None,
    'subworkflows/nf-core/fastq_align_hisat2/main.nf:21 BAM_SORT_STATS_SAMTOOLS(HISAT2_ALIGN.out.bam, ch_fasta_fai); subworkflows/nf-core/bam_sort_stats_samtools/main.nf:15 SAMTOOLS_SORT(ch_bam, ch_fasta_fai, \'\')',
    'HISAT2 BAM is the sort input. Single-source channel.')
add('P09', 'Gold', 'analysis-data', 'high', None,
    'workflows/rnaseq/main.nf:731 (ch_kraken_reports = KRAKEN2.out.report); :737-741 BRACKEN(ch_kraken_reports, ch_kraken_db); modules/nf-core/kraken2/kraken2/main.nf output path(\'*report.txt\') emit: report; bracken input path(kraken_report)',
    'The Kraken2 report is the Bracken report input; branch requires contaminant_screening==kraken2_bracken (workflows/rnaseq/main.nf:737). Confirmed in the kraken2_bracken and hisat2_kraken2_bracken previews.')
add('P10', 'Gold', 'analysis-data', 'high', lambda e: e['evidence_tier'].startswith('A'),
    'subworkflows/local/align_star/main.nf:51 PARABRICKS_RNA_FQ2BAM(...) at :51; :61 ch_orig_bam = ch_star_out.out.bam; :74 BAM_SORT_STATS_SAMTOOLS(ch_orig_bam, fasta_fai); subworkflows/nf-core/bam_sort_stats_samtools/main.nf:15',
    'Parabricks rna_fq2bam is an alternative STAR implementation; its BAM goes through the same samtools sort stage. Needs use_parabricks_star (preview: parabricks_star). Alternative-implementation pair.')
add('P11', 'Gold', 'analysis-data', 'high', None,
    'workflows/rnaseq/main.nf:521-525 (BAM_MARKDUPLICATES_PICARD at :521, ch_genome_bam = ...out.bam at :525); :670 ch_genomecov_input = ch_genome_bam.map{meta,bam -> [meta,bam,1]}; :674 BEDTOOLS_GENOMECOV_FW',
    'Picard-deduplicated BAM replaces ch_genome_bam and feeds genomecov. Needs skip_markduplicates=false, with_umi=false, no Parabricks mark-duplicates, skip_bigwig=false.')
add('P12', 'Gold', 'analysis-data', 'high', None,
    'workflows/rnaseq/main.nf:521-525; :551-555 STRINGTIE_STRINGTIE(ch_genome_bam.map{meta,bam -> [meta,bam,[]]}, ...)',
    'Picard BAM (srbam slot) goes to StringTie; needs skip_stringtie=false and the same markduplicates conditions as P11.')
add('P13', 'Gold', 'reference-resource', 'high', None,
    'subworkflows/local/prepare_genome_references/main.nf:20 (RSEM_PREPAREREFERENCE as MAKE_TRANSCRIPTS_FASTA), :180 MAKE_TRANSCRIPTS_FASTA(ch_fasta,ch_gtf).transcript_fasta; modules/nf-core/rsem/preparereference/main.nf:16,46; workflows/rnaseq/main.nf:454-463 QUANTIFY_BAM_SALMON(...ch_transcript_fasta...); modules/nf-core/salmon/quant/main.nf:28-39 (alignment mode uses -t transcript_fasta); subworkflows/nf-core/fastq_subsample_fq_salmon/main.nf:48',
    'RSEM prepare-reference is used only to extract the transcriptome FASTA, which Salmon uses as its -t reference in alignment (star_salmon) mode and which builds the Salmon index. Direct edge E00598 (QUANTIFY_BAM_SALMON) is hub-free DAG-confirmed. Only when no --transcript_fasta, no --gffread_transcript_fasta and no Sentieon STAR.')
add('P14', 'Gold', 'reference-resource', 'high', None,
    'subworkflows/local/prepare_genome_references/main.nf:180 (MAKE_TRANSCRIPTS_FASTA = RSEM_PREPAREREFERENCE); modules/nf-core/rsem/preparereference/main.nf:16,46 (cp rsem/genome.transcripts.fa .); subworkflows/local/prepare_genome_indices/main.nf:292 KALLISTO_INDEX(ch_transcript_fasta.map{item -> [[:], item]})',
    'SUSPICIOUS BUT TRUE: no RSEM quantification is involved. The nf-core module RSEM_PREPAREREFERENCE (rsem-prepare-reference) is used as a transcript extractor and its transcripts.fa is the only input of KALLISTO_INDEX. Direct, single-source, hub-free DAG-confirmed (kallisto preview). Absent when --transcript_fasta, --gffread_transcript_fasta, --use_sentieon_star or --kallisto_index is set.')
add('P15', 'Silver', 'partial-payload', 'medium', None,
    'subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:25-48 (quant_results.toSortedList...first -> CUSTOM_TX2GENE input 2); modules/nf-core/custom/tx2gene/templates/tx2gene.py:39-57,152-160 (reads the top 100 transcripts of ONE isoforms.results)',
    'Real read of one RSEM isoforms file, but only to pick the GTF transcript-id attribute; target is a local Python script. Silver.')
add('P16', 'Silver', 'utility-script', 'medium', None,
    'subworkflows/nf-core/quantify_rsem/main.nf:58-70 CUSTOM_RSEMMERGECOUNTS(genes, isoforms); modules/nf-core/custom/rsemmergecounts/main.nf (script uses mkdir/cut/paste/sed on RSEM *.results)',
    'RSEM results files are merged by a shell script. The canonical node "sed" exists only because the module declares sed in its version tuple; the tool is a coreutils shell script.')
add('P17', 'Gold', 'analysis-data', 'high', None,
    'subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:56-72 (quant_results.toSortedList -> sorted.collect{it[1]} -> TXIMETA_TXIMPORT input 0); called from subworkflows/nf-core/quantify_rsem/main.nf:79-87 with ch_counts_transcript and quant_type rsem',
    'RSEM isoform results are the tximport input (quant_type rsem). Collect/sort only; no foreign source in the channel.')
add('P18', 'Negative', 'extractor-false-positive', 'high', None,
    'subworkflows/local/prepare_genome_indices/main.nf:60 ch_fasta = ch_fasta_fai.map { _meta, fasta_file, _fai -> fasta_file }; prepare_genome_references/main.nf:193-196',
    'FALSE POSITIVE: the .fai is explicitly discarded (_fai) before BBSPLIT (indices:96) and the other index builders. The analyzer unions the tuple elements of ch_fasta_fai. BBSplit receives only the FASTA.')
add('P19', 'Gold', 'reference-resource', 'high', None,
    'subworkflows/local/prepare_genome_references/main.nf:191-196 ch_fasta_fai = ch_fasta.combine(FAIDX.out.fai...) -> emit fasta_fai :235; subworkflows/nf-core/bam_markduplicates_picard/main.nf:15 PICARD_MARKDUPLICATES(ch_reads, ch_fasta_fai); input tuple(meta2, path(fasta), path(fai))',
    'The whole [meta,fasta,fai] tuple is the second Picard input; the fai slot is consumed (tuple not projected on this path). Contrast with P18.')
add('P20', 'Gold', 'analysis-data', 'high', None,
    'subworkflows/nf-core/bam_qc_rnaseq/main.nf:54-62 SAMTOOLS_SORT_QUALIMAP(...); QUALIMAP_RNASEQ(SAMTOOLS_SORT_QUALIMAP.out.bam, ch_gtf)',
    'Name-sorted BAM from samtools sort is the Qualimap input (single-source). Needs qualimap in qc tools.')
add('P21', 'Gold', 'reference-resource', 'high', None,
    'subworkflows/local/prepare_genome_references/main.nf:191-192 SAMTOOLS_FAIDX(...,true); ch_chrom_sizes = ...out.sizes.map{tuple[1]}; subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:18 UCSC_BEDCLIP(bedgraph, sizes)',
    'chrom.sizes written by samtools faidx is the sizes input of bedClip.')
add('P22', 'Gold', 'reference-resource', 'high', None,
    'subworkflows/local/prepare_genome_references/main.nf:192; subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:23 UCSC_BEDGRAPHTOBIGWIG(UCSC_BEDCLIP.out.bedgraph, sizes)',
    'chrom.sizes from samtools faidx is the sizes input of bedGraphToBigWig.')
add('P23', 'Gold', 'analysis-data', 'high', None,
    'workflows/rnaseq/main.nf:291 ch_unaligned_sequences = ALIGN_STAR.out.fastq; :716-722; :725; conf/modules/align_star.config:93-96 (--outReadsUnmapped Fastx when contaminant_screening_input==unmapped)',
    'STAR unmapped reads are screened by Kraken2 under the default contaminant_screening_input=unmapped; the module emits them only because of align_star.config:93-96.')
add('P24', 'Gold', 'reference-resource', 'high', lambda e: e['src_instance'].endswith('PARABRICKS_STARGENOMEGENERATE'),
    'subworkflows/local/prepare_genome_indices/main.nf:19 (STAR_GENOMEGENERATE as PARABRICKS_STARGENOMEGENERATE), :149-154; conf/modules/prepare_genome.config:42-46 (star=2.7.2a container); subworkflows/local/align_star/main.nf PARABRICKS_RNA_FQ2BAM(reads, fasta, index,...)',
    'Only the PARABRICKS_STARGENOMEGENERATE instance (STAR genomeGenerate with Parabricks-compatible STAR 2.7.2a) is valid: edge E00350, DAG-confirmed in parabricks_star. The edge from plain STAR_GENOMEGENERATE (E00353) is infeasible: that process runs only when use_parabricks_star is false (indices:149 if-branch precedes :168 else-if), the consumer only when it is true.')
add('P25', 'Gold', 'analysis-data', 'high', None,
    'subworkflows/local/align_star/main.nf:61 ch_orig_bam = ch_star_out.out.bam; :74 BAM_SORT_STATS_SAMTOOLS(ch_orig_bam, fasta_fai); subworkflows/nf-core/bam_sort_stats_samtools/main.nf:15',
    'Headline example. ch_star_out is an alias of STAR_ALIGN (align_star/main.nf:41-60).')
add('P26', 'Gold', 'reference-resource', 'high', lambda e: e['src_instance'].endswith(':STAR_GENOMEGENERATE'),
    'subworkflows/local/prepare_genome_indices/main.nf:168-173 (STAR_GENOMEGENERATE); subworkflows/local/align_star/main.nf:45 SENTIEON_STAR_ALIGN(reads, index, gtf, ...)',
    'Sentieon STAR is an alternative STAR implementation that uses the regular STAR index. Edge E00325 is DAG-confirmed in sentieon_star; the Parabricks-built index edge (E00322) is excluded because the pipeline errors when --use_parabricks_star and --use_sentieon_star are combined (subworkflows/local/utils_nfcore_rnaseq_pipeline/main.nf:323-325).')
add('P27', 'Silver', 'partial-payload', 'medium', None,
    'subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:25-48; modules/nf-core/custom/tx2gene/templates/tx2gene.py:39-57,152-160',
    'Same as P15 for Salmon quant.sf: one file is read to choose the GTF attribute; local script.')
add('P28', 'Gold', 'analysis-data', 'high', None,
    'subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:56-72 TXIMETA_TXIMPORT(ch_tximport_input, CUSTOM_TX2GENE.out.tx2gene, quant_type)',
    'All Salmon result directories are collected (sorted) and imported by tximeta/tximport. Headline example (Salmon downstream).')
add('P29', 'Gold', 'analysis-data', 'high', None,
    'subworkflows/local/align_star/main.nf:61,74; subworkflows/nf-core/bam_sort_stats_samtools/main.nf:15',
    'Sentieon STAR BAM is sorted by samtools exactly like STAR. Alternative-implementation pair; needs use_sentieon_star (preview sentieon_star).')
add('P30', 'Gold', 'analysis-data', 'high', lambda e: e['src_emit'] == 'reads',
    'subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf:294-298 (ch_filtered_reads.join(FQ_LINT_AFTER_TRIMMING.out.lint.map{meta,_lint -> meta})); :307 BBMAP_BBSPLIT(ch_filtered_reads, ...)',
    'Only the TRIMGALORE.reads edge counts: the join partner is key-only (lint reduced to meta, :298), so the payload reaching BBSplit is the trimmed reads. The TRIMGALORE.log edge is a gating dependency (percent-trimmed filter) and is NOT counted.')
add('P31', 'Gold', 'analysis-data', 'high', lambda e: e['src_emit'] == 'reads',
    'subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf:294 FQ_LINT_AFTER_TRIMMING(ch_filtered_reads)',
    'Trimmed reads are linted by fq. The TRIMGALORE.log edge is gating-only and not counted.')
add('P32', 'Gold', 'analysis-data', 'high', None,
    'subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:18,23 UCSC_BEDGRAPHTOBIGWIG(UCSC_BEDCLIP.out.bedgraph, sizes)',
    'Direct, single-source.')
add('P33', 'Gold', 'reference-resource', 'high', None,
    'subworkflows/nf-core/bam_rseqc/main.nf:46,60,77,96,108 (bed input of RSEQC_* modules); subworkflows/local/prepare_genome_references/main.nf:145 EAUTILS_GTF2BED',
    'Gene BED generated from the GTF by ea-utils gtf2bed is the annotation input of five RSeQC modules.')
add('P34', 'Silver', 'utility-script', 'medium', None,
    'subworkflows/nf-core/bam_qc_rnaseq/main.nf:43-48 CUSTOM_MULTIQCCUSTOMBIOTYPE(SUBREAD_FEATURECOUNTS.out.counts, ch_biotypes_header)',
    'featureCounts biotype counts are reformatted by a local Python script for MultiQC (reporting-oriented target).')
add('P35', 'Negative', 'key-only-synchronisation', 'high', None,
    'subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf:325 ch_filtered_reads = ch_filtered_reads.join(FQ_LINT_AFTER_BBSPLIT.out.lint.map { meta, _lint -> meta }); :191,298,358 same pattern',
    'The lint report is reduced to the sample key (_lint dropped). Downstream tools wait for fq lint but never read its output. Not a data exchange.')
add('P36', 'Gold', 'analysis-data', 'high', None,
    'subworkflows/nf-core/fastq_subsample_fq_salmon/main.nf:41-48 FQ_SUBSAMPLE(ch_reads); SALMON_QUANT(FQ_SUBSAMPLE.out.fastq, ...)',
    'Sub-sampled FASTQ is the Salmon reads input (strandedness inference).')
add('P37', 'Silver', TAR, 'high', None,
    'subworkflows/local/prepare_genome_references/main.nf:97 CUSTOM_GTFFILTER(GUNZIP_GTF.gunzip...); :117 CUSTOM_CATADDITIONALFASTA(...)',
    'Decompressed GTF/FASTA is the input of local scripts. Utility to local script.')
add('P38', 'Silver', 'partial-payload', 'medium', None,
    'subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:25-48; tx2gene.py:39-57,152-160',
    'Same as P15 for kallisto abundance files.')
add('P39', 'Gold', 'analysis-data', 'high', None,
    'subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:56-72',
    'kallisto results are imported by tximeta.')
for pid, tgt in (('P40', 'HISAT2_EXTRACTSPLICESITES, subworkflows/local/prepare_genome_indices/main.nf:210'),
                 ('P41', 'QUALIMAP_RNASEQ(…, ch_gtf), subworkflows/nf-core/bam_qc_rnaseq/main.nf:60-62'),
                 ('P42', 'RSEM_PREPAREREFERENCE_GENOME(ch_fasta, ch_gtf), prepare_genome_indices/main.nf:193; MAKE_TRANSCRIPTS_FASTA :180'),
                 ('P43', 'STAR_GENOMEGENERATE (indices:151) and STAR_ALIGN gtf (align_star/main.nf:56)'),
                 ('P44', 'SALMON_QUANT --geneMap ${gtf}: modules/nf-core/salmon/quant/main.nf:55; fastq_subsample_fq_salmon/main.nf:48'),
                 ('P45', 'SENTIEON_STAR_ALIGN gtf, align_star/main.nf:45'),
                 ('P46', 'STRINGTIE_STRINGTIE annotation_gtf, workflows/rnaseq/main.nf:551-555'),
                 ('P48', 'DUPRADAR(…, ch_gtf), bam_qc_rnaseq/main.nf:66-69'),
                 ('P49', 'EAUTILS_GTF2BED, prepare_genome_references/main.nf:145'),
                 ('P50', 'KALLISTO_QUANT gtf slot, quantify_pseudo_alignment/main.nf:38-43')):
    add(pid, 'Silver', 'utility-script', 'medium', None,
        f'subworkflows/local/prepare_genome_references/main.nf:97-103,117-123 (CUSTOM_GTFFILTER / CUSTOM_CATADDITIONALFASTA define ch_gtf and ch_fasta); consumer: {tgt}',
        'The GTF (or FASTA) produced by a local nf-core script (GTF filter / add-additional-fasta) is the annotation input of the named tool. Flow verified; the source node "nf-core custom script (Python)" merges distinct scripts, so Silver. CATADDITIONALFASTA applies only with --additional_fasta, GTFFILTER only when filtering is needed.')
add('P47', 'Silver', 'utility-script', 'medium', None,
    'subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90-93 SE_GENE_UNIFIED(ch_gene_unified, CUSTOM_TX2GENE.out.tx2gene, samplesheet)',
    'The tx2gene table (rowdata) from the local script is consumed by SummarizedExperiment.')
add('P51', 'Silver', 'utility-script', 'medium', None,
    'subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67-71 TXIMETA_TXIMPORT(ch_tximport_input, CUSTOM_TX2GENE.out.tx2gene, quant_type)',
    'The tx2gene table from the local script is a required tximport input.')
add('P52', 'Gold', 'analysis-data', 'high', None,
    'workflows/rnaseq/main.nf:439-441 DESEQ2_QC_*(QUANTIFY_*.out.counts_gene_length_scaled.map{_meta,counts -> counts}, ...)',
    'Length-scaled gene counts from tximeta are the DESeq2 QC input.')
add('P53', 'Gold', 'analysis-data', 'high', None,
    'subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:83-93 (join of tximport outputs failOnMismatch, .map{row -> tuple(row[0], row.tail())} -> SE_GENE_UNIFIED); :100-108 transcript level',
    'Every joined element is a tximeta output and the whole tail becomes matrix_files; the join partners are all siblings of the same producer, so the merge adds no foreign source.')
