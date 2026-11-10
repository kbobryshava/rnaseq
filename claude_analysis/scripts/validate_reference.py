#!/usr/bin/env python3
"""Validate the frozen reference dataset. Writes reference/VALIDATION_SUMMARY.md and reference/validation.json; exit status 1 if any check FAILs.

Checks: duplicates, contradictions, process->software mapping, direction, execution conditions, source file:line provenance (+ content anchors),
audit vs canonical consistency, preservation of the original (v1) results, frozen record counts.
"""
import csv, json, os, re, sys, collections
import networkx as nx
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); REPO = os.path.dirname(ROOT)
P = os.path.join(ROOT, 'data', 'processed'); A = os.path.join(ROOT, 'audit'); C = os.path.join(A, 'curated'); R = os.path.join(ROOT, 'reference')
RP = os.path.join(R, 'process_level'); RS = os.path.join(R, 'software_level')
FROZEN = {'Gold': 29, 'Silver': 22, 'Negative_verified': 19, 'Negative_unverified': 127, 'Unresolved': 37}   # record counts of the frozen release
rd = lambda p: list(csv.DictReader(open(p, encoding='utf-8', newline='')))
res = []   # (id, title, status, detail)
def check(cid, title, bad, info='', warn=False):
    res.append((cid, title, ('WARN' if warn else 'FAIL') if bad else 'PASS', (f'{len(bad)} issue(s): ' + '; '.join(map(str, bad[:6])) + (' ...' if len(bad) > 6 else '')) if bad else info))
def info(cid, title, text): res.append((cid, title, 'INFO', text))

PR = rd(os.path.join(RP, 'process_relationships_all.csv')); SW = rd(os.path.join(RS, 'software_relationships_all.csv'))
EDGES = {e['edge_id']: e for e in rd(os.path.join(P, 'process_edges.csv'))}
FIN = {r['edge_id']: r for r in rd(os.path.join(A, 'process_edges_final_confidence.csv'))}
SWM = {r['process_instance']: r for r in rd(os.path.join(P, 'process_software_map.csv'))}
CANON = {r['key']: r for r in rd(os.path.join(P, 'canonical_software.csv'))}; CANON_NAMES = {r['canonical_name'] for r in CANON.values()}
G = json.load(open(os.path.join(P, 'static_graph.json'))); INST = {i['path']: i for i in G['instances']}
PBY = {r['edge_id']: r for r in PR}

# ---- 1 duplicates
d = [k for k, n in collections.Counter((r['source_software'], r['target_software']) for r in SW).items() if n > 1]
check('D1', 'no duplicate ordered software pair in software_relationships_all', d)
d = [k for k, n in collections.Counter(r['edge_id'] for r in PR).items() if n > 1]
check('D2', 'no duplicate process edge_id', d)
d = [k for k, n in collections.Counter((r['src_instance'], r['src_emit'], r['dst_instance'], r['dst_input_index']) for r in PR).items() if n > 1]
check('D3', 'no duplicate (source instance, emit, target instance, input slot)', d)
files = {f: rd(os.path.join(RS, f)) for f in os.listdir(RS) if f.endswith('.csv') and f != 'software_relationships_all.csv'}
seen = collections.Counter(); [seen.update((r['source_software'], r['target_software']) for r in rows) for rows in files.values()]
check('D4', 'every software pair appears in exactly one category file', [k for k, n in seen.items() if n > 1] + ([f'{len(SW)-len(seen)} missing'] if len(seen) != len(SW) else []))
check('D5', 'category files add up to the combined table', [] if sum(len(v) for v in files.values()) == len(SW) else ['mismatch'])

# ---- 2 contradictions
pos = {(r['source_software'], r['target_software']) for r in SW if r['category'] in ('Gold', 'Silver')}
neg = {(r['source_software'], r['target_software']) for r in SW if r['category'].startswith('Negative')}
unr = {(r['source_software'], r['target_software']) for r in SW if r['category'] == 'Unresolved'}
ind_pos = {(r['source_software'], r['target_software']) for r in rd(os.path.join(C, 'positive_controls.csv'))}
ind_neg = {(r['source_software'], r['target_software']) for r in rd(os.path.join(C, 'negative_controls.csv'))}
ind_unr = {(r['source_software'], r['target_software']) for r in rd(os.path.join(C, 'unresolved.csv'))}
check('C1', 'no pair is both positive and negative/unresolved (independent source files)', sorted((ind_pos & ind_neg) | (ind_pos & ind_unr) | (ind_neg & ind_unr)))
check('C2', 'consolidated sets equal the independent curated sets', [] if (pos == ind_pos and neg == ind_neg and unr == ind_unr) else ['set mismatch'])
live = collections.defaultdict(list)
for r in PR:
    if r['confidence_final'] in ('high', 'medium'): live[(r['src_software'], r['dst_software'])].append(r['edge_id'])
check('C3', 'no negative pair has a live (high/medium) process edge', [(k, live[k][:2]) for k in sorted(neg) if k in live])
check('C4', 'every Gold/Silver pair has a source-verified positive supporting edge and no rejected supporting edge',
      [r['software_pair_id'] for r in SW if r['category'] in ('Gold', 'Silver') and (not r['process_edge_ids'] or any(PBY[e]['validation_category'] != 'source_verified_positive' for e in r['process_edge_ids'].split(';')))])
check('C5', 'no verified-positive process edge is rejected by the payload check', [e for e, r in PBY.items() if r['validation_category'] == 'source_verified_positive' and r['payload_check'] in ('PROJECTION-DROPPED', 'MULTIMAP-SPLIT', 'INFEASIBLE-CALLSITE-CONSTANT')])
check('C6', 'no source-verified-negative process edge also appears in a Gold/Silver pair', [e for r in SW if r['category'] in ('Gold', 'Silver') for e in r['process_edge_ids'].split(';') if PBY[e]['validation_category'] == 'source_verified_negative'])
both = sorted(k for k in pos if (k[1], k[0]) in pos and k[0] < k[1])
info('C7', 'software pairs that are positive in both directions (allowed: the same software is used at different stages)', f'{len(both)}: ' + '; '.join(f'{a} <-> {b}' for a, b in both))

# ---- 3 process -> software mapping
check('M1', 'every process instance in an edge has a software mapping', sorted({i for r in PR for i in (r['src_instance'], r['dst_instance']) if i not in SWM}))
check('M2', 'mapped software keys exist in the canonical software table', sorted({k for m in SWM.values() for k in m['primary_software_keys'].split(';') if k and k not in CANON}))
check('M3', 'edge src/dst software equals the process->software map', [r['edge_id'] for r in PR if r['src_software'] != SWM[r['src_instance']]['primary_software'] or r['dst_software'] != SWM[r['dst_instance']]['primary_software']])
bymod = collections.defaultdict(set)
for i, m in SWM.items(): bymod[m['process_module']].add(m['primary_software'])
check('M4', 'one module -> one software (no module is mapped to different software in different instances)', sorted(k for k, v in bymod.items() if len(v) > 1))
check('M5', 'no multi-tool process mapped (software pairs would be ambiguous)', [i for i, m in SWM.items() if m['multi_tool_process'] == 'True'])
unrev = [i for i, m in SWM.items() if 'UNREVIEWED' in m['mapping_method']]
check('M6', 'no process mapping is auto-derived/unreviewed', unrev)
mm = [(m['process_module'], m['meta_yml_tools'], m['primary_software']) for i, m in SWM.items() if m['meta_yml_tools'] and not any(t.lower().split()[0] in m['primary_software'].lower() or m['primary_software'].lower().split()[0] in t.lower() for t in m['meta_yml_tools'].split(';'))]
info('M7', 'curated mapping differs from meta.yml tools (reviewed, curated value kept)', f'{len({x[0] for x in mm})} modules, e.g. ' + '; '.join(sorted({f"{a}: meta.yml={b!r} -> {c}" for a, b, c in mm})[:5]))
# identity vs operation: software identity is not the operation performed
bad = []
for r in SW:
    if r['category'] in ('Gold', 'Silver') and r['source_software'] == 'RSEM' and 'rsem-calculate-expression' not in r['source_operations'] and 'prepare-reference' not in r['source_operations']: bad.append(r['software_pair_id'])
    if not r['source_operations'] and r['process_edge_ids']: bad.append(r['software_pair_id'])
check('M8', 'every pair with process edges records the operation actually performed', bad)
rk = [r for r in SW if (r['source_software'], r['target_software']) == ('RSEM', 'kallisto')]
check('M9', 'RSEM -> kallisto is recorded as rsem-prepare-reference transcript extraction (not RSEM quantification)', [] if rk and 'no RSEM quantification' in rk[0]['source_operations'] and 'rsem-calculate-expression (quantification)' not in rk[0]['source_operations'] and rk[0]['category'] == 'Gold' else ['wrong operation or category'])
opsw = collections.defaultdict(set)
for r in PR: opsw[r['src_software']].add(r['src_operation'])
info('M10', 'software nodes standing for several different operations', '; '.join(f'{k}: {len(v)}' for k, v in sorted(opsw.items(), key=lambda x: -len(x[1]))[:6]) + ' (see src_operation / dst_operation; always join pairs back to process level)')

# ---- 4 direction
dg = nx.DiGraph([(r['src_instance'], r['dst_instance']) for r in PR])
check('R1', 'process graph is acyclic (no process-level cycle)', [sorted(c)[:2] for c in nx.strongly_connected_components(dg) if len(c) > 1])
check('R2', 'no process edge from an instance to itself', [r['edge_id'] for r in PR if r['src_instance'] == r['dst_instance']])
badr = []
for r in PR:
    s, t = INST[r['src_instance']], INST[r['dst_instance']]
    if r['src_emit'] not in {o['emit'] for o in s['outputs']}: badr.append((r['edge_id'], 'emit'))
    if int(r['dst_input_index']) >= len(t['inputs']): badr.append((r['edge_id'], 'input slot'))
check('R3', 'source emit is a declared output of the producer and the input slot exists on the consumer', badr)
cr = []
for r in SW:
    if r['category'] in ('Gold', 'Silver'):
        for e in r['process_edge_ids'].split(';'):
            p = PBY[e]
            if p['src_software'] != r['source_software'] or p['dst_software'] != r['target_software']: cr.append((r['software_pair_id'], e))
check('R4', 'direction of each Gold/Silver supporting edge matches the pair (producer = source)', cr)

# ---- 5 execution conditions
def contradictory(txt):
    at = collections.defaultdict(set)
    for a in [x.strip() for x in txt.split(' & ') if x.strip()]:
        m = re.match(r'^(\S+) (truthy|eq|ne) (.*)$', a)
        if m: at[m.group(1)].add((m.group(2), m.group(3)))
    out = []
    for k, v in at.items():
        eq = {x for o, x in v if o == 'eq'}; ne = {x for o, x in v if o == 'ne'}; tr = {x for o, x in v if o == 'truthy'}
        if len(eq) > 1 or (eq & ne) or len(tr) > 1: out.append(k)
    if 'use_parabricks_star' in at and 'use_sentieon_star' in at and ('truthy', 'True') in at['use_parabricks_star'] and ('truthy', 'True') in at['use_sentieon_star']: out.append('parabricks+sentieon')
    return out
cb = [(r['edge_id'], contradictory(r['required_params'])) for r in PR if r['validation_category'] in ('source_verified_positive', 'algorithmic_supported') and contradictory(r['required_params'])]
check('E1', 'no positive edge has contradictory execution conditions', cb)
check('E2', "'conditional' flag is consistent with recorded conditions", [r['edge_id'] for r in PR if r['required_params'] and r['conditional'] != 'True'])
gp = [r for r in SW if r['category'] in ('Gold', 'Silver')]
nodag = [r['pair_id'] for r in gp if not r['hubfree_dag_configs']]
info('E3', 'Gold/Silver pairs without hub-free preview-DAG confirmation (verified by source reading only)', f'{len(nodag)} of {len(gp)}: ' + ','.join(nodag))
unc = [r['pair_id'] for r in gp if not any(PBY[e]['required_params'] for e in r['process_edge_ids'].split(';'))]
info('E4', 'Gold/Silver pairs whose supporting edges carry no recorded conditions (always active)', f'{len(unc)}: ' + ','.join(unc))
sch = json.load(open(os.path.join(REPO, 'nextflow_schema.json')))
params = set()
def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == 'properties' and isinstance(v, dict): params.update(v)
            walk(v)
    elif isinstance(o, list): [walk(x) for x in o]
walk(sch)
atoms = {a.split(' ')[0] for r in gp for e in r['process_edge_ids'].split(';') for a in PBY[e]['required_params'].split(' & ') if a}
info('E5', 'condition atoms of positives that are not --params (derived variables, documented in evidence text)', ', '.join(sorted(atoms - params)) or 'none')

# ---- 6 provenance
REF = re.compile(r'((?:[\w.\-]+/)*[\w.\-]+\.(?:nf|config|py)):(\d+)(?:-(\d+))?')
allf = []
for base in ('modules', 'subworkflows', 'workflows', 'conf', 'bin'):
    for dp, _, fs in os.walk(os.path.join(REPO, base)):
        allf += [os.path.relpath(os.path.join(dp, f), REPO).replace('\\', '/') for f in fs if f.endswith(('.nf', '.config', '.py'))]
allf += ['main.nf', 'nextflow.config']
nlines = {}
def resolve(ref):
    cands = [ref] if ref in allf else [f for f in allf if f.endswith('/' + ref)]
    return cands[0] if len(cands) == 1 else None
def lines_of(f):
    if f not in nlines: nlines[f] = open(os.path.join(REPO, f), encoding='utf-8', errors='replace').read().splitlines()
    return nlines[f]
bad_ref, n_ref = [], 0
def chk(text, where):
    global n_ref
    for m in REF.finditer(text or ''):
        n_ref += 1; f = resolve(m.group(1)); ln = int(m.group(2)); ln2 = int(m.group(3) or ln)
        if not f or ln < 1 or ln2 > len(lines_of(f)) or ln2 < ln: bad_ref.append((where, m.group(0)))
for r in PR:
    for c in ('producer_call', 'consumer_call', 'src_module_file', 'dst_module_file'): chk(r[c], f"{r['edge_id']}.{c}")
for r in SW: chk(r['evidence_basis'] + ' ' + r['explanation'], r['software_pair_id'])
check('P1', f'all {n_ref} file:line references resolve to an existing file and a line inside it', bad_ref)
ANCH = [('subworkflows/local/prepare_genome_indices/main.nf', 60, r'_fai'), ('subworkflows/local/align_star/main.nf', 51, r'_fai'), ('subworkflows/local/align_star/main.nf', 61, r'ch_orig_bam'),
        ('subworkflows/nf-core/bam_qc_rnaseq/main.nf', 27, r'_bai'), ('subworkflows/nf-core/fastq_qc_trim_filter_setstrandedness/main.nf', 325, r'_lint'),
        ('subworkflows/local/prepare_genome_references/main.nf', 180, r'MAKE_TRANSCRIPTS_FASTA'), ('subworkflows/local/prepare_genome_references/main.nf', 20, r'RSEM_PREPAREREFERENCE as MAKE_TRANSCRIPTS_FASTA'),
        ('subworkflows/local/prepare_genome_indices/main.nf', 292, r'KALLISTO_INDEX'), ('modules/nf-core/rsem/preparereference/main.nf', 46, r'genome\.transcripts\.fa'),
        ('workflows/rnaseq/main.nf', 731, r'ch_kraken_reports\s*=\s*KRAKEN2\.out\.report'), ('workflows/rnaseq/main.nf', 738, r'BRACKEN'), ('workflows/rnaseq/main.nf', 461, r"'salmon'"),
        ('subworkflows/local/utils_nfcore_rnaseq_pipeline/main.nf', 323, r'use_parabricks_star.*use_sentieon_star'), ('modules/nf-core/custom/tx2gene/templates/tx2gene.py', 152, r'salmon'),
        ('subworkflows/local/prepare_genome_references/main.nf', 228, r'UNTAR_KRAKEN_DB'), ('modules/nf-core/salmon/quant/main.nf', 39, r'transcript_fasta'),
        ('subworkflows/nf-core/fastq_fastqc_umitools_trimgalore/main.nf', 74, r'TRIMGALORE'), ('subworkflows/nf-core/fastq_fastqc_umitools_trimgalore/main.nf', 42, r'FASTQC'),
        ('subworkflows/local/prepare_genome_indices/main.nf', 149, r'use_parabricks_star'), ('subworkflows/local/prepare_genome_indices/main.nf', 168, r'fasta_provided')]
badA = [(f, l, rx) for f, l, rx in ANCH if not re.search(rx, lines_of(f)[l - 1])]
check('P2', f'{len(ANCH)} content anchors (the lines the key decisions rest on) contain the expected text', badA)
check('P3', 'every positive/negative software record carries evidence text and (for process-backed records) a call-site line',
      [r['software_pair_id'] for r in SW if r['category'] in ('Gold', 'Silver', 'Negative_verified') and not (r['evidence_basis'] and REF.search(r['evidence_basis'] + r['explanation']))])
check('P4', 'every process record has producer_call, consumer_call and module file:line', [r['edge_id'] for r in PR if not (REF.fullmatch(r['producer_call'] or '') and REF.fullmatch(r['consumer_call'] or '') and r['src_module_file'] and r['dst_module_file'])])

# ---- 7 audit vs canonical
check('A1', 'audit confidence table covers exactly the canonical edge ids', [] if set(FIN) == set(EDGES) == set(PBY) else ['id sets differ'])
pa = {r['edge_id']: r['family_verdict'] for r in rd(os.path.join(A, 'payload_audit.csv'))}
check('A2', 'audit payload verdicts equal the verdicts stored in the canonical build', [e for e, v in pa.items() if EDGES[e]['payload_check'] != v])
aud = json.load(open(os.path.join(A, 'summary.json')))
cnt = collections.Counter(r['category'] for r in SW)
check('A3', 'audit summary counts equal reference counts', [] if (aud['decisions_core53']['Gold'] == cnt['Gold'] and aud['decisions_core53']['Silver'] == cnt['Silver'] and aud['negative_controls']['manually_verified'] == cnt['Negative_verified'] and aud['negative_controls']['unresolved_information_dependency'] == cnt['Unresolved'] and aud['negative_controls']['total_unique_ordered_pairs'] == cnt['Negative_verified'] + cnt['Negative_unverified']) else [str(aud['decisions_core53']), dict(cnt)])
v1 = {r['edge_id']: r['confidence'] for r in rd(os.path.join(ROOT, 'data', 'processed_v1_original', 'process_edges.csv'))}
check('A4', 'original (v1) confidence preserved: confidence_v1 equals the frozen original results for every edge', [e for e in EDGES if v1.get(e) != EDGES[e]['confidence_v1']])
check('A5', 'edge sets of canonical and original results are identical', [] if set(v1) == set(EDGES) else ['edge id sets differ'])
check('A6', 'process category counts add up', [] if sum(collections.Counter(r['validation_category'] for r in PR).values()) == len(EDGES) else ['mismatch'])
chg = collections.Counter((r['confidence_v1'], r['confidence_final']) for r in PR)
info('A7', 'confidence_v1 -> confidence_final transitions', ', '.join(f'{a}->{b}: {n}' for (a, b), n in sorted(chg.items())))

# ---- 8 frozen counts
check('F1', 'record counts equal the frozen release', [f'{k}: {cnt[k]} != {v}' for k, v in FROZEN.items() if cnt[k] != v])
check('F2', 'verified-negative software pairs include the two negatives from the 53 core pairs', [] if {('SAMtools', 'BBMap (BBSplit)'), ('fq', 'BBMap (BBSplit)')} <= {(r['source_software'], r['target_software']) for r in SW if r['category'] == 'Negative_verified'} else ['missing'])

nf = sum(1 for r in res if r[2] == 'FAIL'); nw = sum(1 for r in res if r[2] == 'WARN')
L = ['# Validation summary', '', f'Result: **{"FAIL" if nf else "PASS"}** ({sum(1 for r in res if r[2]=="PASS")} pass, {nw} warn, {nf} fail, {sum(1 for r in res if r[2]=="INFO")} informational)', '',
     '| id | check | status | detail |', '|---|---|---|---|'] + [f'| {a} | {b} | {c} | {d.replace("|", "/")} |' for a, b, c, d in res]
L += ['', '## Record counts', '', '| table | category | n |', '|---|---|---|'] + [f'| software_relationships | {k} | {v} |' for k, v in sorted(cnt.items())] + \
     [f'| process_relationships | {k} | {v} |' for k, v in sorted(collections.Counter(r['validation_category'] for r in PR).items())]
open(os.path.join(R, 'VALIDATION_SUMMARY.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
json.dump([dict(id=a, title=b, status=c, detail=d) for a, b, c, d in res], open(os.path.join(R, 'validation.json'), 'w'), indent=1)
print('\n'.join(f'{c:5} {a:4} {b}  {d[:140] if c != "PASS" else ""}' for a, b, c, d in res))
sys.exit(1 if nf else 0)
