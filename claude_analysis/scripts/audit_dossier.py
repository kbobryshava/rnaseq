#!/usr/bin/env python3
"""Build a per-pair evidence dossier for the 53 core (tier A) software pairs. Read-only on existing results.
Output: audit/core_pair_dossier.md and audit/core_pair_edges.csv (all supporting process edges, tier-A and others)."""
import csv, json, os, re, collections, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); repo = os.path.dirname(root)
P = os.path.join(root, 'data', 'processed'); A = os.path.join(root, 'audit'); os.makedirs(A, exist_ok=True)
core = list(csv.DictReader(open(os.path.join(P, 'software_edges_core_tierA.csv'), encoding='utf-8')))
ev = {}
for l in open(os.path.join(P, 'process_edges_evidence.jsonl'), encoding='utf-8'):
    r = json.loads(l); ev[r['edge_id']] = r
rows = list(ev.values())
out = []; md = ['# Core-pair dossier (auto-generated; decisions are in curation/core_pair_decisions.csv)\n']
for n, c in enumerate(core, 1):
    s, d = c['src_software'], c['dst_software']
    sup = [r for r in rows if r['src_software'] == s and r['dst_software'] == d]
    tA = [r for r in sup if r['evidence_tier'].startswith('A')]
    md.append(f'\n## P{n:02d}: {s} -> {d}  (edges {len(sup)}, tierA {len(tA)})')
    for r in tA:
        md.append(f"- {r['edge_id']} {r['src_instance']}.{r['src_emit']} -> {r['dst_instance']}[in{r['dst_input_index']}] class={r['edge_class']} conf={r['confidence_v1']} ops={r['operators']}")
        md.append(f"  - producer decl: {r['src_output_decl']} @ {r['producer_call']}; consumer decl: {r['dst_input_decl']} @ {r['consumer_call']}; flags={r['flags']}")
        md.append(f"  - assumes: {r['required_param_assumptions']}; dag: {r['confirmed_by_hubfree_dag_in']}")
    for r in sup:
        out.append({'pair_id': f'P{n:02d}', 'src_software': s, 'dst_software': d, **{k: r[k] for k in ('edge_id', 'src_instance', 'src_emit', 'dst_instance', 'dst_input_index', 'edge_class', 'confidence_v1', 'confidence_v2', 'evidence_tier', 'operators', 'consumer_call', 'producer_call', 'confirmed_by_hubfree_dag_in')}})
open(os.path.join(A, 'core_pair_dossier.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
with open(os.path.join(A, 'core_pair_edges.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print(len(core), 'pairs,', len(out), 'edge rows')
