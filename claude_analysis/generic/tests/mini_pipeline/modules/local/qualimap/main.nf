process QUALIMAP_QC {
    input:
    tuple val(meta), path(bam)

    output:
    tuple val(meta), path("qualimap"), emit: results

    script:
    """
    qualimap bamqc -bam $bam -outdir qualimap
    """
}
