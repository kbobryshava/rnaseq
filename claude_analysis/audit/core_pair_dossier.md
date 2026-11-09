# Core-pair dossier (auto-generated; decisions are in curation/core_pair_decisions.csv)


## P01: BBMap (BBSplit) -> fq  (edges 3, tierA 1)
- E00138 NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:BBMAP_BBSPLIT.primary_fastq -> NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:FQ_LINT_AFTER_BBSPLIT[in0] class=direct conf=high ops=
  - producer decl: tuple val(meta), path('*primary*fastq.gz'), optional:true, emit: primary_fastq @ subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf:307; consumer decl: tuple val(meta), path(fastq, arity: '1..2') @ subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf:321; flags=['conditional-consumer', 'conditional-producer']
  - assumes: skip_bbsplit truthy False & skip_linting truthy False; dag: hisat2;hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test

## P02: BEDTools -> UCSC bedClip  (edges 3, tierA 3)
- E01011 NFCORE_RNASEQ:RNASEQ:BEDTOOLS_GENOMECOV_FW.genomecov -> NFCORE_RNASEQ:RNASEQ:BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG_FORWARD:UCSC_BEDCLIP[in0] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*.${extension}"), emit: genomecov @ workflows/rnaseq/main.nf:674; consumer decl: tuple val(meta), path(bedgraph) @ subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:18; flags=['conditional-consumer', 'conditional-producer']
  - assumes: skip_bigwig truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test
- E01015 NFCORE_RNASEQ:RNASEQ:BEDTOOLS_GENOMECOV_REV.genomecov -> NFCORE_RNASEQ:RNASEQ:BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG_REVERSE:UCSC_BEDCLIP[in0] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*.${extension}"), emit: genomecov @ workflows/rnaseq/main.nf:680; consumer decl: tuple val(meta), path(bedgraph) @ subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:18; flags=['conditional-consumer', 'conditional-producer']
  - assumes: skip_bigwig truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test
- E01019 NFCORE_RNASEQ:RNASEQ:BEDTOOLS_GENOMECOV_COMBINED.genomecov -> NFCORE_RNASEQ:RNASEQ:BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG_COMBINED:UCSC_BEDCLIP[in0] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*.${extension}"), emit: genomecov @ workflows/rnaseq/main.nf:686; consumer decl: tuple val(meta), path(bedgraph) @ subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:18; flags=['conditional-consumer', 'conditional-producer']
  - assumes: skip_bigwig truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test

## P03: GNU tar -> Bracken  (edges 1, tierA 1)
- E01046 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:UNTAR_KRAKEN_DB.untar -> NFCORE_RNASEQ:RNASEQ:BRACKEN[in1] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("${prefix}"), emit: untar @ subworkflows/local/prepare_genome_references/main.nf:228; consumer decl: path database @ workflows/rnaseq/main.nf:738; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: contaminant_screening eq kraken2_bracken & contaminant_screening ne kraken2 & contaminant_screening truthy True & kraken_db truthy True & skip_qc truthy False; dag: hisat2_kraken2_bracken;kraken2_bracken

## P04: GNU tar -> HISAT2  (edges 1, tierA 1)
- E00444 NFCORE_RNASEQ:PREPARE_GENOME_INDICES:UNTAR_HISAT2_INDEX.untar -> NFCORE_RNASEQ:RNASEQ:FASTQ_ALIGN_HISAT2:HISAT2_ALIGN[in1] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("${prefix}"), emit: untar @ subworkflows/local/prepare_genome_indices/main.nf:215; consumer decl: tuple val(meta2), path(index) @ subworkflows/nf-core/fastq_align_hisat2/main.nf:16; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: aligner eq hisat2 & hisat2_index truthy True & skip_alignment truthy False; dag: hisat2;hisat2_kraken2_bracken

## P05: GNU tar -> Kraken 2  (edges 1, tierA 1)
- E01044 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:UNTAR_KRAKEN_DB.untar -> NFCORE_RNASEQ:RNASEQ:KRAKEN2[in1] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("${prefix}"), emit: untar @ subworkflows/local/prepare_genome_references/main.nf:228; consumer decl: path db @ workflows/rnaseq/main.nf:725; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: contaminant_screening truthy True & kraken_db truthy True & skip_qc truthy False; dag: hisat2_kraken2_bracken;kraken2;kraken2_bracken

## P06: GNU tar -> Salmon  (edges 2, tierA 2)
- E00294 NFCORE_RNASEQ:PREPARE_GENOME_INDICES:UNTAR_SALMON_INDEX.untar -> NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:FASTQ_SUBSAMPLE_FQ_SALMON:SALMON_QUANT[in1] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("${prefix}"), emit: untar @ subworkflows/local/prepare_genome_indices/main.nf:259; consumer decl: tuple val(meta2), path(index), path(gtf), path(transcript_fasta) @ subworkflows/nf-core/fastq_subsample_fq_salmon/main.nf:48; flags=['alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: salmon_index truthy True; dag: hisat2;hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test
- E01086 NFCORE_RNASEQ:PREPARE_GENOME_INDICES:UNTAR_SALMON_INDEX.untar -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:SALMON_QUANT[in1] class=direct conf=medium ops=first
  - producer decl: tuple val(meta), path("${prefix}"), emit: untar @ subworkflows/local/prepare_genome_indices/main.nf:259; consumer decl: tuple val(meta2), path(index), path(gtf), path(transcript_fasta) @ subworkflows/nf-core/quantify_pseudo_alignment/main.nf:31; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: pseudo_aligner eq salmon & pseudo_aligner truthy True & salmon_index truthy True & skip_pseudo_alignment truthy False; dag: hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test

## P07: HISAT2 -> Kraken 2  (edges 1, tierA 1)
- E01040 NFCORE_RNASEQ:RNASEQ:FASTQ_ALIGN_HISAT2:HISAT2_ALIGN.fastq -> NFCORE_RNASEQ:RNASEQ:KRAKEN2[in0] class=direct conf=medium ops=
  - producer decl: tuple val(meta), path("*fastq.gz"), optional: true, emit: fastq @ subworkflows/nf-core/fastq_align_hisat2/main.nf:16; consumer decl: tuple val(meta), path(reads) @ workflows/rnaseq/main.nf:725; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: aligner eq hisat2 & skip_alignment truthy False & skip_qc truthy False; dag: hisat2_kraken2_bracken

## P08: HISAT2 -> SAMtools  (edges 1, tierA 1)
- E00447 NFCORE_RNASEQ:RNASEQ:FASTQ_ALIGN_HISAT2:HISAT2_ALIGN.bam -> NFCORE_RNASEQ:RNASEQ:FASTQ_ALIGN_HISAT2:BAM_SORT_STATS_SAMTOOLS:SAMTOOLS_SORT[in0] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*.bam"), emit: bam @ subworkflows/nf-core/fastq_align_hisat2/main.nf:16; consumer decl: tuple val(meta), path(bam, stageAs: "?/*") @ subworkflows/nf-core/bam_sort_stats_samtools/main.nf:15; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner eq hisat2 & skip_alignment truthy False; dag: hisat2;hisat2_kraken2_bracken

## P09: Kraken 2 -> Bracken  (edges 1, tierA 1)
- E01045 NFCORE_RNASEQ:RNASEQ:KRAKEN2.report -> NFCORE_RNASEQ:RNASEQ:BRACKEN[in0] class=direct conf=high ops=
  - producer decl: tuple val(meta), path('*report.txt') , emit: report @ workflows/rnaseq/main.nf:725; consumer decl: tuple val(meta), path(kraken_report) @ workflows/rnaseq/main.nf:738; flags=['conditional-consumer', 'conditional-producer']
  - assumes: contaminant_screening eq kraken2_bracken & contaminant_screening ne kraken2 & skip_qc truthy False; dag: hisat2_kraken2_bracken;kraken2_bracken

## P10: NVIDIA Parabricks rna_fq2bam (STAR-based) -> SAMtools  (edges 3, tierA 1)
- E00379 NFCORE_RNASEQ:RNASEQ:ALIGN_STAR:PARABRICKS_RNA_FQ2BAM.bam -> NFCORE_RNASEQ:RNASEQ:ALIGN_STAR:BAM_SORT_STATS_SAMTOOLS:SAMTOOLS_SORT[in0] class=direct conf=medium ops=
  - producer decl: tuple val(meta), path("${prefix}.bam"), emit: bam, optional:true @ subworkflows/local/align_star/main.nf:51; consumer decl: tuple val(meta), path(bam, stageAs: "?/*") @ subworkflows/nf-core/bam_sort_stats_samtools/main.nf:15; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: use_parabricks_star truthy True & use_sentieon_star truthy False; dag: parabricks_star

## P11: Picard -> BEDTools  (edges 3, tierA 3)
- E00963 NFCORE_RNASEQ:RNASEQ:BAM_MARKDUPLICATES_PICARD:PICARD_MARKDUPLICATES.bam -> NFCORE_RNASEQ:RNASEQ:BEDTOOLS_GENOMECOV_FW[in0] class=direct conf=medium ops=filter;map
  - producer decl: tuple val(meta), path("*.bam"), emit: bam, optional: true @ subworkflows/nf-core/bam_markduplicates_picard/main.nf:15; consumer decl: tuple val(meta), path(intervals), val(scale) @ workflows/rnaseq/main.nf:674; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: markdups_done truthy False & skip_bigwig truthy False & skip_markduplicates truthy False & with_umi truthy False; dag: kallisto;kraken2;kraken2_bracken;salmon_pseudo;sentieon_star;star_rsem;test
- E00979 NFCORE_RNASEQ:RNASEQ:BAM_MARKDUPLICATES_PICARD:PICARD_MARKDUPLICATES.bam -> NFCORE_RNASEQ:RNASEQ:BEDTOOLS_GENOMECOV_REV[in0] class=direct conf=medium ops=filter;map
  - producer decl: tuple val(meta), path("*.bam"), emit: bam, optional: true @ subworkflows/nf-core/bam_markduplicates_picard/main.nf:15; consumer decl: tuple val(meta), path(intervals), val(scale) @ workflows/rnaseq/main.nf:680; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: markdups_done truthy False & skip_bigwig truthy False & skip_markduplicates truthy False & with_umi truthy False; dag: kallisto;kraken2;kraken2_bracken;salmon_pseudo;sentieon_star;star_rsem;test
- E00995 NFCORE_RNASEQ:RNASEQ:BAM_MARKDUPLICATES_PICARD:PICARD_MARKDUPLICATES.bam -> NFCORE_RNASEQ:RNASEQ:BEDTOOLS_GENOMECOV_COMBINED[in0] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("*.bam"), emit: bam, optional: true @ subworkflows/nf-core/bam_markduplicates_picard/main.nf:15; consumer decl: tuple val(meta), path(intervals), val(scale) @ workflows/rnaseq/main.nf:686; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: markdups_done truthy False & skip_bigwig truthy False & skip_markduplicates truthy False & with_umi truthy False; dag: kallisto;kraken2;kraken2_bracken;salmon_pseudo;sentieon_star;star_rsem;test

## P12: Picard -> StringTie  (edges 2, tierA 1)
- E00682 NFCORE_RNASEQ:RNASEQ:BAM_MARKDUPLICATES_PICARD:PICARD_MARKDUPLICATES.bam -> NFCORE_RNASEQ:RNASEQ:STRINGTIE_STRINGTIE[in0] class=direct conf=medium ops=
  - producer decl: tuple val(meta), path("*.bam"), emit: bam, optional: true @ subworkflows/nf-core/bam_markduplicates_picard/main.nf:15; consumer decl: tuple val(meta), path(srbam), path(lrbam) @ workflows/rnaseq/main.nf:551; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: markdups_done truthy False & skip_markduplicates truthy False & skip_stringtie truthy False & with_umi truthy False; dag: hisat2;hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;salmon_pseudo;sentieon_star;star_rsem;test

## P13: RSEM -> Salmon  (edges 4, tierA 2)
- E00304 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:MAKE_TRANSCRIPTS_FASTA.transcript_fasta -> NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:FASTQ_SUBSAMPLE_FQ_SALMON:SALMON_QUANT[in1] class=merged-channel conf=medium ops=combine
  - producer decl: path "*transcripts.fa", emit: transcript_fasta @ subworkflows/local/prepare_genome_references/main.nf:180; consumer decl: tuple val(meta2), path(index), path(gtf), path(transcript_fasta) @ subworkflows/nf-core/fastq_subsample_fq_salmon/main.nf:48; flags=['alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: fasta_provided truthy True & gffread_transcript_fasta truthy False & transcript_fasta truthy False & use_sentieon_star truthy False; dag: kallisto
- E00598 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:MAKE_TRANSCRIPTS_FASTA.transcript_fasta -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:SALMON_QUANT[in1] class=direct conf=medium ops=
  - producer decl: path "*transcripts.fa", emit: transcript_fasta @ subworkflows/local/prepare_genome_references/main.nf:180; consumer decl: tuple val(meta2), path(index), path(gtf), path(transcript_fasta) @ subworkflows/nf-core/quantify_pseudo_alignment/main.nf:31; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: aligner ne star_rsem & fasta_provided truthy True & gffread_transcript_fasta truthy False & pseudo_aligner eq salmon & transcript_fasta truthy False & use_sentieon_star truthy False; dag: kallisto

## P14: RSEM -> kallisto  (edges 1, tierA 1)
- E00101 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:MAKE_TRANSCRIPTS_FASTA.transcript_fasta -> NFCORE_RNASEQ:PREPARE_GENOME_INDICES:KALLISTO_INDEX[in0] class=direct conf=medium ops=
  - producer decl: path "*transcripts.fa", emit: transcript_fasta @ subworkflows/local/prepare_genome_references/main.nf:180; consumer decl: tuple val(meta), path(fasta) @ subworkflows/local/prepare_genome_indices/main.nf:292; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: fasta_provided truthy True & gffread_transcript_fasta truthy False & kallisto_index truthy False & transcript_fasta truthy False & use_sentieon_star truthy False; dag: kallisto

## P15: RSEM -> nf-core custom script (Python)  (edges 1, tierA 1)
- E00569 NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:RSEM_CALCULATEEXPRESSION.counts_transcript -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:CUSTOM_TX2GENE[in1] class=direct conf=medium ops=filter;first;map;size;toSortedList
  - producer decl: tuple val(meta), path("*.isoforms.results"), emit: counts_transcript @ subworkflows/nf-core/quantify_rsem/main.nf:32; consumer decl: tuple val(meta2), path ("quants/*") @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:43; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: aligner eq star_rsem & use_sentieon_star truthy False; dag: star_rsem

## P16: RSEM -> sed  (edges 2, tierA 2)
- E00561 NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:RSEM_CALCULATEEXPRESSION.counts_gene -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:CUSTOM_RSEMMERGECOUNTS[in0] class=direct conf=medium ops=
  - producer decl: tuple val(meta), path("*.genes.results") , emit: counts_gene @ subworkflows/nf-core/quantify_rsem/main.nf:32; consumer decl: tuple val(meta), path ('genes/*') @ subworkflows/nf-core/quantify_rsem/main.nf:58; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: aligner eq star_rsem & skip_merge truthy False & use_sentieon_star truthy False; dag: star_rsem
- E00563 NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:RSEM_CALCULATEEXPRESSION.counts_transcript -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:CUSTOM_RSEMMERGECOUNTS[in1] class=direct conf=medium ops=
  - producer decl: tuple val(meta), path("*.isoforms.results"), emit: counts_transcript @ subworkflows/nf-core/quantify_rsem/main.nf:32; consumer decl: path ('isoforms/*') @ subworkflows/nf-core/quantify_rsem/main.nf:58; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: aligner eq star_rsem & skip_merge truthy False & use_sentieon_star truthy False; dag: star_rsem

## P17: RSEM -> tximeta  (edges 1, tierA 1)
- E00571 NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:RSEM_CALCULATEEXPRESSION.counts_transcript -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT[in0] class=direct conf=medium ops=collect;filter;map;size;toSortedList
  - producer decl: tuple val(meta), path("*.isoforms.results"), emit: counts_transcript @ subworkflows/nf-core/quantify_rsem/main.nf:32; consumer decl: tuple val(meta), path("quants/*") @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: aligner eq star_rsem & use_sentieon_star truthy False; dag: star_rsem

## P18: SAMtools -> BBMap (BBSplit)  (edges 1, tierA 1)
- E00041 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:SAMTOOLS_FAIDX.fai -> NFCORE_RNASEQ:PREPARE_GENOME_INDICES:BBMAP_BBSPLIT[in2] class=merged-channel conf=medium ops=combine;first;map
  - producer decl: tuple val(meta), path("*.fai"), emit: fai, optional: true @ subworkflows/local/prepare_genome_references/main.nf:191; consumer decl: path primary_ref @ subworkflows/local/prepare_genome_indices/main.nf:96; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: bbsplit_index truthy False & fasta_provided truthy True; dag: kallisto

## P19: SAMtools -> Picard  (edges 8, tierA 1)
- E00642 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:SAMTOOLS_FAIDX.fai -> NFCORE_RNASEQ:RNASEQ:BAM_MARKDUPLICATES_PICARD:PICARD_MARKDUPLICATES[in1] class=merged-channel conf=medium ops=combine;first;map
  - producer decl: tuple val(meta), path("*.fai"), emit: fai, optional: true @ subworkflows/local/prepare_genome_references/main.nf:191; consumer decl: tuple val(meta2), path(fasta), path(fai) @ subworkflows/nf-core/bam_markduplicates_picard/main.nf:15; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: fasta_provided truthy True & markdups_done truthy False & skip_markduplicates truthy False & with_umi truthy False; dag: kallisto

## P20: SAMtools -> Qualimap  (edges 1, tierA 1)
- E00783 NFCORE_RNASEQ:RNASEQ:BAM_QC_RNASEQ:SAMTOOLS_SORT_QUALIMAP.bam -> NFCORE_RNASEQ:RNASEQ:BAM_QC_RNASEQ:QUALIMAP_RNASEQ[in0] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("${prefix}.bam"), emit: bam, optional: true @ subworkflows/nf-core/bam_qc_rnaseq/main.nf:54; consumer decl: tuple val(meta), path(bam) @ subworkflows/nf-core/bam_qc_rnaseq/main.nf:60; flags=['conditional-consumer', 'conditional-producer']
  - assumes: skip_qc truthy False & use_rustqc truthy False; dag: hisat2;hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;sentieon_star;star_rsem;test

## P21: SAMtools -> UCSC bedClip  (edges 3, tierA 3)
- E01012 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:SAMTOOLS_FAIDX.sizes -> NFCORE_RNASEQ:RNASEQ:BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG_FORWARD:UCSC_BEDCLIP[in1] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("*.sizes"), emit: sizes, optional: true @ subworkflows/local/prepare_genome_references/main.nf:191; consumer decl: path sizes @ subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:18; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: fasta_provided truthy True & skip_bigwig truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test
- E01016 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:SAMTOOLS_FAIDX.sizes -> NFCORE_RNASEQ:RNASEQ:BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG_REVERSE:UCSC_BEDCLIP[in1] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("*.sizes"), emit: sizes, optional: true @ subworkflows/local/prepare_genome_references/main.nf:191; consumer decl: path sizes @ subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:18; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: fasta_provided truthy True & skip_bigwig truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test
- E01020 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:SAMTOOLS_FAIDX.sizes -> NFCORE_RNASEQ:RNASEQ:BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG_COMBINED:UCSC_BEDCLIP[in1] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("*.sizes"), emit: sizes, optional: true @ subworkflows/local/prepare_genome_references/main.nf:191; consumer decl: path sizes @ subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:18; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: fasta_provided truthy True & skip_bigwig truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test

## P22: SAMtools -> UCSC bedGraphToBigWig  (edges 3, tierA 3)
- E01014 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:SAMTOOLS_FAIDX.sizes -> NFCORE_RNASEQ:RNASEQ:BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG_FORWARD:UCSC_BEDGRAPHTOBIGWIG[in1] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("*.sizes"), emit: sizes, optional: true @ subworkflows/local/prepare_genome_references/main.nf:191; consumer decl: path sizes @ subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:23; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: fasta_provided truthy True & skip_bigwig truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test
- E01018 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:SAMTOOLS_FAIDX.sizes -> NFCORE_RNASEQ:RNASEQ:BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG_REVERSE:UCSC_BEDGRAPHTOBIGWIG[in1] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("*.sizes"), emit: sizes, optional: true @ subworkflows/local/prepare_genome_references/main.nf:191; consumer decl: path sizes @ subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:23; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: fasta_provided truthy True & skip_bigwig truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test
- E01022 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:SAMTOOLS_FAIDX.sizes -> NFCORE_RNASEQ:RNASEQ:BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG_COMBINED:UCSC_BEDGRAPHTOBIGWIG[in1] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("*.sizes"), emit: sizes, optional: true @ subworkflows/local/prepare_genome_references/main.nf:191; consumer decl: path sizes @ subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:23; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: fasta_provided truthy True & skip_bigwig truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test

## P23: STAR -> Kraken 2  (edges 1, tierA 1)
- E01043 NFCORE_RNASEQ:RNASEQ:ALIGN_STAR:STAR_ALIGN.fastq -> NFCORE_RNASEQ:RNASEQ:KRAKEN2[in0] class=direct conf=medium ops=
  - producer decl: tuple val(meta), path('*fastq.gz') , optional:true, emit: fastq @ subworkflows/local/align_star/main.nf:56; consumer decl: tuple val(meta), path(reads) @ workflows/rnaseq/main.nf:725; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: skip_qc truthy False & use_parabricks_star truthy False & use_sentieon_star truthy False; dag: kraken2;kraken2_bracken

## P24: STAR -> NVIDIA Parabricks rna_fq2bam (STAR-based)  (edges 2, tierA 1)
- E00350 NFCORE_RNASEQ:PREPARE_GENOME_INDICES:PARABRICKS_STARGENOMEGENERATE.index -> NFCORE_RNASEQ:RNASEQ:ALIGN_STAR:PARABRICKS_RNA_FQ2BAM[in2] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("star") , emit: index @ subworkflows/local/prepare_genome_indices/main.nf:151; consumer decl: tuple val(meta3), path(index) @ subworkflows/local/align_star/main.nf:51; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: fasta_provided truthy True & use_parabricks_star truthy True & use_sentieon_star truthy False; dag: parabricks_star

## P25: STAR -> SAMtools  (edges 3, tierA 1)
- E00380 NFCORE_RNASEQ:RNASEQ:ALIGN_STAR:STAR_ALIGN.bam -> NFCORE_RNASEQ:RNASEQ:ALIGN_STAR:BAM_SORT_STATS_SAMTOOLS:SAMTOOLS_SORT[in0] class=direct conf=medium ops=
  - producer decl: tuple val(meta), path('*d.out.bam') , optional:true, emit: bam @ subworkflows/local/align_star/main.nf:56; consumer decl: tuple val(meta), path(bam, stageAs: "?/*") @ subworkflows/nf-core/bam_sort_stats_samtools/main.nf:15; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: use_parabricks_star truthy False & use_sentieon_star truthy False; dag: kraken2;kraken2_bracken;star_rsem;test

## P26: STAR -> Sentieon STAR  (edges 2, tierA 1)
- E00325 NFCORE_RNASEQ:PREPARE_GENOME_INDICES:STAR_GENOMEGENERATE.index -> NFCORE_RNASEQ:RNASEQ:ALIGN_STAR:SENTIEON_STAR_ALIGN[in1] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("star") , emit: index @ subworkflows/local/prepare_genome_indices/main.nf:169; consumer decl: tuple val(meta2), path(index) @ subworkflows/local/align_star/main.nf:45; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: fasta_provided truthy True & star_index truthy False & use_sentieon_star truthy True; dag: sentieon_star

## P27: Salmon -> nf-core custom script (Python)  (edges 2, tierA 2)
- E00613 NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:SALMON_QUANT.results -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:CUSTOM_TX2GENE[in1] class=direct conf=medium ops=filter;first;map;size;toSortedList
  - producer decl: tuple val(meta), path("${prefix}"), emit: results @ subworkflows/nf-core/quantify_pseudo_alignment/main.nf:31; consumer decl: tuple val(meta2), path ("quants/*") @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:43; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: aligner ne star_rsem & pseudo_aligner eq salmon; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E01119 NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:SALMON_QUANT.results -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:CUSTOM_TX2GENE[in1] class=direct conf=medium ops=filter;first;map;size;toSortedList
  - producer decl: tuple val(meta), path("${prefix}"), emit: results @ subworkflows/nf-core/quantify_pseudo_alignment/main.nf:31; consumer decl: tuple val(meta2), path ("quants/*") @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:43; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: pseudo_aligner eq salmon & pseudo_aligner truthy True & skip_pseudo_alignment truthy False; dag: hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test

## P28: Salmon -> tximeta  (edges 2, tierA 2)
- E00615 NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:SALMON_QUANT.results -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT[in0] class=direct conf=medium ops=collect;filter;map;size;toSortedList
  - producer decl: tuple val(meta), path("${prefix}"), emit: results @ subworkflows/nf-core/quantify_pseudo_alignment/main.nf:31; consumer decl: tuple val(meta), path("quants/*") @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: aligner ne star_rsem & pseudo_aligner eq salmon; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E01121 NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:SALMON_QUANT.results -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT[in0] class=direct conf=medium ops=collect;filter;map;size;toSortedList
  - producer decl: tuple val(meta), path("${prefix}"), emit: results @ subworkflows/nf-core/quantify_pseudo_alignment/main.nf:31; consumer decl: tuple val(meta), path("quants/*") @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: pseudo_aligner eq salmon & pseudo_aligner truthy True & skip_pseudo_alignment truthy False; dag: hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test

## P29: Sentieon STAR -> SAMtools  (edges 3, tierA 1)
- E00378 NFCORE_RNASEQ:RNASEQ:ALIGN_STAR:SENTIEON_STAR_ALIGN.bam -> NFCORE_RNASEQ:RNASEQ:ALIGN_STAR:BAM_SORT_STATS_SAMTOOLS:SAMTOOLS_SORT[in0] class=direct conf=medium ops=
  - producer decl: tuple val(meta), path('*d.out.bam'), emit: bam, optional: true @ subworkflows/local/align_star/main.nf:45; consumer decl: tuple val(meta), path(bam, stageAs: "?/*") @ subworkflows/nf-core/bam_sort_stats_samtools/main.nf:15; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: use_sentieon_star truthy True; dag: sentieon_star

## P30: Trim Galore -> BBMap (BBSplit)  (edges 2, tierA 2)
- E00130 NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:FASTQ_FASTQC_UMITOOLS_TRIMGALORE:TRIMGALORE.reads -> NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:BBMAP_BBSPLIT[in0] class=merged-channel conf=medium ops=filter;join;map;toFloat
  - producer decl: tuple val(meta), path("*{3prime,5prime,trimmed,val}{,_1,_2}.fq.gz"), emit: reads @ subworkflows/nf-core/fastq_fastqc_umitools_trimgalore/main.nf:74; consumer decl: tuple val(meta), path(reads) @ subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf:307; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: skip_bbsplit truthy False & skip_trimming truthy False & trimmer eq trimgalore; dag: hisat2;hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test
- E00131 NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:FASTQ_FASTQC_UMITOOLS_TRIMGALORE:TRIMGALORE.log -> NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:BBMAP_BBSPLIT[in0] class=gating-or-metadata conf=low ops=filter;join;map;toFloat
  - producer decl: tuple val(meta), path("*report.txt") , emit: log , optional: true @ subworkflows/nf-core/fastq_fastqc_umitools_trimgalore/main.nf:74; consumer decl: tuple val(meta), path(reads) @ subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf:307; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: skip_bbsplit truthy False & skip_trimming truthy False & trimmer eq trimgalore; dag: hisat2;hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test

## P31: Trim Galore -> fq  (edges 6, tierA 2)
- E00122 NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:FASTQ_FASTQC_UMITOOLS_TRIMGALORE:TRIMGALORE.reads -> NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:FQ_LINT_AFTER_TRIMMING[in0] class=merged-channel conf=medium ops=filter;join;map;toFloat
  - producer decl: tuple val(meta), path("*{3prime,5prime,trimmed,val}{,_1,_2}.fq.gz"), emit: reads @ subworkflows/nf-core/fastq_fastqc_umitools_trimgalore/main.nf:74; consumer decl: tuple val(meta), path(fastq, arity: '1..2') @ subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf:294; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: skip_trimming truthy False & trimmer eq trimgalore; dag: hisat2;hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test
- E00123 NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:FASTQ_FASTQC_UMITOOLS_TRIMGALORE:TRIMGALORE.log -> NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:FQ_LINT_AFTER_TRIMMING[in0] class=gating-or-metadata conf=low ops=filter;join;map;toFloat
  - producer decl: tuple val(meta), path("*report.txt") , emit: log , optional: true @ subworkflows/nf-core/fastq_fastqc_umitools_trimgalore/main.nf:74; consumer decl: tuple val(meta), path(fastq, arity: '1..2') @ subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf:294; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: skip_trimming truthy False & trimmer eq trimgalore; dag: hisat2;hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test

## P32: UCSC bedClip -> UCSC bedGraphToBigWig  (edges 3, tierA 3)
- E01013 NFCORE_RNASEQ:RNASEQ:BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG_FORWARD:UCSC_BEDCLIP.bedgraph -> NFCORE_RNASEQ:RNASEQ:BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG_FORWARD:UCSC_BEDGRAPHTOBIGWIG[in0] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*.bedGraph"), emit: bedgraph @ subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:18; consumer decl: tuple val(meta), path(bedgraph) @ subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:23; flags=['conditional-consumer', 'conditional-producer']
  - assumes: skip_bigwig truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test
- E01017 NFCORE_RNASEQ:RNASEQ:BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG_REVERSE:UCSC_BEDCLIP.bedgraph -> NFCORE_RNASEQ:RNASEQ:BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG_REVERSE:UCSC_BEDGRAPHTOBIGWIG[in0] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*.bedGraph"), emit: bedgraph @ subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:18; consumer decl: tuple val(meta), path(bedgraph) @ subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:23; flags=['conditional-consumer', 'conditional-producer']
  - assumes: skip_bigwig truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test
- E01021 NFCORE_RNASEQ:RNASEQ:BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG_COMBINED:UCSC_BEDCLIP.bedgraph -> NFCORE_RNASEQ:RNASEQ:BEDGRAPH_BEDCLIP_BEDGRAPHTOBIGWIG_COMBINED:UCSC_BEDGRAPHTOBIGWIG[in0] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*.bedGraph"), emit: bedgraph @ subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:18; consumer decl: tuple val(meta), path(bedgraph) @ subworkflows/nf-core/bedgraph_bedclip_bedgraphtobigwig/main.nf:23; flags=['conditional-consumer', 'conditional-producer']
  - assumes: skip_bigwig truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test

## P33: ea-utils gtf2bed -> RSeQC  (edges 6, tierA 5)
- E00845 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:EAUTILS_GTF2BED.bed -> NFCORE_RNASEQ:RNASEQ:BAM_QC_RNASEQ:BAM_RSEQC:RSEQC_INNERDISTANCE[in1] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("${prefix}.bed") , emit: bed @ subworkflows/local/prepare_genome_references/main.nf:145; consumer decl: path bed @ subworkflows/nf-core/bam_rseqc/main.nf:46; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: gene_bed truthy False & prokaryotic truthy False & skip_qc truthy False & use_rustqc truthy False; dag: hisat2;hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;sentieon_star;star_rsem;test
- E00865 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:EAUTILS_GTF2BED.bed -> NFCORE_RNASEQ:RNASEQ:BAM_QC_RNASEQ:BAM_RSEQC:RSEQC_INFEREXPERIMENT[in1] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("${prefix}.bed") , emit: bed @ subworkflows/local/prepare_genome_references/main.nf:145; consumer decl: path bed @ subworkflows/nf-core/bam_rseqc/main.nf:60; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: gene_bed truthy False & prokaryotic truthy False & skip_qc truthy False & use_rustqc truthy False; dag: hisat2;hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;sentieon_star;star_rsem;test
- E00885 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:EAUTILS_GTF2BED.bed -> NFCORE_RNASEQ:RNASEQ:BAM_QC_RNASEQ:BAM_RSEQC:RSEQC_JUNCTIONANNOTATION[in1] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("${prefix}.bed") , emit: bed @ subworkflows/local/prepare_genome_references/main.nf:145; consumer decl: path bed @ subworkflows/nf-core/bam_rseqc/main.nf:77; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: gene_bed truthy False & prokaryotic truthy False & skip_qc truthy False & use_rustqc truthy False; dag: hisat2;hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;sentieon_star;star_rsem;test
- E00905 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:EAUTILS_GTF2BED.bed -> NFCORE_RNASEQ:RNASEQ:BAM_QC_RNASEQ:BAM_RSEQC:RSEQC_JUNCTIONSATURATION[in1] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("${prefix}.bed") , emit: bed @ subworkflows/local/prepare_genome_references/main.nf:145; consumer decl: path bed @ subworkflows/nf-core/bam_rseqc/main.nf:96; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: gene_bed truthy False & prokaryotic truthy False & skip_qc truthy False & use_rustqc truthy False; dag: hisat2;hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;sentieon_star;star_rsem;test
- E00925 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:EAUTILS_GTF2BED.bed -> NFCORE_RNASEQ:RNASEQ:BAM_QC_RNASEQ:BAM_RSEQC:RSEQC_READDISTRIBUTION[in1] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("${prefix}.bed") , emit: bed @ subworkflows/local/prepare_genome_references/main.nf:145; consumer decl: path bed @ subworkflows/nf-core/bam_rseqc/main.nf:108; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: gene_bed truthy False & prokaryotic truthy False & skip_qc truthy False & use_rustqc truthy False; dag: hisat2;hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;sentieon_star;star_rsem;test

## P34: featureCounts (Subread) -> nf-core custom script (Python)  (edges 1, tierA 1)
- E00762 NFCORE_RNASEQ:RNASEQ:BAM_QC_RNASEQ:SUBREAD_FEATURECOUNTS.counts -> NFCORE_RNASEQ:RNASEQ:BAM_QC_RNASEQ:CUSTOM_MULTIQCCUSTOMBIOTYPE[in0] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*featureCounts.tsv"), emit: counts @ subworkflows/nf-core/bam_qc_rnaseq/main.nf:39; consumer decl: tuple val(meta), path(count) @ subworkflows/nf-core/bam_qc_rnaseq/main.nf:45; flags=['conditional-consumer', 'conditional-producer']
  - assumes: skip_qc truthy False & use_rustqc truthy False; dag: hisat2;hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;sentieon_star;star_rsem;test

## P35: fq -> BBMap (BBSplit)  (edges 2, tierA 1)
- E00135 NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:FQ_LINT_AFTER_TRIMMING.lint -> NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:BBMAP_BBSPLIT[in0] class=key-only-synchronization conf=low ops=join;map
  - producer decl: tuple val(meta), path("*.fq_lint.txt"), emit: lint @ subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf:294; consumer decl: tuple val(meta), path(reads) @ subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf:307; flags=['closure-with-unused-param(weak)', 'key-only(sample key kept, payload dropped)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: skip_bbsplit truthy False; dag: hisat2;hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test

## P36: fq -> Salmon  (edges 9, tierA 1)
- E00292 NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:FASTQ_SUBSAMPLE_FQ_SALMON:FQ_SUBSAMPLE.fastq -> NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:FASTQ_SUBSAMPLE_FQ_SALMON:SALMON_QUANT[in0] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*.fastq.gz"), emit: fastq @ subworkflows/nf-core/fastq_subsample_fq_salmon/main.nf:43; consumer decl: tuple val(meta), path(reads) @ subworkflows/nf-core/fastq_subsample_fq_salmon/main.nf:48; flags=[]
  - assumes: ; dag: hisat2;hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test

## P37: gzip (gunzip) -> nf-core custom script (Python)  (edges 8, tierA 2)
- E00002 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:GUNZIP_GTF.gunzip -> NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_GTFFILTER[in0] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("${gunzip}"), emit: gunzip @ subworkflows/local/prepare_genome_references/main.nf:58; consumer decl: tuple val(meta), path(gtf) @ subworkflows/local/prepare_genome_references/main.nf:97; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: filter_gtf_needed truthy True & gtf truthy True; dag: hisat2;hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test
- E00009 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:GUNZIP_ADDITIONAL_FASTA.gunzip -> NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA[in1] class=direct conf=medium ops=map
  - producer decl: tuple val(meta), path("${gunzip}"), emit: gunzip @ subworkflows/local/prepare_genome_references/main.nf:112; consumer decl: tuple val(meta2), path(add_fasta) @ subworkflows/local/prepare_genome_references/main.nf:117; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & fasta_provided truthy True; dag: hisat2;hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test

## P38: kallisto -> nf-core custom script (Python)  (edges 2, tierA 1)
- E01120 NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:KALLISTO_QUANT.results -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:CUSTOM_TX2GENE[in1] class=direct conf=medium ops=filter;first;map;size;toSortedList
  - producer decl: tuple val(meta), path("${prefix}") , emit: results @ subworkflows/nf-core/quantify_pseudo_alignment/main.nf:38; consumer decl: tuple val(meta2), path ("quants/*") @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:43; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: pseudo_aligner ne salmon & pseudo_aligner truthy True & skip_pseudo_alignment truthy False; dag: kallisto

## P39: kallisto -> tximeta  (edges 2, tierA 1)
- E01122 NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:KALLISTO_QUANT.results -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT[in0] class=direct conf=medium ops=collect;filter;map;size;toSortedList
  - producer decl: tuple val(meta), path("${prefix}") , emit: results @ subworkflows/nf-core/quantify_pseudo_alignment/main.nf:38; consumer decl: tuple val(meta), path("quants/*") @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: pseudo_aligner ne salmon & pseudo_aligner truthy True & skip_pseudo_alignment truthy False; dag: kallisto

## P40: nf-core custom script (Python) -> HISAT2  (edges 5, tierA 1)
- E00072 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA.gtf -> NFCORE_RNASEQ:PREPARE_GENOME_INDICES:HISAT2_EXTRACTSPLICESITES[in0] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("out/${prefix}.gtf") , emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:117; consumer decl: tuple val(meta), path(gtf) @ subworkflows/local/prepare_genome_indices/main.nf:210; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & fasta_provided truthy True & splicesites truthy False; dag: hisat2;hisat2_kraken2_bracken

## P41: nf-core custom script (Python) -> Qualimap  (edges 2, tierA 1)
- E00784 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA.gtf -> NFCORE_RNASEQ:RNASEQ:BAM_QC_RNASEQ:QUALIMAP_RNASEQ[in1] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("out/${prefix}.gtf") , emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:117; consumer decl: tuple val(meta2), path(gtf) @ subworkflows/nf-core/bam_qc_rnaseq/main.nf:60; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & fasta_provided truthy True & skip_qc truthy False & use_rustqc truthy False; dag: hisat2;hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;sentieon_star;star_rsem;test

## P42: nf-core custom script (Python) -> RSEM  (edges 6, tierA 3)
- E00034 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_GTFFILTER.gtf -> NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:MAKE_TRANSCRIPTS_FASTA[in1] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("${prefix}.${suffix}"), emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:97; consumer decl: path gtf @ subworkflows/local/prepare_genome_references/main.nf:180; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: fasta_provided truthy True & filter_gtf_needed truthy True & gffread_transcript_fasta truthy False & transcript_fasta truthy False & use_sentieon_star truthy False; dag: kallisto
- E00065 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA.fasta -> NFCORE_RNASEQ:PREPARE_GENOME_INDICES:RSEM_PREPAREREFERENCE_GENOME[in0] class=merged-channel conf=medium ops=combine;first;map
  - producer decl: tuple val(meta), path("out/${prefix}.fasta"), emit: fasta @ subworkflows/local/prepare_genome_references/main.nf:117; consumer decl: path fasta, stageAs: "rsem/*" @ subworkflows/local/prepare_genome_indices/main.nf:193; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & fasta_provided truthy True & rsem_index truthy False & use_sentieon_star truthy False; dag: star_rsem
- E00068 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA.gtf -> NFCORE_RNASEQ:PREPARE_GENOME_INDICES:RSEM_PREPAREREFERENCE_GENOME[in1] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("out/${prefix}.gtf") , emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:117; consumer decl: path gtf @ subworkflows/local/prepare_genome_indices/main.nf:193; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & fasta_provided truthy True & rsem_index truthy False & use_sentieon_star truthy False; dag: star_rsem

## P43: nf-core custom script (Python) -> STAR  (edges 8, tierA 5)
- E00043 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA.fasta -> NFCORE_RNASEQ:PREPARE_GENOME_INDICES:PARABRICKS_STARGENOMEGENERATE[in0] class=merged-channel conf=medium ops=combine;first;map
  - producer decl: tuple val(meta), path("out/${prefix}.fasta"), emit: fasta @ subworkflows/local/prepare_genome_references/main.nf:117; consumer decl: tuple val(meta), path(fasta) @ subworkflows/local/prepare_genome_indices/main.nf:151; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & fasta_provided truthy True & use_parabricks_star truthy True; dag: parabricks_star
- E00046 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA.gtf -> NFCORE_RNASEQ:PREPARE_GENOME_INDICES:PARABRICKS_STARGENOMEGENERATE[in1] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("out/${prefix}.gtf") , emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:117; consumer decl: tuple val(meta2), path(gtf) @ subworkflows/local/prepare_genome_indices/main.nf:151; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & fasta_provided truthy True & use_parabricks_star truthy True; dag: parabricks_star
- E00051 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA.fasta -> NFCORE_RNASEQ:PREPARE_GENOME_INDICES:STAR_GENOMEGENERATE[in0] class=merged-channel conf=medium ops=combine;first;map
  - producer decl: tuple val(meta), path("out/${prefix}.fasta"), emit: fasta @ subworkflows/local/prepare_genome_references/main.nf:117; consumer decl: tuple val(meta), path(fasta) @ subworkflows/local/prepare_genome_indices/main.nf:169; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & fasta_provided truthy True & star_index truthy False; dag: kraken2;kraken2_bracken;sentieon_star;star_rsem;test
- E00054 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA.gtf -> NFCORE_RNASEQ:PREPARE_GENOME_INDICES:STAR_GENOMEGENERATE[in1] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("out/${prefix}.gtf") , emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:117; consumer decl: tuple val(meta2), path(gtf) @ subworkflows/local/prepare_genome_indices/main.nf:169; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & fasta_provided truthy True & star_index truthy False; dag: kraken2;kraken2_bracken;sentieon_star;star_rsem;test
- E00374 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA.gtf -> NFCORE_RNASEQ:RNASEQ:ALIGN_STAR:STAR_ALIGN[in2] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("out/${prefix}.gtf") , emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:117; consumer decl: tuple val(meta3), path(gtf) @ subworkflows/local/align_star/main.nf:56; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & fasta_provided truthy True & use_parabricks_star truthy False & use_sentieon_star truthy False; dag: kraken2;kraken2_bracken;star_rsem;test

## P44: nf-core custom script (Python) -> Salmon  (edges 8, tierA 5)
- E00296 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA.gtf -> NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:FASTQ_SUBSAMPLE_FQ_SALMON:SALMON_QUANT[in1] class=merged-channel conf=medium ops=combine;first;map
  - producer decl: tuple val(meta), path("out/${prefix}.gtf") , emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:117; consumer decl: tuple val(meta2), path(index), path(gtf), path(transcript_fasta) @ subworkflows/nf-core/fastq_subsample_fq_salmon/main.nf:48; flags=['alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & fasta_provided truthy True; dag: hisat2;hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test
- E00297 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_GTFFILTER.gtf -> NFCORE_RNASEQ:RNASEQ:FASTQ_QC_TRIM_FILTER_SETSTRANDEDNESS:FASTQ_SUBSAMPLE_FQ_SALMON:SALMON_QUANT[in1] class=merged-channel conf=medium ops=combine;first;map
  - producer decl: tuple val(meta), path("${prefix}.${suffix}"), emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:97; consumer decl: tuple val(meta2), path(index), path(gtf), path(transcript_fasta) @ subworkflows/nf-core/fastq_subsample_fq_salmon/main.nf:48; flags=['closure-with-unused-param(weak)', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: filter_gtf_needed truthy True; dag: kallisto
- E00590 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA.gtf -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:SALMON_QUANT[in1] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("out/${prefix}.gtf") , emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:117; consumer decl: tuple val(meta2), path(index), path(gtf), path(transcript_fasta) @ subworkflows/nf-core/quantify_pseudo_alignment/main.nf:31; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & aligner ne star_rsem & fasta_provided truthy True & pseudo_aligner eq salmon; dag: kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E00591 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_GTFFILTER.gtf -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:SALMON_QUANT[in1] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("${prefix}.${suffix}"), emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:97; consumer decl: tuple val(meta2), path(index), path(gtf), path(transcript_fasta) @ subworkflows/nf-core/quantify_pseudo_alignment/main.nf:31; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: aligner ne star_rsem & filter_gtf_needed truthy True & pseudo_aligner eq salmon; dag: kallisto
- E01088 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA.gtf -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:SALMON_QUANT[in1] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("out/${prefix}.gtf") , emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:117; consumer decl: tuple val(meta2), path(index), path(gtf), path(transcript_fasta) @ subworkflows/nf-core/quantify_pseudo_alignment/main.nf:31; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & fasta_provided truthy True & pseudo_aligner eq salmon & pseudo_aligner truthy True & skip_pseudo_alignment truthy False; dag: hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test

## P45: nf-core custom script (Python) -> Sentieon STAR  (edges 2, tierA 1)
- E00326 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA.gtf -> NFCORE_RNASEQ:RNASEQ:ALIGN_STAR:SENTIEON_STAR_ALIGN[in2] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("out/${prefix}.gtf") , emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:117; consumer decl: tuple val(meta3), path(gtf) @ subworkflows/local/align_star/main.nf:45; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & fasta_provided truthy True & use_sentieon_star truthy True; dag: sentieon_star

## P46: nf-core custom script (Python) -> StringTie  (edges 6, tierA 2)
- E00699 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA.gtf -> NFCORE_RNASEQ:RNASEQ:STRINGTIE_STRINGTIE[in2] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("out/${prefix}.gtf") , emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:117; consumer decl: path(annotation_gtf) @ workflows/rnaseq/main.nf:551; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & fasta_provided truthy True & skip_stringtie truthy False & stringtie_ignore_gtf truthy False; dag: hisat2;hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test
- E00700 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_GTFFILTER.gtf -> NFCORE_RNASEQ:RNASEQ:STRINGTIE_STRINGTIE[in2] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("${prefix}.${suffix}"), emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:97; consumer decl: path(annotation_gtf) @ workflows/rnaseq/main.nf:551; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: filter_gtf_needed truthy True & skip_stringtie truthy False & stringtie_ignore_gtf truthy False; dag: kallisto

## P47: nf-core custom script (Python) -> SummarizedExperiment  (edges 3, tierA 3)
- E00578 NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:CUSTOM_TX2GENE.tx2gene -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in1] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*tx2gene.tsv"), emit: tx2gene @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:43; consumer decl: tuple val(meta2), path(rowdata) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner eq star_rsem & skip_merge truthy False; dag: star_rsem
- E00623 NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:CUSTOM_TX2GENE.tx2gene -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in1] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*tx2gene.tsv"), emit: tx2gene @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:43; consumer decl: tuple val(meta2), path(rowdata) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner ne star_rsem & skip_merge truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E01129 NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:CUSTOM_TX2GENE.tx2gene -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in1] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*tx2gene.tsv"), emit: tx2gene @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:43; consumer decl: tuple val(meta2), path(rowdata) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: pseudo_aligner truthy True & skip_merge truthy False & skip_pseudo_alignment truthy False; dag: hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test

## P48: nf-core custom script (Python) -> dupRadar  (edges 2, tierA 1)
- E00805 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA.gtf -> NFCORE_RNASEQ:RNASEQ:BAM_QC_RNASEQ:DUPRADAR[in1] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("out/${prefix}.gtf") , emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:117; consumer decl: tuple val(meta2), path(gtf) @ subworkflows/nf-core/bam_qc_rnaseq/main.nf:68; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & fasta_provided truthy True & skip_qc truthy False & use_rustqc truthy False; dag: hisat2;hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;sentieon_star;star_rsem;test

## P49: nf-core custom script (Python) -> ea-utils gtf2bed  (edges 2, tierA 2)
- E00014 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_CATADDITIONALFASTA.gtf -> NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:EAUTILS_GTF2BED[in0] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("out/${prefix}.gtf") , emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:117; consumer decl: tuple val(meta), path(gtf) @ subworkflows/local/prepare_genome_references/main.nf:145; flags=['conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: additional_fasta truthy True & fasta_provided truthy True & gene_bed truthy False & prokaryotic truthy False; dag: hisat2;hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;star_rsem;test
- E00015 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_GTFFILTER.gtf -> NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:EAUTILS_GTF2BED[in0] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("${prefix}.${suffix}"), emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:97; consumer decl: tuple val(meta), path(gtf) @ subworkflows/local/prepare_genome_references/main.nf:145; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: filter_gtf_needed truthy True & gene_bed truthy False & prokaryotic truthy False; dag: kallisto

## P50: nf-core custom script (Python) -> kallisto  (edges 4, tierA 1)
- E01112 NFCORE_RNASEQ:PREPARE_GENOME_REFERENCES:CUSTOM_GTFFILTER.gtf -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:KALLISTO_QUANT[in1] class=direct conf=medium ops=first;map
  - producer decl: tuple val(meta), path("${prefix}.${suffix}"), emit: gtf @ subworkflows/local/prepare_genome_references/main.nf:97; consumer decl: tuple val(meta2), path(index), path(gtf), path(chromosomes) @ subworkflows/nf-core/quantify_pseudo_alignment/main.nf:38; flags=['closure-with-unused-param(weak)', 'conditional-consumer', 'alternative-branch-in-channel-path', 'conditional-producer']
  - assumes: filter_gtf_needed truthy True & pseudo_aligner ne salmon & pseudo_aligner truthy True & skip_pseudo_alignment truthy False; dag: kallisto

## P51: nf-core custom script (Python) -> tximeta  (edges 3, tierA 3)
- E00572 NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:CUSTOM_TX2GENE.tx2gene -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT[in1] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*tx2gene.tsv"), emit: tx2gene @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:43; consumer decl: tuple val(meta2), path(tx2gene) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner eq star_rsem; dag: star_rsem
- E00617 NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:CUSTOM_TX2GENE.tx2gene -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT[in1] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*tx2gene.tsv"), emit: tx2gene @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:43; consumer decl: tuple val(meta2), path(tx2gene) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner ne star_rsem; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E01123 NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:CUSTOM_TX2GENE.tx2gene -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT[in1] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*tx2gene.tsv"), emit: tx2gene @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:43; consumer decl: tuple val(meta2), path(tx2gene) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; flags=['conditional-consumer', 'conditional-producer']
  - assumes: pseudo_aligner truthy True & skip_pseudo_alignment truthy False; dag: hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test

## P52: tximeta -> DESeq2  (edges 3, tierA 3)
- E00583 NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.counts_gene_length_scaled -> NFCORE_RNASEQ:RNASEQ:DESEQ2_QC_RSEM[in0] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*gene_counts_length_scaled.tsv"), emit: counts_gene_length_scaled @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: path counts @ workflows/rnaseq/main.nf:439; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner eq star_rsem & skip_deseq2_qc truthy False & skip_qc truthy False & skip_quantification_merge truthy False; dag: star_rsem
- E00628 NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.counts_gene_length_scaled -> NFCORE_RNASEQ:RNASEQ:DESEQ2_QC_BAM_SALMON[in0] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*gene_counts_length_scaled.tsv"), emit: counts_gene_length_scaled @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: path counts @ workflows/rnaseq/main.nf:467; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner ne star_rsem & skip_deseq2_qc truthy False & skip_qc truthy False & skip_quantification_merge truthy False; dag: kraken2;kraken2_bracken;parabricks_star;sentieon_star;test
- E01134 NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.counts_gene_length_scaled -> NFCORE_RNASEQ:RNASEQ:DESEQ2_QC_PSEUDO[in0] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*gene_counts_length_scaled.tsv"), emit: counts_gene_length_scaled @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: path counts @ workflows/rnaseq/main.nf:797; flags=['conditional-consumer', 'conditional-producer']
  - assumes: pseudo_aligner truthy True & skip_deseq2_qc truthy False & skip_pseudo_alignment truthy False & skip_qc truthy False & skip_quantification_merge truthy False; dag: hisat2_kraken2_bracken;kraken2;kraken2_bracken;parabricks_star;sentieon_star;test

## P53: tximeta -> SummarizedExperiment  (edges 27, tierA 27)
- E00573 NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.counts_gene -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*gene_counts.tsv") , emit: counts_gene @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner eq star_rsem & skip_merge truthy False; dag: star_rsem
- E00574 NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.counts_gene_length_scaled -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*gene_counts_length_scaled.tsv"), emit: counts_gene_length_scaled @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner eq star_rsem & skip_merge truthy False; dag: star_rsem
- E00575 NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.counts_gene_scaled -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*gene_counts_scaled.tsv") , emit: counts_gene_scaled @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner eq star_rsem & skip_merge truthy False; dag: star_rsem
- E00576 NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.lengths_gene -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*gene_lengths.tsv") , emit: lengths_gene @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner eq star_rsem & skip_merge truthy False; dag: star_rsem
- E00577 NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.tpm_gene -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*gene_tpm.tsv") , emit: tpm_gene @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner eq star_rsem & skip_merge truthy False; dag: star_rsem
- E00579 NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.counts_transcript -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_TRANSCRIPT_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*transcript_counts.tsv") , emit: counts_transcript @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:104; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner eq star_rsem & skip_merge truthy False; dag: star_rsem
- E00580 NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.lengths_transcript -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_TRANSCRIPT_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*transcript_lengths.tsv") , emit: lengths_transcript @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:104; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner eq star_rsem & skip_merge truthy False; dag: star_rsem
- E00581 NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.tpm_transcript -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_TRANSCRIPT_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*transcript_tpm.tsv") , emit: tpm_transcript @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:104; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner eq star_rsem & skip_merge truthy False; dag: star_rsem
- E00582 NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.tx2gene_augmented -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_RSEM:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_TRANSCRIPT_UNIFIED[in1] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*tx2gene_augmented.tsv") , emit: tx2gene_augmented @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta2), path(rowdata) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:104; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner eq star_rsem & skip_merge truthy False; dag: star_rsem
- E00618 NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.counts_gene -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*gene_counts.tsv") , emit: counts_gene @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner ne star_rsem & skip_merge truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E00619 NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.counts_gene_length_scaled -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*gene_counts_length_scaled.tsv"), emit: counts_gene_length_scaled @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner ne star_rsem & skip_merge truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E00620 NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.counts_gene_scaled -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*gene_counts_scaled.tsv") , emit: counts_gene_scaled @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner ne star_rsem & skip_merge truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E00621 NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.lengths_gene -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*gene_lengths.tsv") , emit: lengths_gene @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner ne star_rsem & skip_merge truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E00622 NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.tpm_gene -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*gene_tpm.tsv") , emit: tpm_gene @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner ne star_rsem & skip_merge truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E00624 NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.counts_transcript -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_TRANSCRIPT_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*transcript_counts.tsv") , emit: counts_transcript @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:104; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner ne star_rsem & skip_merge truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E00625 NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.lengths_transcript -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_TRANSCRIPT_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*transcript_lengths.tsv") , emit: lengths_transcript @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:104; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner ne star_rsem & skip_merge truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E00626 NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.tpm_transcript -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_TRANSCRIPT_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*transcript_tpm.tsv") , emit: tpm_transcript @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:104; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner ne star_rsem & skip_merge truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E00627 NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.tx2gene_augmented -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_BAM_SALMON:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_TRANSCRIPT_UNIFIED[in1] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*tx2gene_augmented.tsv") , emit: tx2gene_augmented @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta2), path(rowdata) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:104; flags=['conditional-consumer', 'conditional-producer']
  - assumes: aligner ne star_rsem & skip_merge truthy False; dag: kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E01124 NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.counts_gene -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*gene_counts.tsv") , emit: counts_gene @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: pseudo_aligner truthy True & skip_merge truthy False & skip_pseudo_alignment truthy False; dag: hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E01125 NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.counts_gene_length_scaled -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*gene_counts_length_scaled.tsv"), emit: counts_gene_length_scaled @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: pseudo_aligner truthy True & skip_merge truthy False & skip_pseudo_alignment truthy False; dag: hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E01126 NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.counts_gene_scaled -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*gene_counts_scaled.tsv") , emit: counts_gene_scaled @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: pseudo_aligner truthy True & skip_merge truthy False & skip_pseudo_alignment truthy False; dag: hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E01127 NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.lengths_gene -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*gene_lengths.tsv") , emit: lengths_gene @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: pseudo_aligner truthy True & skip_merge truthy False & skip_pseudo_alignment truthy False; dag: hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E01128 NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.tpm_gene -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_GENE_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*gene_tpm.tsv") , emit: tpm_gene @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:90; flags=['conditional-consumer', 'conditional-producer']
  - assumes: pseudo_aligner truthy True & skip_merge truthy False & skip_pseudo_alignment truthy False; dag: hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E01130 NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.counts_transcript -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_TRANSCRIPT_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*transcript_counts.tsv") , emit: counts_transcript @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:104; flags=['conditional-consumer', 'conditional-producer']
  - assumes: pseudo_aligner truthy True & skip_merge truthy False & skip_pseudo_alignment truthy False; dag: hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E01131 NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.lengths_transcript -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_TRANSCRIPT_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*transcript_lengths.tsv") , emit: lengths_transcript @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:104; flags=['conditional-consumer', 'conditional-producer']
  - assumes: pseudo_aligner truthy True & skip_merge truthy False & skip_pseudo_alignment truthy False; dag: hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E01132 NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.tpm_transcript -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_TRANSCRIPT_UNIFIED[in0] class=merged-channel conf=medium ops=join;map;tail
  - producer decl: tuple val(meta), path("*transcript_tpm.tsv") , emit: tpm_transcript @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta), path(matrix_files) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:104; flags=['conditional-consumer', 'conditional-producer']
  - assumes: pseudo_aligner truthy True & skip_merge truthy False & skip_pseudo_alignment truthy False; dag: hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
- E01133 NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:TXIMETA_TXIMPORT.tx2gene_augmented -> NFCORE_RNASEQ:RNASEQ:QUANTIFY_PSEUDO_ALIGNMENT:QUANT_TXIMPORT_SUMMARIZEDEXPERIMENT:SE_TRANSCRIPT_UNIFIED[in1] class=direct conf=high ops=
  - producer decl: tuple val(meta), path("*tx2gene_augmented.tsv") , emit: tx2gene_augmented @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:67; consumer decl: tuple val(meta2), path(rowdata) @ subworkflows/nf-core/quant_tximport_summarizedexperiment/main.nf:104; flags=['conditional-consumer', 'conditional-producer']
  - assumes: pseudo_aligner truthy True & skip_merge truthy False & skip_pseudo_alignment truthy False; dag: hisat2_kraken2_bracken;kallisto;kraken2;kraken2_bracken;parabricks_star;salmon_pseudo;sentieon_star;test
