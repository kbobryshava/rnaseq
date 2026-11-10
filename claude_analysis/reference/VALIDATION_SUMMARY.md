# Validation summary

Result: **PASS** (42 pass, 0 warn, 0 fail, 7 informational)

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
| C7 | software pairs that are positive in both directions (allowed: the same software is used at different stages) | INFO | 16: Bowtie 2 <-> SAMtools; GffRead <-> nf-core custom script (Python); HISAT2 <-> SAMtools; NVIDIA Parabricks rna_fq2bam (STAR-based) <-> SAMtools; Picard <-> SAMtools; RSEM <-> SAMtools; RSEM <-> nf-core custom script (Python); SAMtools <-> STAR; SAMtools <-> Sentieon RSEM; SAMtools <-> Sentieon STAR; SAMtools <-> UMI-tools; SAMtools <-> UMICollapse; Salmon <-> nf-core custom script (Python); Sentieon RSEM <-> nf-core custom script (Python); featureCounts (Subread) <-> nf-core custom script (Python); kallisto <-> nf-core custom script (Python) |
| M1 | every process instance in an edge has a software mapping | PASS |  |
| M2 | mapped software keys exist in the canonical software table | PASS |  |
| M3 | edge src/dst software equals the process->software map | PASS |  |
| M4 | one module -> one software (no module is mapped to different software in different instances) | PASS |  |
| M5 | no multi-tool process mapped (software pairs would be ambiguous) | PASS |  |
| M6 | no process mapping is auto-derived/unreviewed | PASS |  |
| M7 | curated mapping differs from meta.yml tools (reviewed, curated value kept) | INFO | 11 modules, e.g. CUSTOM_GTFFILTER: meta.yml='gtffilter' -> nf-core custom script (Python); CUSTOM_RSEMMERGECOUNTS: meta.yml='custom' -> sed; RSEM_CALCULATEEXPRESSION: meta.yml='rseqc' -> RSEM; RSEM_PREPAREREFERENCE: meta.yml='rseqc' -> RSEM; SENTIEON_RSEMCALCULATEEXPRESSION: meta.yml='rseqc' -> Sentieon RSEM |
| M8 | every pair with process edges records the operation actually performed | PASS |  |
| M9 | RSEM -> kallisto is recorded as rsem-prepare-reference transcript extraction (not RSEM quantification) | PASS |  |
| M10 | software nodes standing for several different operations | INFO | SAMtools: 18; RSeQC: 8; STAR: 6; HISAT2: 5; UMI-tools: 5; nf-core custom script (Python): 4 (see src_operation / dst_operation; always join pairs back to process level) |
| R1 | process graph is acyclic (no process-level cycle) | PASS |  |
| R2 | no process edge from an instance to itself | PASS |  |
| R3 | source emit is a declared output of the producer and the input slot exists on the consumer | PASS |  |
| R4 | direction of each Gold/Silver supporting edge matches the pair (producer = source) | PASS |  |
| E1 | no positive edge has contradictory execution conditions | PASS |  |
| E2 | 'conditional' flag is consistent with recorded conditions | PASS |  |
| E3 | Gold/Silver pairs without hub-free preview-DAG confirmation (verified by source reading only) | INFO | 243 of 294: F001,F002,F003,F004,F005,F006,F007,F008,F009,F010,F011,F012,F013,F014,F015,F016,F017,F018,F019,F020,F021,F022,F023,F024,F035,F036,F037,F038,F039,F040,F041,F042,F043,F044,F045,F046,F047,F048,F049,F050,F052,F053,F054,F055,F056,F057,F058,F059,F060,F061,F062,F063,F064,F065,F066,F067,F068,F069,F070,F071,F072,F073,F074,F075,F076,F077,F078,F079,F080,F081,F082,F083,F084,F085,F086,F087,F088,F089,F090,F091,F092,F093,F094,F095,F096,F097,F098,F099,F100,F101,F102,F103,F104,F107,F108,F109,F110,F111,F112,F113,F114,F115,F116,F117,F118,F119,F120,F121,F122,F123,F124,F125,F126,F127,F128,F129,F130,F131,F132,F133,F134,F135,F136,F137,F138,F139,F140,F141,F142,F143,F144,F145,F146,F147,F148,F149,F150,F151,F152,F153,F154,F155,F156,F157,F158,F159,F160,F161,F162,F163,F164,F165,F166,F167,F168,F169,F170,F171,F172,F191,F192,F193,F194,F195,F196,F197,F198,F199,F200,F201,F202,F203,F204,F205,F025,F026,F027,F028,F029,F030,F031,F032,F033,F034,F051,F105,F106,F173,F174,F175,F176,F177,F178,F179,F180,F181,F182,F183,F184,F185,F186,F187,F188,F189,F190,F206,F207,F208,F209,F210,F211,F212,F213,F214,F215,F216,F217,F218,F219,F220,F221,F222,F223,F224,F225,F226,F227,F228,F229,F230,F231,F232,F233,F234,F235,F236,F237,F238,F239,F240,F241,F242,F243 |
| E4 | Gold/Silver pairs whose supporting edges carry no recorded conditions (always active) | INFO | 1: P36 |
| E5 | condition atoms of positives that are not --params (derived variables, documented in evidence text) | INFO | ch_transcript_fasta, fasta_provided, filter_gtf_needed, make_bowtie2_index, make_index, make_sortmerna_index, markdups_done, skip_merge, val_primary_only |
| P1 | all 5756 file:line references resolve to an existing file and a line inside it | PASS |  |
| P2 | 20 content anchors (the lines the key decisions rest on) contain the expected text | PASS |  |
| P3 | every positive/negative software record carries evidence text and (for process-backed records) a call-site line | PASS |  |
| P4 | every process record has producer_call, consumer_call and module file:line | PASS |  |
| A1 | audit confidence table covers exactly the canonical edge ids | PASS |  |
| A2 | audit payload verdicts equal the verdicts stored in the canonical build | PASS |  |
| A3 | audit decision files (53 core + family rules) equal reference counts | PASS |  |
| A4 | original (v1) confidence preserved: confidence_v1 equals the frozen original results for every edge | PASS |  |
| A5 | edge sets of canonical and original results are identical | PASS |  |
| A6 | process category counts add up | PASS |  |
| A7 | confidence_v1 -> confidence_final transitions | INFO | high->high: 47, low->low: 222, low->rejected: 2, medium->high: 702, medium->medium: 180, medium->rejected: 81 |
| V1 | every edge behind a family-rule Gold/Silver pair still satisfies the family rule (live edge, stage order) | PASS |  |
| V2 | every positive pair states its verification level (pair or family-rule) | PASS |  |
| V3 | no weak-identity (tar/gzip/cat/sed/gawk/custom script) pair is Gold | PASS |  |
| V4 | RustQC is its own software node (not RSeQC) | PASS |  |
| V5 | Salmon roles are distinguished (strandedness inference vs quantification) in the operation columns | PASS |  |
| F1 | record counts equal the frozen release | PASS |  |
| F2 | verified-negative software pairs include the two negatives from the 53 core pairs | PASS |  |

## Record counts

| table | category | n |
|---|---|---|
| software_relationships | Algorithmic_supported | 46 |
| software_relationships | Dependency_gate_metadata | 41 |
| software_relationships | Gold | 203 |
| software_relationships | Negative_unverified | 229 |
| software_relationships | Negative_verified | 56 |
| software_relationships | Silver | 91 |
| process_relationships | algorithmic_negative_candidate | 172 |
| process_relationships | algorithmic_supported | 244 |
| process_relationships | functional_dependency_non_data | 128 |
| process_relationships | source_verified_negative | 5 |
| process_relationships | source_verified_positive | 685 |
