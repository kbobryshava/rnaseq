"""Payload checks for extracted process edges (shared by build_datasets.py and the audit).
For one evidence record (dict with src_emit, src_output_decl, dst_input_decl, dst_module, dst_instance, channel_trail, consumer_call, src_module)
return (verdict, reason). Verdicts: compatible | unknown-producer-family | INCOMPATIBLE (heuristic, noisy for direct edges: never used to reject)
| PROJECTION-DROPPED | MULTIMAP-SPLIT | INFEASIBLE-CALLSITE-CONSTANT (the last three reject the edge). The rules encode three source-verified
false-positive mechanisms of a union-semantics channel analysis; see audit/AUDIT_REPORT.md section 5."""
import re, os
REJECT_VERDICTS = {'PROJECTION-DROPPED', 'MULTIMAP-SPLIT', 'INFEASIBLE-CALLSITE-CONSTANT'}
# pipeline-specific rules, set by build_datasets.py from the profile / software-map file:
#   CALLSITE_INFEASIBLE = [{'dst_suffix': 'SUBWF:PROCESS', 'reason': '...'}]  (a subworkflow called with a literal argument that disables this branch)
CALLSITE_INFEASIBLE = []
MULTIMAP_NOTE = 'a multiMap on the channel path separates the bam and index outputs; the analyzer unions the branches'
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
REPO = None   # set by payload_verdict(repo=...)
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


def payload_verdict(r, repo):
    global REPO
    REPO = repo
    r = dict(r, src_emit=r.get('src_emit') or '', src_output_decl=r.get('src_output_decl') or '', dst_input_decl=r.get('dst_input_decl') or '')   # outputs used positionally (.out[0]) have no emit/declaration
    pf = fams(r['src_emit'] + ' ' + r['src_output_decl'])
    idecl = r['dst_input_decl']; sl = slots(idecl); cs = ' '.join(sl) + ' ' + idecl
    cf = fams(cs)
    if any(x in ('input', 'file', 'files') for x in sl): cf |= {'bam', 'fastq', 'fasta', 'gtf', 'bed', 'counts'}
    if any(x in ('input_index', 'index') for x in sl): cf |= {'bai'}
    if any(x == 'reads' for x in sl) and r['dst_module'] in ('SALMON_QUANT', 'RSEM_CALCULATEEXPRESSION', 'SENTIEON_RSEMCALCULATEEXPRESSION', 'PICARD_MARKDUPLICATES'): cf |= {'bam'}   # alignment-based quantification
    if any(x in ('intervals', 'srbam', 'lrbam') for x in sl): cf |= {'bam'}
    if r['dst_module'] in ('FQ_LINT', 'BBMAP_BBSPLIT', 'SORTMERNA', 'RIBODETECTOR', 'BOWTIE2_ALIGN') and 'fastq' in pf: cf |= {'fastq'}
    dr = dropped_in_trail(r, pf)
    if not dr:   # closures written inline in the consumer call
        try:
            txt = statement(r['consumer_call'])
            for m in re.finditer(r'\{\s*([\w\s,_]+?)\s*->', txt):
                for prm in [x.strip() for x in m.group(1).split(',')]:
                    nm = prm.lstrip('_').lower()
                    if prm.startswith('_') and prm != '_meta' and any(fam in pf and any(k in nm for k in keys) for fam, keys in DROP.items()): dr = r['consumer_call'] + ' (inline) drops ' + prm
        except Exception: pass
    multimap = any(st.get('var', '').startswith('map_filtered') or 'multiMap' in st.get('operators', []) for st in r['channel_trail'])
    hit = next((x for x in CALLSITE_INFEASIBLE if r['dst_instance'].endswith(x['dst_suffix'])), None)
    if hit: v = 'INFEASIBLE-CALLSITE-CONSTANT'; dr = hit['reason']
    elif dr: v = 'PROJECTION-DROPPED'
    elif not pf: v = 'unknown-producer-family'
    elif pf & cf: v = 'compatible'
    else: v = 'INCOMPATIBLE'
    if v == 'INCOMPATIBLE' and multimap and 'bai' in pf: v = 'MULTIMAP-SPLIT'; dr = MULTIMAP_NOTE
    return v, dr, pf, cf
