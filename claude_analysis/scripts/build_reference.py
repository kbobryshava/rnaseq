#!/usr/bin/env python3
"""Consolidate the extraction and the audit into the frozen reference dataset  claude_analysis/reference/  (process level and software level kept apart).

Inputs (all produced by earlier stages): data/processed/*, audit/*, audit/curated/*.   Nothing outside reference/ is written.
Output CSVs use '\n' line endings and are sorted, so a clean rebuild is byte-identical.
"""
import csv, json, os, re, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
P = os.path.join(ROOT, 'data', 'processed'); A = os.path.join(ROOT, 'audit'); C = os.path.join(A, 'curated')
R = os.path.join(ROOT, 'reference'); RP = os.path.join(R, 'process_level'); RS = os.path.join(R, 'software_level')
for d in (RP, RS): os.makedirs(d, exist_ok=True)


def rd(path): return list(csv.DictReader(open(path, encoding='utf-8', newline='')))
def wr(path, rows, cols):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore', lineterminator='\n'); w.writeheader(); w.writerows(rows)
    return len(rows)


# ---------------------------------------------------------------- operation performed (software identity != operation)
OPERATION = {   # by process (call) name first, then by module; default = module name with the first '_' as a space
    'MAKE_TRANSCRIPTS_FASTA': 'rsem-prepare-reference used only to extract the transcriptome FASTA (no RSEM quantification)',
    'SENTIEON_MAKE_TRANSCRIPTS_FASTA': 'Sentieon rsem-prepare-reference used only to extract the transcriptome FASTA',
    'RSEM_PREPAREREFERENCE_GENOME': 'rsem-prepare-reference (RSEM index build)',
    'SENTIEON_RSEM_PREPAREREFERENCE_GENOME': 'Sentieon rsem-prepare-reference (RSEM index build)',
    'RSEM_CALCULATEEXPRESSION': 'rsem-calculate-expression (quantification)',
    'STAR_GENOMEGENERATE': 'STAR --runMode genomeGenerate (index build)',
    'PARABRICKS_STARGENOMEGENERATE': 'STAR --runMode genomeGenerate with the STAR 2.7.2a build used by Parabricks',
    'STAR_ALIGN': 'STAR --runMode alignReads', 'SENTIEON_STAR_ALIGN': 'Sentieon STAR alignment', 'PARABRICKS_RNA_FQ2BAM': 'Parabricks rna_fq2bam (STAR-based alignment, optional mark-duplicates)',
    'SAMTOOLS_SORT': 'samtools sort', 'SAMTOOLS_SORT_QUALIMAP': 'samtools sort -n (name sort for Qualimap)', 'SAMTOOLS_INDEX': 'samtools index', 'SAMTOOLS_FAIDX': 'samtools faidx (also writes chrom.sizes)',
    'SAMTOOLS_STATS': 'samtools stats', 'SAMTOOLS_FLAGSTAT': 'samtools flagstat', 'SAMTOOLS_IDXSTATS': 'samtools idxstats', 'SAMTOOLS_VIEW': 'samtools view', 'SAMTOOLS_FASTQ': 'samtools fastq',
    'KALLISTO_INDEX': 'kallisto index', 'KALLISTO_QUANT': 'kallisto quant', 'SALMON_INDEX': 'salmon index', 'SALMON_QUANT': 'salmon quant (mapping- or alignment-based)',
    'FQ_SUBSAMPLE': 'fq subsample', 'FQ_LINT': 'fq lint', 'FQ_LINT_AFTER_TRIMMING': 'fq lint', 'FQ_LINT_AFTER_BBSPLIT': 'fq lint', 'FQ_LINT_AFTER_RIBO_REMOVAL': 'fq lint',
    'CUSTOM_GTFFILTER': 'local Python script: GTF filtering', 'CUSTOM_CATADDITIONALFASTA': 'local Python script: append additional FASTA/GTF', 'CUSTOM_TX2GENE': 'local Python script: transcript-to-gene table',
    'CUSTOM_RSEMMERGECOUNTS': 'local shell script (cut/paste/sed): merge RSEM results', 'CUSTOM_MULTIQCCUSTOMBIOTYPE': 'local Python script: biotype table for MultiQC',
    'EAUTILS_GTF2BED': 'ea-utils gtf2bed', 'TXIMETA_TXIMPORT': 'tximport (via tximeta module)', 'SUMMARIZEDEXPERIMENT_SUMMARIZEDEXPERIMENT': 'R SummarizedExperiment construction',
    'DESEQ2_QC': 'DESeq2 QC (local R script)', 'UNTAR': 'tar extraction', 'GUNZIP': 'gunzip', 'CAT_FASTQ': 'cat (FASTQ concatenation)'}


def operation(instance, module):
    leaf = instance.split(':')[-1]
    if leaf in OPERATION: return OPERATION[leaf]
    if re.match(r'UNTAR_', leaf): return 'tar extraction'
    if re.match(r'GUNZIP_', leaf): return 'gunzip'
    if module in OPERATION: return OPERATION[module]
    return module.lower().replace('_', ' ', 1)


def short(i): return i.split(':')[-1]


edges = rd(os.path.join(P, 'process_edges.csv')); EV = {}
for l in open(os.path.join(P, 'process_edges_evidence.jsonl'), encoding='utf-8'): r = json.loads(l); EV[r['edge_id']] = r
FIN = {r['edge_id']: r for r in rd(os.path.join(A, 'process_edges_final_confidence.csv'))}
SWM = {r['process_instance']: r for r in rd(os.path.join(P, 'process_software_map.csv'))}
DEC = rd(os.path.join(C, 'all_core_pair_decisions.csv'))
NEG = rd(os.path.join(C, 'negative_controls.csv')); UNR = rd(os.path.join(C, 'unresolved.csv'))
SWE = rd(os.path.join(P, 'software_edges.csv'))
CORE_OF = {}
for d in DEC:
    for eid in d['supporting_process_edges'].split(';'):
        if eid: CORE_OF[eid] = d['pair_id']
PAIR_DEC = {d['pair_id']: d['decision'] for d in DEC}

# ---------------------------------------------------------------- process level
prow = []
for e in edges:
    f = FIN[e['edge_id']]; ev = EV[e['edge_id']]; cls = e['edge_class']; fin = f['confidence_final']; mv = f['manual_verification']
    if mv == 'verified_positive': cat, sub, basis = 'source_verified_positive', 'gold_or_silver_supporting_edge', 'call site and input slot read in source (audit/curated/all_core_pair_decisions.csv)'
    elif mv == 'verified_negative': cat, sub, basis = 'source_verified_negative', 'artifact_or_infeasible', f['final_reason']
    elif fin == 'rejected': cat, sub, basis = 'algorithmic_negative_candidate', 'payload_check_rejected', e['payload_check'] + ': ' + e['payload_check_detail']
    elif cls == 'key-only-synchronization': cat, sub, basis = 'algorithmic_negative_candidate', 'key_only_synchronisation', 'channel reduced to the sample key (.map { meta, _x -> meta }); payload not consumed'
    elif cls in ('gating-or-metadata', 'metadata-dependency'): cat, sub, basis = 'unresolved', 'gate_or_metadata', 'output used as a gate or travels in meta; whether this counts as data is a definition choice'
    else: cat, sub, basis = 'algorithmic_supported', 'reporting_aggregation' if cls == 'reporting-aggregation' else 'static_channel_provenance', 'static analysis' + (' + hub-free preview DAG' if e['evidence_tier'].startswith('A') else '')
    sm, dm = SWM[e['src_instance']], SWM[e['dst_instance']]
    prow.append({
        'edge_id': e['edge_id'], 'validation_category': cat, 'validation_subtype': sub, 'validation_basis': basis, 'pair_id': CORE_OF.get(e['edge_id'], ''),
        'src_instance': e['src_instance'], 'src_process': short(e['src_instance']), 'src_module': e['src_module'], 'src_emit': e['src_emit'],
        'dst_instance': e['dst_instance'], 'dst_process': short(e['dst_instance']), 'dst_module': e['dst_module'], 'dst_input_index': e['dst_input_index'],
        'src_software': sm['primary_software'], 'dst_software': dm['primary_software'],
        'src_operation': operation(e['src_instance'], e['src_module']), 'dst_operation': operation(e['dst_instance'], e['dst_module']),
        'edge_class': cls, 'evidence_tier': e['evidence_tier'], 'confidence_v1': e['confidence_v1'], 'confidence_v2_rule': e['confidence_v2'], 'confidence_final': fin,
        'payload_check': e['payload_check'], 'required_params': e['required_param_assumptions'], 'conditional': e['conditional'],
        'producer_call': e['producer_call'], 'consumer_call': e['consumer_call'], 'src_module_file': ev['src_module_file'], 'dst_module_file': ev['dst_module_file'],
        'src_output_decl': ev['src_output_decl'], 'dst_input_decl': ev['dst_input_decl'], 'operators': e['operators'],
        'hubfree_dag_configs': e['confirmed_by_hubfree_dag_in'], 'configs_with_both_endpoints': e['both_endpoints_in_configs'],
        'in_default_test_profile': 'test' in e['both_endpoints_in_configs'].split(';')})
prow.sort(key=lambda r: r['edge_id'])
PCOLS = list(prow[0].keys())
n_all = wr(os.path.join(RP, 'process_relationships_all.csv'), prow, PCOLS)
cnt_p = collections.Counter(r['validation_category'] for r in prow)
for cat, fn in (('source_verified_positive', 'process_source_verified_positive.csv'), ('source_verified_negative', 'process_source_verified_negative.csv'),
                ('algorithmic_supported', 'process_algorithmic_supported.csv'), ('algorithmic_negative_candidate', 'process_algorithmic_negative_candidates.csv'), ('unresolved', 'process_unresolved.csv')):
    wr(os.path.join(RP, fn), [r for r in prow if r['validation_category'] == cat], PCOLS)

# ---------------------------------------------------------------- software level
by_pair = collections.defaultdict(list)
for r in prow: by_pair[(r['src_software'], r['dst_software'])].append(r)


def agg(rows):
    return {'n_process_edges': len(rows), 'process_edge_ids': ';'.join(r['edge_id'] for r in rows),
            'source_processes': ';'.join(sorted({r['src_process'] for r in rows})), 'target_processes': ';'.join(sorted({r['dst_process'] for r in rows})),
            'source_operations': ' | '.join(sorted({r['src_operation'] for r in rows})), 'target_operations': ' | '.join(sorted({r['dst_operation'] for r in rows})),
            'hubfree_dag_configs': ';'.join(sorted({c for r in rows for c in r['hubfree_dag_configs'].split(';') if c})),
            'in_default_test_profile': any(r['in_default_test_profile'] for r in rows)}


srows, used = [], set()
def add(src, dst, category, vcat, sub, conf, basis, expl, rows, pair_id='', flow='', ident=''):
    d = {'source_software': src, 'target_software': dst, 'category': category, 'validation_category': vcat, 'validation_subtype': sub, 'decision_confidence': conf,
         'pair_id': pair_id, 'flow_type': flow, 'identity_flag': ident, 'evidence_basis': basis, 'explanation': expl, 'is_self_loop': src == dst,
         'only_reporting': bool(rows) and all(r['edge_class'] == 'reporting-aggregation' for r in rows)}
    d.update(agg(rows)); srows.append(d); used.add((src, dst))


for d in DEC:
    if d['decision'] not in ('Gold', 'Silver'): continue
    ids = set(d['supporting_process_edges'].split(';')); rows = [r for r in prow if r['edge_id'] in ids]
    ev = EV[sorted(ids)[0]]
    add(d['source_software'], d['target_software'], d['decision'], 'source_verified_positive', d['flow_type'], d['decision_confidence'], d['source_lines_read_by_auditor'], d['explanation'], rows, d['pair_id'], d['flow_type'], d['identity_flag'])
    srows[-1]['required_params'] = d['conditions_required']
for n in NEG:
    key = (n['source_software'], n['target_software']); rows = [r for r in by_pair.get(key, [])]
    ver = n['verification'].startswith('manual')
    pid = next((d['pair_id'] for d in DEC if (d['source_software'], d['target_software']) == key and d['decision'] == 'Negative'), '')
    add(key[0], key[1], 'Negative_verified' if ver else 'Negative_unverified', 'source_verified_negative' if ver else 'algorithmic_negative_candidate', n['negative_kind'], n['decision_confidence'],
        n['verification'] + ' || ' + n['evidence'], n['direction_tested'], rows, pid)
for u in UNR:
    key = (u['source_software'], u['target_software']); rows = by_pair.get(key, [])
    add(key[0], key[1], 'Unresolved', 'unresolved', u['negative_kind'], u['decision_confidence'], u['verification'] + ' || ' + u['evidence'], 'gate/metadata-only dependency; definition-dependent', rows)
# remaining extracted software pairs: algorithmic
leftover = collections.Counter()
for key in sorted(by_pair):
    if key in used: continue
    rows = by_pair[key]; live = [r for r in rows if r['confidence_final'] in ('high', 'medium')]
    if key[0] == key[1] and not live: continue
    if live:
        add(key[0], key[1], 'Algorithmic_supported', 'algorithmic_supported', 'self_loop' if key[0] == key[1] else 'static_channel_provenance', 'medium' if all(r['confidence_final'] == 'medium' for r in live) else 'high',
            'static analysis' + ('; hub-free preview DAG' if any(r['evidence_tier'].startswith('A') for r in live) else ''), 'not individually adjudicated', live)
    else:
        kinds = {r['validation_category'] for r in rows}
        leftover[tuple(sorted(kinds))] += 1
        add(key[0], key[1], 'Unclassified_no_live_edge', 'unresolved' if 'unresolved' in kinds else 'algorithmic_negative_candidate', 'only_rejected_gate_or_sync_edges', 'low',
            'every extracted edge is rejected, key-only or gate/metadata; pair involves a utility/reporting node excluded from the curated negative sets', 'not adjudicated', rows)
srows.sort(key=lambda r: (r['category'], r['source_software'], r['target_software']))
for i, r in enumerate(srows, 1): r['software_pair_id'] = f'SW{i:04d}'
SCOLS = ['software_pair_id', 'source_software', 'target_software', 'category', 'validation_category', 'validation_subtype', 'decision_confidence', 'pair_id', 'flow_type', 'identity_flag',
         'is_self_loop', 'only_reporting', 'n_process_edges', 'process_edge_ids', 'source_processes', 'target_processes', 'source_operations', 'target_operations', 'required_params',
         'hubfree_dag_configs', 'in_default_test_profile', 'evidence_basis', 'explanation']
for r in srows: r.setdefault('required_params', '')
wr(os.path.join(RS, 'software_relationships_all.csv'), srows, SCOLS)
for cat, fn in (('Gold', 'gold_positive_controls.csv'), ('Silver', 'silver_positive_controls.csv'), ('Negative_verified', 'negative_controls_verified.csv'), ('Negative_unverified', 'negative_candidates_unverified.csv'),
                ('Unresolved', 'unresolved_gate_metadata.csv'), ('Algorithmic_supported', 'algorithmic_supported_pairs.csv'), ('Unclassified_no_live_edge', 'unclassified_pairs.csv')):
    rows_ = [r for r in srows if r['category'] == cat]
    if rows_ or cat != 'Unclassified_no_live_edge': wr(os.path.join(RS, fn), rows_, SCOLS)
cnt_s = collections.Counter(r['category'] for r in srows)

# optional parquet copies (convenience only; CSV is canonical)
try:
    import pandas as pd
    pd.read_csv(os.path.join(RP, 'process_relationships_all.csv'), dtype=str, keep_default_na=False).to_parquet(os.path.join(RP, 'process_relationships_all.parquet'), index=False)
    pd.read_csv(os.path.join(RS, 'software_relationships_all.csv'), dtype=str, keep_default_na=False).to_parquet(os.path.join(RS, 'software_relationships_all.parquet'), index=False)
    parquet = True
except Exception as ex:
    parquet = False; print('parquet skipped:', ex)
json.dump({'process_level': dict(sorted(cnt_p.items())), 'software_level': dict(sorted(cnt_s.items())), 'process_total': n_all, 'software_total': len(srows),
           'unclassified_breakdown': {'+'.join(k): v for k, v in leftover.items()}, 'parquet_written': parquet}, open(os.path.join(R, '_build_counts.json'), 'w'), indent=1, sort_keys=True)
print(json.dumps({'process': dict(cnt_p), 'software': dict(cnt_s), 'unclassified': {'+'.join(k): v for k, v in leftover.items()}}, indent=1))
