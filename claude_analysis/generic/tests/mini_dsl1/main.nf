// synthetic old-style (DSL1) pipeline for the self-test
Channel.fromPath(params.reads).set { raw_ch }
Channel.fromPath(params.ref).into { ref_align; ref_call }

process trim {
    input:
    file reads from raw_ch
    output:
    file "*.trimmed.fq" into trimmed_ch, trimmed_qc
    script:
    """
    fastp -i $reads -o out.trimmed.fq
    """
}

process align {
    input:
    file reads from trimmed_ch
    file ref from ref_align.collect()
    output:
    file "*.bam" into bam_ch
    script:
    """
    bwa mem $ref $reads | samtools view -b - > out.bam
    """
}

process qc {
    input:
    file reads from trimmed_qc
    output:
    file "*.html" into qc_ch
    script:
    """
    fastqc $reads
    """
}

bam_sorted = bam_ch.map { it }

process call {
    input:
    file bam from bam_sorted
    file ref from ref_call.collect()
    output:
    file "*.vcf" into vcf_ch
    script:
    """
    bcftools mpileup -f $ref $bam > out.vcf
    """
}

process report {
    input:
    file q from qc_ch.mix(vcf_ch).collect()
    script:
    """
    multiqc .
    """
}
