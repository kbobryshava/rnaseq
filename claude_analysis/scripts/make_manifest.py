#!/usr/bin/env python3
"""Write reference/MANIFEST.json and reference/SHA256SUMS (checksums of the frozen text outputs; parquet copies and the manifest itself are excluded).
Usage: make_manifest.py [--date YYYY-MM-DD]   (the date is recorded only in MANIFEST.json, which is not part of SHA256SUMS)"""
import argparse, csv, datetime, hashlib, json, os, platform, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); REPO = os.path.dirname(ROOT); R = os.path.join(ROOT, 'reference')
PINNED = 'a1fcdddd3b826fe46eb46f0479f2ff8a7815af05'
ap = argparse.ArgumentParser(); ap.add_argument('--date', default=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')); a = ap.parse_args()
def sha(p):
    h = hashlib.sha256(); h.update(open(p, 'rb').read()); return h.hexdigest()
def git(*args):
    try: return subprocess.check_output(['git', '-C', REPO, *args], stderr=subprocess.DEVNULL).decode().strip()
    except Exception: return ''
def rows(p): return sum(1 for _ in csv.reader(open(p, encoding='utf-8', newline=''))) - 1
files = {}
for dp, _, fs in os.walk(R):
    for f in sorted(fs):
        if f in ('MANIFEST.json', 'SHA256SUMS') or f.endswith('.parquet'): continue
        p = os.path.join(dp, f); rel = os.path.relpath(p, R).replace(chr(92), '/')
        files[rel] = {'sha256': sha(p), 'bytes': os.path.getsize(p), **({'records': rows(p)} if f.endswith('.csv') else {})}
files = dict(sorted(files.items()))
open(os.path.join(R, 'SHA256SUMS'), 'w', newline='\n').write(''.join(f"{v['sha256']}  {k}\n" for k, v in files.items()))
cfg = open(os.path.join(REPO, 'nextflow.config'), encoding='utf-8').read()
import re
ver = re.search(r"manifest\s*\{.*?version\s*=\s*'([^']+)'", cfg, re.S).group(1)
raw = {f: sha(os.path.join(ROOT, 'data', 'raw', f)) for f in sorted(os.listdir(os.path.join(ROOT, 'data', 'raw'))) if f.endswith('_dag.html')}
try: import networkx, yaml; libs = {'networkx': networkx.__version__, 'pyyaml': yaml.__version__}
except Exception: libs = {}
counts = json.load(open(os.path.join(R, '_build_counts.json')))
val = json.load(open(os.path.join(R, 'validation.json')))
M = {'dataset': 'nf-core/rnaseq directed software-relationship reference dataset', 'pipeline': 'nf-core/rnaseq', 'pipeline_version': ver,
     'pipeline_commit_sha': PINNED, 'pipeline_commit_verified_in_checkout': bool(git('cat-file', '-t', PINNED) == 'commit'),
     'analysis_repository': 'https://github.com/kbobryshava/rnaseq (fork), branch claude/directed-software-analysis-3.27.0', 'analysis_base_commit': git('rev-parse', 'HEAD'),
     'generation_date_utc': a.date, 'python': platform.python_version(), 'libraries': libs, 'nextflow_for_preview_dags': '26.10.5 (preview only, run in WSL Ubuntu 22.04, Java 17)',
     'record_counts': counts, 'validation': {'pass': sum(v['status'] == 'PASS' for v in val), 'warn': sum(v['status'] == 'WARN' for v in val), 'fail': sum(v['status'] == 'FAIL' for v in val)},
     'preview_dag_inputs_sha256': raw, 'files': files, 'checksum_file': 'SHA256SUMS (verify with: cd claude_analysis/reference && sha256sum -c SHA256SUMS)'}
json.dump(M, open(os.path.join(R, 'MANIFEST.json'), 'w'), indent=1)
print('manifest:', len(files), 'files')
