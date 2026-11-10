process SAMTOOLS_SORT {
    input:
    tuple val(meta), path(bam)

    output:
    tuple val(meta), path("*.sorted.bam"), emit: bam

    script:
    """
    samtools sort -o ${meta.id}.sorted.bam $bam
    """
}
