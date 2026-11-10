include { FASTP        } from '../modules/local/fastp/main'
include { HISAT2_ALIGN } from '../modules/local/hisat2/main'
include { SAMTOOLS_SORT } from '../modules/local/samtools/main'
include { SUBREAD_COUNT } from '../modules/local/subread/main'
include { QUALIMAP_QC  } from '../modules/local/qualimap/main'

workflow MINI {
    take:
    reads
    index
    gtf

    main:
    ch_fastq = reads
    if (!params.skip_trimming) {
        FASTP ( reads )
        ch_fastq = FASTP.out.reads
    }
    HISAT2_ALIGN ( ch_fastq, index )
    SAMTOOLS_SORT ( HISAT2_ALIGN.out.bam )
    SUBREAD_COUNT ( SAMTOOLS_SORT.out.bam, gtf )
    QUALIMAP_QC ( SAMTOOLS_SORT.out.bam )
}
