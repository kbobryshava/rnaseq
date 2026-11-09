#!/usr/bin/env python3
"""Payload-compatibility audit of the merged-channel edges (audit task 5). Read-only on data/processed.
For each merged-channel edge, compare the *family* of the producer output (emit name + glob) with the family of the consumer
input slots (variable names in the input declaration). A merge whose producer family fits no consumer slot is a candidate
false positive (tuple element dropped or never consumed). Writes audit/merged_channel_audit.csv and audit/merged_sites.csv."""
import json, re, os, csv, collections
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(root, 'data', 'processed'); A = os.path.join(root, 'audit')
FAM = [('fai', r'\bfai\b|\.fai'), ('sizes', r'sizes'), ('bai', r'\bbai\b|\bcsi\b|\bcrai\b|\bindex\b.*(bam|cram)|bam_index'),
       ('bam', r'\bbam|\bcram|\bsam\b|bam_transcript'), ('fastq', r'fastq|fastx|reads|\.fq'), ('gtf', r'\bgtf\b|\.gtf|annotation'),
       ('fasta', r'fasta|\.fa\b|genome|primary_ref|gunzip'), ('tx2gene', r'tx2gene'), ('counts', r'counts|matrix|tpm|lengths|quants|results'),
       ('bed', r'\bbed\b|bedgraph|genomecov'), ('index', r'\bindex\b|\bdb\b|database')]
def fams(text):
    t = text.lower(); return {f for f, rx in FAM if re.search(rx, t)}
def slots(decl):
    # variable names of each path()/val() slot in a tuple/path declaration
    return re.findall(r'(?:path|val)\s*\(?\s*([A-Za-z_][\w]*)', decl)
def pf_tmp(r): return fams(r['src_emit'] + ' ' + r['src_output_decl'])
REPO = os.path.dirname(root)
_cache = {}
def src_lines(f):
    if f not in _cache: _cache[f] = open(os.path.join(REPO, f), encoding='utf-8').read().splitlines()
    return _cache[f]
def statement(at):
    f, ln = at.rsplit(':', 1); L = src_lines(f); i = int(ln) - 1; buf = []; depth = 0
    for k in range(i, min(i + 12, len(L))):
        buf.append(L[k]); depth += L[k].count('{') - L[k].count('}') + L[k].count('(') - L[k].count(')')
        if depth <= 0 and k > i - 1 and ('}' in L[k] or ')' in L[k] or k > i): break
    return ' '.join(buf)
DROP = {'bai': ('bai', 'index', 'csi'), 'fai': ('fai',), 'lint': ('lint',), 'sizes': ('sizes',)}
def dropped_in_trail(r, pfam):
    # a trail statement containing a closure whose underscore-prefixed parameter names the producer's family -> the element is discarded
    for st in r['channel_trail']:
        if 'map' not in st.get('operators', []) or ':' not in st.get('at', ''): continue
        try: txt = statement(st['at'])
        except Exception: continue
        for m in re.finditer(r'\{\s*([\w\s,_]+?)\s*->', txt):
            for prm in [x.strip() for x in m.group(1).split(',')]:
                if prm.startswith('_') and prm != '_meta' and prm.lstrip('_') != '':
                    nm = prm.lstrip('_').lower()
                    for fam, keys in DROP.items():
                        if fam in pfam and any(k in nm for k in keys): return st['at'] + ' drops ' + prm
    return ''
rows = []
for l in open(os.path.join(P, 'process_edges_evidence.jsonl'), encoding='utf-8'):
    r = json.loads(l)
    if r['edge_class'] not in ('merged-channel', 'direct'): continue
    pf = fams(r['src_emit'] + ' ' + r['src_output_decl'])
    idecl = r['dst_input_decl']; sl = slots(idecl); cs = ' '.join(sl) + ' ' + idecl
    cf = fams(cs)
    # generic slot names that accept several families (reviewed against the module input declarations)
    if any(x in ('input', 'file', 'files') for x in sl): cf |= {'bam', 'fastq', 'fasta', 'gtf', 'bed', 'counts'}
    if any(x in ('input_index', 'index') for x in sl): cf |= {'bai'}
    if any(x == 'reads' for x in sl) and r['dst_module'] in ('SALMON_QUANT', 'RSEM_CALCULATEEXPRESSION', 'SENTIEON_RSEMCALCULATEEXPRESSION', 'PICARD_MARKDUPLICATES'): cf |= {'bam'}   # alignment-based quantification
    if any(x in ('intervals', 'srbam', 'lrbam') for x in sl): cf |= {'bam'}
    if r['dst_module'] in ('FQ_LINT', 'BBMAP_BBSPLIT', 'SORTMERNA', 'RIBODETECTOR', 'BOWTIE2_ALIGN') and 'fastq' in pf_tmp(r): cf |= {'fastq'}
    dr = dropped_in_trail(r, pf)
    if not dr:   # closures written inline in the consumer call, e.g. fasta_fai.map { meta, fasta, _fai -> [meta, fasta] }
        try:
            txt = statement(r['consumer_call'])
            for m in re.finditer(r'\{\s*([\w\s,_]+?)\s*->', txt):
                for prm in [x.strip() for x in m.group(1).split(',')]:
                    nm = prm.lstrip('_').lower()
                    if prm.startswith('_') and prm != '_meta' and any(fam in pf and any(k in nm for k in keys) for fam, keys in DROP.items()): dr = r['consumer_call'] + ' (inline) drops ' + prm
        except Exception: pass
    multimap = any(st.get('var', '').startswith('map_filtered') or 'multiMap' in st.get('operators', []) for st in r['channel_trail'])
    if r['dst_instance'].endswith('QUANTIFY_BAM_SALMON:KALLISTO_QUANT'): v = 'INFEASIBLE-CALLSITE-CONSTANT'; dr = 'workflows/rnaseq/main.nf: QUANTIFY_BAM_SALMON is called with pseudo_aligner literal "salmon" (line 461); kallisto branch cannot run'
    elif dr: v = 'PROJECTION-DROPPED'
    elif not pf: v = 'unknown-producer-family'
    elif pf & cf: v = 'compatible'
    else: v = 'INCOMPATIBLE'
    if v == 'INCOMPATIBLE' and multimap and 'bai' in pf: v = 'MULTIMAP-SPLIT'; dr = 'workflows/rnaseq/main.nf:495-512 multiMap separates the bam and index branches; the analyzer unions them'
    rows.append({'edge_id': r['edge_id'], 'edge_class': r['edge_class'], 'src': r['src_module'] + '.' + r['src_emit'], 'dst': r['dst_module'], 'dst_input_index': r['dst_input_index'],
                 'producer_family': ';'.join(sorted(pf)), 'consumer_family': ';'.join(sorted(cf)), 'family_verdict': v, 'verdict_reason': dr, 'operators': r['operators'],
                 'consumer_call': r['consumer_call'], 'dst_input_decl': idecl, 'evidence_tier': r['evidence_tier'], 'dropped_by': dr})
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
