#!/usr/bin/env nextflow
include { MINI } from './workflows/mini'

workflow {
    ch_reads = channel.fromPath(params.input).map { f -> [ [id: f.baseName], f ] }
    MINI ( ch_reads, channel.value(file(params.index)), channel.value(file(params.gtf)) )
}
