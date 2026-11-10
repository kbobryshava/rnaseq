process FASTP {
    input:
    tuple val(meta), path(reads)

    output:
    tuple val(meta), path("*.trim.fastq.gz"), emit: reads
    tuple val(meta), path("*.json"), emit: json

    script:
    """
    fastp -i $reads -o ${meta.id}.trim.fastq.gz --json ${meta.id}.json
    """
}
