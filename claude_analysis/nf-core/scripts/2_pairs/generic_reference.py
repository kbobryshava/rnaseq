#!/usr/bin/env python3
"""Generic reference builder: turns data/processed (from build_datasets.py --profile generic) into reference/ tables for ANY Nextflow DSL2 pipeline.

No pipeline-specific knowledge is used. Categories are algorithmic unless you pass --curation (a CSV of your own decisions).
  process_relationships.csv   one row per process edge   (category: algorithmic_supported | algorithmic_negative_candidate | functional_dependency_non_data)
  software_relationships.csv  one row per ordered software pair (Algorithmic_supported | Dependency_gate_metadata | Parallel_co_use | Negative_candidate | Gold | Silver | Negative_verified); Parallel_co_use = both tools read the same upstream output, no path either way, and they can run in the same run: a valid pair in BOTH directions
  curation_template.csv       review worklist: every supported non-self pair with its first supporting edge and call sites -> fill `decision` and pass back with --curation
  validation.md/json, manifest.json
"""
import argparse, csv, collections, datetime, hashlib, json, os, re, subprocess, sys
import networkx as nx

ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); ap.add_argument('--repo', required=True); ap.add_argument('--curation'); a = ap.parse_args()
P = os.path.join(a.out, 'data', 'processed'); R = os.path.join(a.out, 'reference'); os.makedirs(R, exist_ok=True)
rd = lambda p: list(csv.DictReader(open(p, encoding='utf-8', newline='')))


def wr(name, rows, cols):
    with open(os.path.join(R, name), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore', lineterminator='\n'); w.writeheader(); w.writerows(rows)


edges = rd(os.path.join(P, 'process_edges.csv')); SWM = {r['process_instance']: r for r in rd(os.path.join(P, 'process_software_map.csv'))}
ROLE = {r['canonical_name']: r['role'] for r in rd(os.path.join(P, 'canonical_software.csv'))}
EV = {}
for l in open(os.path.join(P, 'process_edges_evidence.jsonl'), encoding='utf-8'):
    r = json.loads(l); EV[r['edge_id']] = r


def op(inst, module): return module.lower().replace('_', ' ', 1) + ('' if inst.split(':')[-1] == module else ' (as ' + inst.split(':')[-1] + ')')


prow = []
for e in edges:
    fin = e['confidence_v2']; cls = e['edge_class']
    if fin == 'rejected': cat = 'algorithmic_negative_candidate'     # extractor artefact proved by the payload check (dropped tuple element, constant call argument ...)
    elif cls in ('gating-or-metadata', 'metadata-dependency', 'key-only-synchronization'): cat = 'functional_dependency_non_data'   # B receives a key, verdict or metadata from A: a valid (weaker) pair
    else: cat = 'algorithmic_supported'
    prow.append({'edge_id': e['edge_id'], 'category': cat, 'src_instance': e['src_instance'], 'src_process': e['src_instance'].split(':')[-1], 'src_module': e['src_module'], 'src_emit': e['src_emit'],
                 'dst_instance': e['dst_instance'], 'dst_process': e['dst_instance'].split(':')[-1], 'dst_module': e['dst_module'], 'dst_input_index': e['dst_input_index'],
                 'src_software': e['src_software'], 'dst_software': e['dst_software'], 'src_operation': op(e['src_instance'], e['src_module']), 'dst_operation': op(e['dst_instance'], e['dst_module']),
                 'edge_class': cls, 'confidence_v1': e['confidence_v1'], 'confidence_v2': fin, 'payload_check': e['payload_check'], 'required_params': e['required_param_assumptions'],
                 'producer_call': e['producer_call'], 'consumer_call': e['consumer_call'], 'dst_input_decl': EV[e['edge_id']]['dst_input_decl'], 'src_output_decl': EV[e['edge_id']]['src_output_decl'],
                 'hubfree_dag_configs': e['confirmed_by_hubfree_dag_in']})
if not prow: sys.exit('no process edges were extracted - check that main.nf has an unnamed workflow that calls processes')
wr('process_relationships.csv', prow, list(prow[0].keys()))

by = collections.defaultdict(list)
for r in prow: by[(r['src_software'], r['dst_software'])].append(r)
srows, used = [], set()


def add(k, cat, sub, rows, ev=''):
    live = [r for r in rows if r['category'] == 'algorithmic_supported']
    srows.append({'source_software': k[0], 'target_software': k[1], 'category': cat, 'subtype': sub, 'source_role': ROLE.get(k[0], ''), 'target_role': ROLE.get(k[1], ''), 'is_self_loop': k[0] == k[1],
                  'n_process_edges': len(rows), 'n_live_edges': len(live), 'best_confidence_v2': max((r['confidence_v2'] for r in live), key=['low', 'medium', 'high'].index, default=''),
                  'process_edge_ids': ';'.join(r['edge_id'] for r in rows), 'source_operations': ' | '.join(sorted({r['src_operation'] for r in rows})),
                  'target_operations': ' | '.join(sorted({r['dst_operation'] for r in rows})),
                  'required_params': '; '.join(sorted({r['required_params'] for r in live if r['required_params']})[:3]), 'evidence': ev})
    used.add(k)


for k, rows in sorted(by.items()):
    live = [r for r in rows if r['category'] == 'algorithmic_supported']
    if live: add(k, 'Algorithmic_supported', 'self_loop' if k[0] == k[1] else 'static_channel_provenance', rows)
    elif any(r['category'] == 'functional_dependency_non_data' for r in rows): add(k, 'Dependency_gate_metadata', 'gate_or_metadata', rows)
    else: add(k, 'Negative_candidate', 'rejected_or_sync_only', rows, 'every extracted edge is rejected or key-only')

# conditions per instance (for detecting mutually exclusive alternatives)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nf_static_analyzer import infeasible
CONDS = {i['path']: i.get('conds', []) for i in json.load(open(os.path.join(P, 'static_graph.json')))['instances']}
# graph-computed negatives: no path in either direction + a shared producer output
G = nx.DiGraph([(r['src_instance'], r['dst_instance']) for r in prow]); desc = {n: nx.descendants(G, n) for n in G}
mem = collections.defaultdict(list)
for i, m in SWM.items(): mem[m['primary_software']].append(i)
cons = collections.defaultdict(set)
for r in prow:
    if r['category'] == 'algorithmic_supported': cons[(r['src_instance'], r['src_emit'])].add((r['dst_software'], r['dst_instance'], r['edge_id']))
shared = {}
for port, cs in sorted(cons.items()):
    cs = sorted(cs)
    for x in cs:
        for y in cs:
            if x[0] != y[0] and (x[0], y[0]) not in shared: shared[(x[0], y[0])] = (port, x, y)
for (s1, s2), (port, x, y) in sorted(shared.items()):
    if (s1, s2) in used: continue
    A, B = mem.get(s1, []), mem.get(s2, [])
    if any(q in desc.get(p, ()) or p in desc.get(q, ()) for p in A for q in B): continue
    excl = bool(A and B) and all(infeasible(CONDS.get(p, []) + CONDS.get(q, [])) for p in A for q in B)   # exclusive only when EVERY pair of instances can never run together
    if excl: continue   # mutually exclusive alternatives (--aligner star vs hisat2): never in one run, so not a pair and not in the dataset
    add((s1, s2), 'Parallel_co_use', 'shared-input-no-path', [],'both consume ' + port[0].split(':')[-1] + '.' + port[1] + ' (' + x[2] + ', ' + y[2] + '); no directed path between any process of the two software in the extracted graph')

# optional curation overlay (your decisions)
conflicts = []
if a.curation:
    CUR = {(r['source_software'], r['target_software']): r for r in rd(a.curation) if r.get('decision')}
    idx = {(r['source_software'], r['target_software']): r for r in srows}
    for k, c in CUR.items():
        d = c['decision'].strip(); r = idx.get(k)
        if d not in ('Gold', 'Silver', 'Negative_verified'): conflicts.append((k, 'unknown decision ' + repr(d))); continue
        if r is None: conflicts.append((k, 'pair not in extracted set')); continue
        if d in ('Gold', 'Silver') and not r['n_live_edges']: conflicts.append((k, d + ' but no live process edge')); continue
        if d == 'Negative_verified' and r['n_live_edges']: conflicts.append((k, 'Negative_verified but a live process edge exists')); continue
        r['category'] = d; r['subtype'] = 'curated'; r['evidence'] = c.get('evidence', '')
SC = ['source_software', 'target_software', 'category', 'subtype', 'source_role', 'target_role', 'is_self_loop', 'n_process_edges', 'n_live_edges', 'best_confidence_v2', 'process_edge_ids',
      'source_operations', 'target_operations', 'required_params', 'evidence']
wr('software_relationships.csv', srows, SC)
PE = {r['edge_id']: r for r in prow}
work = []
for r in srows:
    if r['category'] == 'Algorithmic_supported' and not r['is_self_loop']:
        e = PE[r['process_edge_ids'].split(';')[0]]
        work.append({'source_software': r['source_software'], 'target_software': r['target_software'], 'decision': '', 'evidence': '', 'best_confidence_v2': r['best_confidence_v2'], 'n_live_edges': r['n_live_edges'],
                     'example_edge': e['edge_id'], 'producer_output': e['src_output_decl'], 'consumer_input': e['dst_input_decl'], 'producer_call': e['producer_call'], 'consumer_call': e['consumer_call'],
                     'required_params': r['required_params'], 'source_role': r['source_role'], 'target_role': r['target_role']})
work.sort(key=lambda w: (['high', 'medium', 'low', ''].index(w['best_confidence_v2']), -int(w['n_live_edges'])))
wr('curation_template.csv', work, list(work[0].keys()) if work else ['source_software', 'target_software', 'decision', 'evidence'])

# validation
res = []


def chk(n, bad, warn=False): res.append({'check': n, 'status': ('WARN' if warn else 'FAIL') if bad else 'PASS', 'detail': '; '.join(map(str, bad[:5]))})


chk('no duplicate ordered software pair', [k for k, n in collections.Counter((r['source_software'], r['target_software']) for r in srows).items() if n > 1])
chk('no duplicate edge id', [k for k, n in collections.Counter(r['edge_id'] for r in prow).items() if n > 1])
chk('process graph is acyclic', [sorted(c)[:2] for c in nx.strongly_connected_components(G) if len(c) > 1])
REF = re.compile(r'([^\s:]+):(\d+)')   # include paths without extension exist in some pipelines
bad = []
for r in prow:
    for c in ('producer_call', 'consumer_call'):
        m = REF.fullmatch(r[c] or ''); pth = os.path.join(a.repo, m.group(1)) if m else None
        if not m or not os.path.exists(pth) or int(m.group(2)) > sum(1 for _ in open(pth, encoding='utf-8', errors='replace')): bad.append((r['edge_id'], c, r[c]))
chk('every producer_call/consumer_call is an existing file:line', bad)
unrev = sorted({m['process_module'] for m in SWM.values() if 'UNREVIEWED' in m['mapping_method']})
chk(str(len(unrev)) + ' process modules have an auto-guessed (UNREVIEWED) software mapping: review them via --software-map', unrev, warn=True)
chk('curation decisions are consistent with the extracted edges', conflicts)
json.dump(res, open(os.path.join(R, 'validation.json'), 'w'), indent=1)
open(os.path.join(R, 'validation.md'), 'w', newline='\n').write('# Validation\n\n| check | status | detail |\n|---|---|---|\n' + ''.join('| ' + x['check'] + ' | ' + x['status'] + ' | ' + x['detail'][:200] + ' |\n' for x in res))
try: sha = subprocess.check_output(['git', '-C', a.repo, 'rev-parse', 'HEAD'], stderr=subprocess.DEVNULL).decode().strip()
except Exception: sha = ''
files = {f: hashlib.sha256(open(os.path.join(R, f), 'rb').read()).hexdigest() for f in sorted(os.listdir(R)) if f != 'manifest.json'}
json.dump({'pipeline_repo': os.path.abspath(a.repo), 'pipeline_commit': sha, 'generated_utc': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d'),
           'counts': {'process_edges': dict(collections.Counter(r['category'] for r in prow)), 'software_pairs': dict(collections.Counter(r['category'] for r in srows))},
           'unreviewed_modules': unrev, 'files_sha256': files}, open(os.path.join(R, 'manifest.json'), 'w'), indent=1)
print('process edges:', dict(collections.Counter(r['category'] for r in prow)))
print('software pairs:', dict(collections.Counter(r['category'] for r in srows)))
print('validation:', dict(collections.Counter(x['status'] for x in res)), '| unreviewed modules:', len(unrev))
sys.exit(1 if any(x['status'] == 'FAIL' for x in res) else 0)
