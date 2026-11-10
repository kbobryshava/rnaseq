# Validation summary

Result: **PASS** (37 pass, 0 warn, 0 fail, 7 informational)

| id | check | status | detail |
|---|---|---|---|
| D1 | no duplicate ordered software pair in software_relationships_all | PASS |  |
| D2 | no duplicate process edge_id | PASS |  |
| D3 | no duplicate (source instance, emit, target instance, input slot) | PASS |  |
| D4 | every software pair appears in exactly one category file | PASS |  |
| D5 | category files add up to the combined table | PASS |  |
| C1 | no pair is both positive and negative/unresolved (independent source files) | PASS |  |
| C2 | consolidated sets equal the independent curated sets | PASS |  |
| C3 | no negative pair has a live (high/medium) process edge | PASS |  |
| C4 | every Gold/Silver pair has a source-verified positive supporting edge and no rejected supporting edge | PASS |  |
| C5 | no verified-positive process edge is rejected by the payload check | PASS |  |
| C6 | no source-verified-negative process edge also appears in a Gold/Silver pair | PASS |  |
| C7 | software pairs that are positive in both directions (allowed: the same software is used at different stages) | INFO | 3: RSEM <-> nf-core custom script (Python); Salmon <-> nf-core custom script (Python); kallisto <-> nf-core custom script (Python) |
| M1 | every process instance in an edge has a software mapping | PASS |  |
| M2 | mapped software keys exist in the canonical software table | PASS |  |
| M3 | edge src/dst software equals the process->software map | PASS |  |
| M4 | one module -> one software (no module is mapped to different software in different instances) | PASS |  |
| M5 | no multi-tool process mapped (software pairs would be ambiguous) | PASS |  |
| M6 | no process mapping is auto-derived/unreviewed | PASS |  |
| M7 | curated mapping differs from meta.yml tools (reviewed, curated value kept) | INFO | 12 modules, e.g. CUSTOM_GTFFILTER: meta.yml='gtffilter' -> nf-core custom script (Python); CUSTOM_RSEMMERGECOUNTS: meta.yml='custom' -> sed; RSEM_CALCULATEEXPRESSION: meta.yml='rseqc' -> RSEM; RSEM_PREPAREREFERENCE: meta.yml='rseqc' -> RSEM; RUSTQC: meta.yml='rustqc' -> RSeQC |
| M8 | every pair with process edges records the operation actually performed | PASS |  |
| M9 | RSEM -> kallisto is recorded as rsem-prepare-reference transcript extraction (not RSEM quantification) | PASS |  |
| M10 | software nodes standing for several different operations | INFO | SAMtools: 9; RSeQC: 9; nf-core custom script (Python): 4; HISAT2: 3; Sentieon RSEM: 3; RSEM: 3 (see src_operation / dst_operation; always join pairs back to process level) |
| R1 | process graph is acyclic (no process-level cycle) | PASS |  |
| R2 | no process edge from an instance to itself | PASS |  |
| R3 | source emit is a declared output of the producer and the input slot exists on the consumer | PASS |  |
| R4 | direction of each Gold/Silver supporting edge matches the pair (producer = source) | PASS |  |
| E1 | no positive edge has contradictory execution conditions | PASS |  |
| E2 | 'conditional' flag is consistent with recorded conditions | PASS |  |
| E3 | Gold/Silver pairs without hub-free preview-DAG confirmation (verified by source reading only) | INFO | 0 of 51:  |
| E4 | Gold/Silver pairs whose supporting edges carry no recorded conditions (always active) | INFO | 1: P36 |
| E5 | condition atoms of positives that are not --params (derived variables, documented in evidence text) | INFO | fasta_provided, filter_gtf_needed, markdups_done, skip_merge |
| P1 | all 5354 file:line references resolve to an existing file and a line inside it | PASS |  |
| P2 | 20 content anchors (the lines the key decisions rest on) contain the expected text | PASS |  |
| P3 | every positive/negative software record carries evidence text and (for process-backed records) a call-site line | PASS |  |
| P4 | every process record has producer_call, consumer_call and module file:line | PASS |  |
| A1 | audit confidence table covers exactly the canonical edge ids | PASS |  |
| A2 | audit payload verdicts equal the verdicts stored in the canonical build | PASS |  |
| A3 | audit summary counts equal reference counts | PASS |  |
| A4 | original (v1) confidence preserved: confidence_v1 equals the frozen original results for every edge | PASS |  |
| A5 | edge sets of canonical and original results are identical | PASS |  |
| A6 | process category counts add up | PASS |  |
| A7 | confidence_v1 -> confidence_final transitions | INFO | high->high: 47, low->low: 222, low->rejected: 2, medium->high: 335, medium->medium: 547, medium->rejected: 81 |
| F1 | record counts equal the frozen release | PASS |  |
| F2 | verified-negative software pairs include the two negatives from the 53 core pairs | PASS |  |

## Record counts

| table | category | n |
|---|---|---|
| software_relationships | Algorithmic_supported | 282 |
| software_relationships | Gold | 29 |
| software_relationships | Negative_unverified | 127 |
| software_relationships | Negative_verified | 19 |
| software_relationships | Silver | 22 |
| software_relationships | Unresolved | 37 |
| process_relationships | algorithmic_negative_candidate | 172 |
| process_relationships | algorithmic_supported | 814 |
| process_relationships | source_verified_negative | 5 |
| process_relationships | source_verified_positive | 115 |
| process_relationships | unresolved | 128 |
