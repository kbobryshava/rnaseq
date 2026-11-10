process HISAT2_ALIGN {
    input:
    tuple val(meta), path(reads)
    path index

    output:
    tuple val(meta), path("*.bam"), emit: bam

    script:
    """
    hisat2 -x $index -U $reads | samtools view -b > ${meta.id}.bam
    """
}
