#!/usr/bin/env python3
"""Writes audit/payload_audit.csv, merged_channel_audit.csv, merged_sites.csv from data/processed (thin wrapper around payload_checks.py)."""
import json, os, csv, collections, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import payload_checks
from payload_checks import payload_verdict
import build_datasets   # audit layer is rnaseq-specific: apply the rnaseq profile rules
payload_checks.CALLSITE_INFEASIBLE = build_datasets.RNASEQ_RULES['callsite_infeasible']; payload_checks.MULTIMAP_NOTE = build_datasets.RNASEQ_RULES['multimap_note']
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = os.path.join(root, 'data', 'processed'); A = os.path.join(root, 'audit'); REPO = os.path.dirname(root)
rows = []
for l in open(os.path.join(P, 'process_edges_evidence.jsonl'), encoding='utf-8'):
    r = json.loads(l)
    if r['edge_class'] not in ('merged-channel', 'direct'): continue
    v, dr, pf, cf = payload_verdict(r, REPO)
    rows.append({'edge_id': r['edge_id'], 'edge_class': r['edge_class'], 'src': r['src_module'] + '.' + r['src_emit'], 'dst': r['dst_module'], 'dst_input_index': r['dst_input_index'],
                 'producer_family': ';'.join(sorted(pf)), 'consumer_family': ';'.join(sorted(cf)), 'family_verdict': v, 'verdict_reason': dr, 'operators': r['operators'],
                 'consumer_call': r['consumer_call'], 'dst_input_decl': r['dst_input_decl'], 'evidence_tier': r['evidence_tier'], 'dropped_by': dr})
os.makedirs(A, exist_ok=True)
for fn, sel in (('payload_audit.csv', rows), ('merged_channel_audit.csv', [x for x in rows if x['edge_class'] == 'merged-channel'])):
    with open(os.path.join(A, fn), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(sel)
print('merged:', collections.Counter(x['family_verdict'] for x in rows if x['edge_class'] == 'merged-channel'))
print('direct:', collections.Counter(x['family_verdict'] for x in rows if x['edge_class'] == 'direct'))
sites = collections.OrderedDict()
for x in rows: sites.setdefault((x['consumer_call'], x['dst_input_index'], x['src'], x['family_verdict']), []).append(x['edge_id'])
with open(os.path.join(A, 'merged_sites.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['consumer_call', 'dst_input_index', 'src', 'family_verdict', 'n_edges', 'example_edge'])
    for k, v in sites.items(): w.writerow([*k, len(v), v[0]])
