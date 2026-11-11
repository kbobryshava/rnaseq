#!/usr/bin/env python3
"""Self-test of the generic tool on the synthetic mini pipeline (no network, no Nextflow).  python generic/tests/test_generic.py"""
import csv, os, subprocess, sys, tempfile

H = os.path.dirname(os.path.abspath(__file__)); G = os.path.dirname(H)
out = tempfile.mkdtemp(prefix='nfrel_test_')
cur = os.path.join(out, 'decisions.csv')
open(cur, 'w', newline='').write('source_software,target_software,decision,evidence\nfastp,HISAT2,Gold,mini.nf FASTP.out.reads -> HISAT2_ALIGN\nQualimap,featureCounts (Subread),Negative_verified,both only read the sorted BAM\n')
cmd = [sys.executable, os.path.join(G, 'nfrel.py'), '--repo', os.path.join(H, 'mini_pipeline'), '--out', out, '--software-map', os.path.join(G, 'pipeline_template.yaml'), '--curation', cur]
r = subprocess.run(cmd, capture_output=True, text=True)
assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
rows = {(x['source_software'], x['target_software']): x for x in csv.DictReader(open(os.path.join(out, 'reference', 'software_relationships.csv'), encoding='utf-8'))}
exp = {('fastp', 'HISAT2'): 'Gold', ('HISAT2', 'SAMtools'): 'Algorithmic_supported', ('SAMtools', 'Qualimap'): 'Algorithmic_supported', ('SAMtools', 'featureCounts (Subread)'): 'Algorithmic_supported',
       ('Qualimap', 'featureCounts (Subread)'): 'Negative_verified', ('featureCounts (Subread)', 'Qualimap'): 'Parallel_co_use'}
bad = {k: (rows.get(k, {}).get('category'), v) for k, v in exp.items() if rows.get(k, {}).get('category') != v}
assert not bad, bad
assert not any(k[0] == 'Qualimap' and k[1] == 'SAMtools' for k in rows), 'reverse direction must not appear'
val = {x['check']: x['status'] for x in __import__('json').load(open(os.path.join(out, 'reference', 'validation.json')))}
assert 'FAIL' not in val.values(), val
print('generic self-test OK ->', out)

# ---- old-style (DSL1) pipeline: edges come from `into` / `from`, never from source order or the shared reference channel
out2 = tempfile.mkdtemp(prefix='nfrel_dsl1_test_')
r = subprocess.run([sys.executable, os.path.join(G, 'nfrel.py'), '--repo', os.path.join(H, 'mini_dsl1'), '--out', out2], capture_output=True, text=True)
assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]
pe = {(x['src_instance'], x['dst_instance']) for x in csv.DictReader(open(os.path.join(out2, 'data', 'processed', 'process_edges.csv'), encoding='utf-8'))}
want = {('trim', 'align'), ('trim', 'qc'), ('align', 'call'), ('qc', 'report'), ('call', 'report')}
assert pe == want, (sorted(pe ^ want))
print('dsl1 self-test OK ->', out2)
