#!/usr/bin/env python3
"""Build the audit outputs (all new files under claude_analysis/audit/; nothing in data/processed is modified).

  audit/process_edges_v2.csv                 every process edge with the ORIGINAL confidence and the corrected one
  audit/reconciliation_high_vs_tierA.{md,csv}
  audit/curated/all_core_pair_decisions.csv  the 53 core pairs, one decision each (Gold/Silver/Negative/Unresolved)
  audit/curated/positive_controls.csv        Gold + Silver
  audit/curated/negative_controls.csv        Negative decisions from the 53 + computed/verified negatives
  audit/curated/unresolved.csv
  audit/summary.json
Run after: nf_static_analyzer.py, build_datasets.py, audit_dossier.py, audit_merged.py.
"""
import csv, json, os, re, sys, collections, itertools
import networkx as nx
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from audit_decisions import D
from nf_static_analyzer import infeasible
P = os.path.join(ROOT, 'data', 'processed'); A = os.path.join(ROOT, 'audit'); C = os.path.join(A, 'curated'); os.makedirs(C, exist_ok=True)


def rd(path): return list(csv.DictReader(open(path, encoding='utf-8')))
def wr(path, rows, cols=None):
    cols = cols or list(rows[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader(); w.writerows(rows)


edges = rd(os.path.join(P, 'process_edges.csv')); E = {e['edge_id']: e for e in edges}
EV = {}
for l in open(os.path.join(P, 'process_edges_evidence.jsonl'), encoding='utf-8'):
    r = json.loads(l); EV[r['edge_id']] = r
MA = {r['edge_id']: r for r in rd(os.path.join(A, 'payload_audit.csv'))}   # direct + merged edges
CORE = rd(os.path.join(A, 'core_pair_edges.csv'))
SW = {r['process_instance']: r for r in rd(os.path.join(P, 'process_software_map.csv'))}
CANON = {r['canonical_name']: r for r in rd(os.path.join(P, 'canonical_software.csv'))}
KEY2NAME = {r['key']: r['canonical_name'] for r in rd(os.path.join(P, 'canonical_software.csv'))}
EXEC = rd(os.path.join(P, 'executed_matrix.csv')); CONFIGS = [c for c in EXEC[0] if c != 'instance']
INST = {i['path']: i for i in json.load(open(os.path.join(P, 'static_graph.json')))['instances']}
WEAK = {'untar', 'gunzip', 'cat', 'sed', 'gawk', 'local_python'}      # generic OS utilities / local scripts: identity too weak for Gold
REJECT_VERDICTS = {'PROJECTION-DROPPED', 'MULTIMAP-SPLIT', 'INFEASIBLE-CALLSITE-CONSTANT'}
STAGING = re.compile(r"endsWith\(|kraken_db|_index\b|fasta_provided|_provided|\.tar\.gz|contaminant_screening && ")

# ------------------------------------------------------------------ pair decisions
pairs = collections.OrderedDict()
for r in CORE: pairs.setdefault(r['pair_id'], {'src': r['src_software'], 'dst': r['dst_software'], 'rows': []})['rows'].append(r)
assert len(pairs) == 53
dec_rows, verified_ok, verified_bad = [], set(), set()
for d in D:
    pid = d['pid']; pr = pairs[pid]
    tierA = [EV[x['edge_id']] for x in pr['rows'] if x['evidence_tier'].startswith('A')]
    filt = d['edge_filter']
    sup = [e for e in tierA if (filt(e) if filt else True)]
    allp = [EV[x['edge_id']] for x in pr['rows']]
    if d['decision'] in ('Gold', 'Silver'): verified_ok |= {e['edge_id'] for e in sup}
    if d['decision'] == 'Negative': verified_bad |= {e['edge_id'] for e in allp}
    rel, seen = [], set()
    for e in sup:
        k = f"{e['src_module']}.{e['src_emit']} -> {e['dst_module']}[{e['dst_input_index']}]"
        if k not in seen: seen.add(k); rel.append(k)
    first = sup[0] if sup else allp[0]
    lines = sorted({e['producer_call'] for e in sup} | {e['consumer_call'] for e in sup})
    configs = sorted({c for e in sup for c in (e['confirmed_by_hubfree_dag_in'] or '').split(';') if c})
    dec_rows.append({
        'pair_id': pid, 'source_software': pr['src'], 'target_software': pr['dst'], 'decision': d['decision'], 'decision_confidence': d['decision_confidence'],
        'flow_type': d['flow_type'],
        'identity_flag': 'weak-identity (utility / local script)' if (set(SW[first['src_instance']]['primary_software_keys'].split(';')) | set(SW[first['dst_instance']]['primary_software_keys'].split(';'))) & WEAK else '',
        'supporting_process_edges': ';'.join(e['edge_id'] for e in sup[:10]) + (f' (+{len(sup)-10} more)' if len(sup) > 10 else ''),
        'n_supporting_process_edges': len(sup), 'n_edges_of_pair_total': len(allp), 'n_edges_of_pair_tierA': len(tierA),
        'process_relationship': ' | '.join(rel[:5]) + (f' (+{len(rel)-5} more)' if len(rel) > 5 else ''),
        'io_evidence': f"producer output: {first['src_output_decl']} => consumer input: {first['dst_input_decl']}",
        'source_lines_extractor': ';'.join(lines[:8]), 'source_lines_read_by_auditor': d['evidence'],
        'conditions_required': first['required_param_assumptions'], 'hubfree_dag_configs': ';'.join(configs),
        'original_edge_class': ';'.join(sorted({e['edge_class'] for e in sup} or {first['edge_class']})),
        'original_confidence': ';'.join(sorted({e['confidence'] for e in sup} or {first['confidence']})),
        'explanation': d['explanation']})
wr(os.path.join(C, 'all_core_pair_decisions.csv'), dec_rows)
wr(os.path.join(C, 'positive_controls.csv'), [r for r in dec_rows if r['decision'] in ('Gold', 'Silver')])

# ------------------------------------------------------------------ corrected confidence (v2) for every edge
EXTRA_REJECT = {'E00353': 'infeasible: plain STAR_GENOMEGENERATE runs only when use_parabricks_star is false (subworkflows/local/prepare_genome_indices/main.nf:149 if-branch precedes :168), the Parabricks consumer needs it true'}
rows_v2 = []
for e in edges:
    eid = e['edge_id']; ev = EV[eid]; v = MA.get(eid, {}).get('family_verdict', '')
    flags = ev['flags']; alt = 'alternative-branch-in-channel-path' in flags
    branches = [t['var'] for t in ev['channel_trail'] if t['var'].startswith('branch:')]
    staging_alt = alt and branches and all(STAGING.search(b) for b in branches)
    cls = e['edge_class']
    if v in REJECT_VERDICTS: c2, why = 'rejected', f'merged-channel audit: {v}'
    elif eid in EXTRA_REJECT: c2, why = 'rejected', EXTRA_REJECT[eid]
    elif 'use_parabricks_star truthy True' in e['required_param_assumptions'] and 'use_sentieon_star truthy True' in e['required_param_assumptions']:
        c2, why = 'rejected', 'pipeline validation forbids --use_parabricks_star together with --use_sentieon_star (subworkflows/local/utils_nfcore_rnaseq_pipeline/main.nf:323-325)'
    elif eid in verified_bad: c2, why = 'rejected', 'audit decision Negative (see curated/all_core_pair_decisions.csv)'
    elif eid in verified_ok: c2, why = 'high', 'payload and consumer slot read in source (audit decision Gold/Silver)'
    elif cls in ('key-only-synchronization', 'metadata-dependency', 'gating-or-metadata'): c2, why = 'low', 'no payload is consumed (sync/gate/metadata)'
    elif cls == 'direct': c2, why = 'high', 'direct single-source path' + ('; channel is assigned on alternative if/else branches, which are mutually exclusive and recorded in required_param_assumptions (v1 wrongly demoted these)' if alt else '')
    elif cls == 'merged-channel': c2, why = 'medium', 'merged channel; family check: ' + (v or 'n/a')
    else: c2, why = 'medium', cls
    rows_v2.append({'edge_id': eid, 'src_instance': e['src_instance'], 'src_emit': e['src_emit'], 'dst_instance': e['dst_instance'], 'dst_input_index': e['dst_input_index'],
                    'edge_class': cls, 'evidence_tier': e['evidence_tier'], 'confidence_v1': e['confidence'], 'confidence_v2': c2, 'v2_reason': why,
                    'merged_audit_verdict': v, 'merged_audit_detail': MA.get(eid, {}).get('verdict_reason', '')})
wr(os.path.join(A, 'process_edges_v2.csv'), rows_v2)
V1 = {r['edge_id']: r['confidence_v1'] for r in rows_v2}; V2 = {r['edge_id']: r['confidence_v2'] for r in rows_v2}
changed = [r for r in rows_v2 if r['confidence_v1'] != r['confidence_v2']]
trans = collections.Counter((r['confidence_v1'], r['confidence_v2']) for r in rows_v2)

# ------------------------------------------------------------------ reconciliation high (47) vs tier A (174)
hi = {e['edge_id'] for e in edges if e['confidence'] == 'high'}; ta = {e['edge_id'] for e in edges if e['evidence_tier'].startswith('A')}
both, hi_only, ta_only = hi & ta, hi - ta, ta - hi
rec = []
for eid in sorted(hi | ta):
    e = E[eid]; ev = EV[eid]
    if eid in both: where = 'high & tierA'
    elif eid in hi_only: where = 'high only'
    else: where = 'tierA only'
    if where == 'high only': why = 'no preview DAG contains both endpoints' if not e['both_endpoints_in_configs'] else 'both endpoints in a preview DAG but the pair is not reachable without a fused operator node (hub)'
    elif where == 'tierA only':
        alt = 'alternative-branch-in-channel-path' in ev['flags']
        why = f"class={e['edge_class']}" + ('; alternative-branch flag (rule demoted it)' if alt and e['edge_class'] == 'direct' else '')
    else: why = ''
    rec.append({'edge_id': eid, 'bucket': where, 'edge_class': e['edge_class'], 'confidence_v1': e['confidence'], 'confidence_v2': V2[eid], 'src': f"{e['src_module']}.{e['src_emit']}", 'dst': e['dst_module'], 'reason': why})
wr(os.path.join(A, 'reconciliation_high_vs_tierA.csv'), rec)
ta_only_breakdown = collections.Counter(r['reason'] for r in rec if r['bucket'] == 'tierA only')
hi_only_breakdown = collections.Counter(r['reason'] for r in rec if r['bucket'] == 'high only')

# ------------------------------------------------------------------ computed negative controls
G = nx.DiGraph(); G.add_nodes_from(i for i, v in INST.items() if v['kind'] == 'process')
for e in edges: G.add_edge(e['src_instance'], e['dst_instance'])      # ALL extracted edges (incl. low/rejected): conservative "no path" test
desc = {n: nx.descendants(G, n) for n in G}
keys_of = lambda inst: [k for k in SW[inst]['primary_software_keys'].split(';') if k]
members = collections.defaultdict(set)
for inst in G:
    for k in keys_of(inst): members[k].add(inst)
execd = {r['instance']: {c for c in CONFIGS if r[c] == '1'} for r in EXEC}
EXCLUDE = WEAK | {'multiqc'}
cand = sorted(k for k in members if k not in EXCLUDE)
ALT_OF = {r['key']: r['alternative_of'] for r in rd(os.path.join(P, 'canonical_software.csv'))}
data_edges = [e for e in edges if e['edge_class'] in ('direct', 'merged-channel', 'reporting-aggregation') and V2[e['edge_id']] != 'rejected']   # rejected edges are not evidence of input sharing
preds = collections.defaultdict(lambda: collections.defaultdict(list))   # consumer instance -> (producer, emit) -> edge ids
for e in data_edges: preds[e['dst_instance']][(e['src_instance'], e['src_emit'])].append(e['edge_id'])
neg = []
for a, b in itertools.combinations(cand, 2):
    if ALT_OF.get(a) == KEY2NAME.get(b) or ALT_OF.get(b) == KEY2NAME.get(a): continue   # an alternative implementation of the same tool
    A_, B_ = members[a], members[b]
    if any(y in desc[x] or x in desc[y] for x in A_ for y in B_): continue            # some path exists: not a negative
    co = sorted({c for x in A_ for y in B_ for c in (execd.get(x, set()) & execd.get(y, set()))})
    shared = None
    for x in A_:
        for y in B_:
            common = set(preds[x]) & set(preds[y])
            if common and (execd.get(x, set()) & execd.get(y, set())):
                p = sorted(common)[0]; shared = (x, y, p, preds[x][p][0], preds[y][p][0]); break
        if shared: break
    row = {'source_software': KEY2NAME[a], 'target_software': KEY2NAME[b], 'direction_tested': 'both (no directed path either way in the extracted process graph)'}
    if shared and co:
        x, y, p, e1, e2 = shared
        row.update(negative_kind='shared-input', coexecuted_in_previews=';'.join(co),
                   evidence=f"both consume {p[0].split(':')[-1]}.{p[1]} : {x.split(':')[-1]} (edge {e1}, {E[e1]['consumer_call']}) and {y.split(':')[-1]} (edge {e2}, {E[e2]['consumer_call']}); no directed path {x.split(':')[-1]}<->{y.split(':')[-1]} in any direction")
    elif co:
        same = [(x, y) for x in A_ for y in B_ if x.rsplit(':', 1)[0] == y.rsplit(':', 1)[0] and (execd.get(x, set()) & execd.get(y, set()))]
        same = [(x, y) for x, y in same if x.rsplit(':', 1)[0] not in ('NFCORE_RNASEQ:RNASEQ', 'NFCORE_RNASEQ')]   # the top-level workflow scope holds ~100 processes: co-membership there says nothing
        if not same: continue
        x, y = same[0]
        row.update(negative_kind='same-subworkflow-no-exchange', coexecuted_in_previews=';'.join(co),
                   evidence=f"{x.split(':')[-1]} (call {INST[x]['call_file']}:{INST[x]['call_line']}) and {y.split(':')[-1]} (call {INST[y]['call_file']}:{INST[y]['call_line']}) run in the same scope {x.rsplit(':',1)[0]}; no shared producer and no path")
    else:
        excl = [(x, y) for x in A_ for y in B_ if infeasible(INST[x]['conds'] + INST[y]['conds'])]
        if not excl: continue
        x, y = excl[0]
        row.update(negative_kind='mutually-exclusive-alternatives', coexecuted_in_previews='',
                   evidence=f"conditions contradict: {x.split(':')[-1]} [{'; '.join(INST[x]['conds'])}] vs {y.split(':')[-1]} [{'; '.join(INST[y]['conds'])}]")
    row.update(decision='Negative', decision_confidence='medium', verification='graph-computed (no path in extracted graph); not individually read in source')
    neg.append(row)

# directional negatives: A -> B has no path although both consume the same input and B -> A does exist (e.g. FastQC -> Trim Galore)
directional = []
for a, b in itertools.permutations(cand, 2):
    A_, B_ = members[a], members[b]
    if any(y in desc[x] for x in A_ for y in B_): continue                     # a path A -> B exists
    if not any(x in desc[y] for x in A_ for y in B_): continue               # no path either way: handled by the symmetric loop above
    if ALT_OF.get(a) == KEY2NAME.get(b) or ALT_OF.get(b) == KEY2NAME.get(a): continue
    hit = None
    for x in A_:
        for y in B_:
            common = set(preds[x]) & set(preds[y])
            if common and (execd.get(x, set()) & execd.get(y, set())): hit = (x, y, sorted(common)[0]); break
        if hit: break
    if not hit: continue
    x, y, p = hit; e1, e2 = preds[x][p][0], preds[y][p][0]
    directional.append({'source_software': KEY2NAME[a], 'target_software': KEY2NAME[b], 'direction_tested': f'{KEY2NAME[a]} -> {KEY2NAME[b]} (the reverse direction is a real flow)',
        'negative_kind': 'shared-input', 'coexecuted_in_previews': ';'.join(sorted(execd[x] & execd[y])),
        'evidence': f"both consume {p[0].split(':')[-1]}.{p[1]} : {x.split(':')[-1]} (edge {e1}, {E[e1]['consumer_call']}) and {y.split(':')[-1]} (edge {e2}, {E[e2]['consumer_call']}); no directed path {x.split(':')[-1]} => {y.split(':')[-1]}",
        'decision': 'Negative', 'decision_confidence': 'medium', 'verification': 'graph-computed (no path in this direction)'})
for r in directional:
    if (r['source_software'], r['target_software']) == ('FastQC', 'Trim Galore'):
        r['verification'] = 'manual source read: subworkflows/nf-core/fastq_fastqc_umitools_trimgalore/main.nf:42 FASTQC(reads) and :74 TRIMGALORE(ch_trimmer_reads) read the same reads; FASTQC html/zip are assigned to ch_fastqc_html/zip (:43-45) only'; r['decision_confidence'] = 'high'
neg += directional

# pairs whose every extracted edge carries no payload / was rejected
byp = collections.defaultdict(list)
for e in edges:
    for ka in keys_of(e['src_instance']):
        for kb in keys_of(e['dst_instance']):
            if ka != kb: byp[(ka, kb)].append(e['edge_id'])
nopayload, infodep = [], []
for (ka, kb), ids in sorted(byp.items()):
    if ka in WEAK or kb in WEAK or 'multiqc' in (ka, kb): continue
    if not all(V2[i] in ('rejected', 'low') for i in ids): continue
    kinds = collections.Counter(E[i]['edge_class'] if V2[i] == 'low' else 'rejected:' + (MA.get(i, {}).get('family_verdict') or 'audit-decision') for i in ids)
    gate = any(E[i]['edge_class'] in ('gating-or-metadata', 'metadata-dependency') for i in ids if V2[i] == 'low')
    base = {'source_software': KEY2NAME[ka], 'target_software': KEY2NAME[kb], 'direction_tested': f'{KEY2NAME[ka]} -> {KEY2NAME[kb]}', 'coexecuted_in_previews': ''}
    if not gate:
        nopayload.append({**base, 'negative_kind': 'extractor-artifact-or-sync-only', 'decision': 'Negative', 'decision_confidence': 'high',
                          'evidence': 'all %d extracted edges carry no payload: %s; e.g. %s (key-only join: fastq_qc_trim_filter_setstrandedness/main.nf:191,298,325,358; dropped closure params: see audit/payload_audit.csv)' % (len(ids), dict(kinds), ids[0]),
                          'verification': 'rule-based on source-verified patterns (key-only join / underscore-dropped closure parameter / multiMap / constant call argument)'})
    else:
        infodep.append({**base, 'negative_kind': 'information-dependency', 'decision': 'Unresolved', 'decision_confidence': 'low',
                        'evidence': 'all %d extracted edges are gates or metadata, not data payload: %s; e.g. %s. Gate: workflows/rnaseq/main.nf:479-512 (STAR percent-mapped filters BAMs); metadata: Salmon lib_format_counts -> meta strandedness (workflows/rnaseq/main.nf:655-662)' % (len(ids), dict(kinds), ids[0]),
                        'verification': 'definition-dependent: derived information is used, no file payload; excluded from both positive and negative controls'})
manual_neg = [dict(source_software=r['source_software'], target_software=r['target_software'], direction_tested=f"{r['source_software']} -> {r['target_software']}",
                   negative_kind=r['flow_type'], coexecuted_in_previews='', evidence=r['source_lines_read_by_auditor'], decision='Negative', decision_confidence=r['decision_confidence'],
                   verification='manual source read (pair ' + r['pair_id'] + ')') for r in dec_rows if r['decision'] == 'Negative']
rev = []
pos_pairs = set()
for e in edges:
    if e['edge_id'] in verified_ok:
        for ka in keys_of(e['src_instance']):
            for kb in keys_of(e['dst_instance']):
                if ka != kb and not ({ka, kb} & EXCLUDE): pos_pairs.add((ka, kb))
for ka, kb in sorted(pos_pairs):
    if (kb, ka) in pos_pairs: continue
    if any(x in desc[y] for x in members[ka] for y in members[kb]): continue       # B -> ... -> A exists somewhere: not a clean negative
    if any(y in desc[x] for x in members[kb] for y in members[ka]): continue
    rev.append({'source_software': KEY2NAME[kb], 'target_software': KEY2NAME[ka], 'direction_tested': f'{KEY2NAME[kb]} -> {KEY2NAME[ka]} (reverse of verified {KEY2NAME[ka]} -> {KEY2NAME[kb]})',
                'negative_kind': 'reverse-of-verified-positive', 'coexecuted_in_previews': '', 'decision': 'Negative', 'decision_confidence': 'high',
                'evidence': f'{KEY2NAME[ka]} -> {KEY2NAME[kb]} is a source-verified data flow; no process of {KEY2NAME[kb]} reaches any process of {KEY2NAME[ka]} in the extracted graph (static process graph is acyclic)',
                'verification': 'graph-computed on top of source-verified forward edge'})
S1 = {'Preseq', 'Qualimap', 'dupRadar', 'featureCounts (Subread)', 'StringTie', 'BEDTools'}
MANUAL = 'manual source read: all consume the genome BAM (workflows/rnaseq/main.nf:551 StringTie, :670-674 genomecov; subworkflows/nf-core/bam_qc_rnaseq/main.nf:29-70 Preseq/featureCounts/Qualimap/dupRadar with ch_genome_bam = ch_bam_bai.map{meta,bam,_bai -> ...}); outputs go only to their own downstream/MultiQC bundles'
for r in neg:
    if r['source_software'] in S1 and r['target_software'] in S1 and r['negative_kind'] != 'mutually-exclusive-alternatives':
        r['verification'] = MANUAL; r['decision_confidence'] = 'high'
    if {r['source_software'], r['target_software']} == {'NVIDIA Parabricks rna_fq2bam (STAR-based)', 'Sentieon STAR'}:
        r['verification'] = 'manual source read: subworkflows/local/utils_nfcore_rnaseq_pipeline/main.nf:323-325 errors when both --use_parabricks_star and --use_sentieon_star are set'; r['decision_confidence'] = 'high'
    if {r['source_software'], r['target_software']} == {'fastp', 'Trim Galore'}:
        r['verification'] = 'manual source read: subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf: if (trimmer == trimgalore) / if (trimmer == fastp) are separate blocks'; r['decision_confidence'] = 'high'
neg_all = manual_neg + nopayload + rev + neg
# one row per ordered pair: manual reads win, other supporting rules are kept in also_supported_by
merged = collections.OrderedDict()
for r in neg_all:
    k = (r['source_software'], r['target_software'])
    if k not in merged: merged[k] = dict(r, also_supported_by=''); continue
    cur = merged[k]
    if r['verification'].startswith('manual') and not cur['verification'].startswith('manual'):
        r2 = dict(r, also_supported_by=cur['negative_kind'] + (';' + cur['also_supported_by'] if cur['also_supported_by'] else '')); merged[k] = r2
    else: cur['also_supported_by'] = ';'.join(filter(None, [cur['also_supported_by'], r['negative_kind']]))
neg_all = list(merged.values())
wr(os.path.join(C, 'negative_controls.csv'), neg_all, ['source_software', 'target_software', 'direction_tested', 'negative_kind', 'also_supported_by', 'decision', 'decision_confidence', 'verification', 'coexecuted_in_previews', 'evidence'])

wr(os.path.join(C, 'unresolved.csv'), infodep + [dict(source_software=r['source_software'], target_software=r['target_software'], direction_tested='', negative_kind=r['flow_type'], decision='Unresolved', decision_confidence=r['decision_confidence'], verification='', coexecuted_in_previews='', evidence=r['explanation']) for r in dec_rows if r['decision'] == 'Unresolved'],
   ['source_software', 'target_software', 'direction_tested', 'negative_kind', 'decision', 'decision_confidence', 'verification', 'coexecuted_in_previews', 'evidence'])
# ------------------------------------------------------------------ summary
cnt = collections.Counter(r['decision'] for r in dec_rows)
summary = {'core_pairs': len(dec_rows), 'decisions_core53': {k: cnt.get(k, 0) for k in ('Gold', 'Silver', 'Negative', 'Unresolved')},
           'edges_total': len(edges), 'v1_confidence': dict(collections.Counter(V1.values())), 'v2_confidence': dict(collections.Counter(V2.values())),
           'v1_to_v2': {f'{a}->{b}': n for (a, b), n in sorted(trans.items())},
           'high_v1': len(hi), 'tierA': len(ta), 'high_and_tierA': len(both), 'high_only': len(hi_only), 'tierA_only': len(ta_only),
           'merged_channel_edges': sum(1 for r in MA.values() if r['edge_class'] == 'merged-channel'), 'merged_audit': dict(collections.Counter(r['family_verdict'] for r in MA.values() if r['edge_class'] == 'merged-channel')), 'direct_audit': dict(collections.Counter(r['family_verdict'] for r in MA.values() if r['edge_class'] == 'direct')),
           'negative_controls': {'total_unique_ordered_pairs': len(neg_all), 'by_kind': dict(collections.Counter(r['negative_kind'] for r in neg_all)), 'rows_before_dedup': len(manual_neg) + len(nopayload) + len(rev) + len(neg), 'manual_from_core53': len(manual_neg), 'extractor_artifact_or_sync_only': len(nopayload), 'reverse_of_verified_positive': len(rev), 'manually_verified': sum(1 for r in neg_all if r['verification'].startswith('manual')), 'unresolved_information_dependency': len(infodep),
                                 'shared_input_directional': len(directional), **{k: sum(1 for r in neg if r['negative_kind'] == k) for k in ('shared-input', 'same-subworkflow-no-exchange', 'mutually-exclusive-alternatives')}},
           'tierA_only_breakdown': dict(ta_only_breakdown), 'high_only_breakdown': dict(hi_only_breakdown)}
json.dump(summary, open(os.path.join(A, 'summary.json'), 'w'), indent=1)
print(json.dumps(summary, indent=1))
