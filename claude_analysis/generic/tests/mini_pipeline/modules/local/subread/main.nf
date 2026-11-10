process SUBREAD_COUNT {
    input:
    tuple val(meta), path(bam)
    path gtf

    output:
    tuple val(meta), path("*.counts.tsv"), emit: counts

    script:
    """
    featureCounts -a $gtf -o ${meta.id}.counts.tsv $bam
    """
}
