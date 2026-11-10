#!/usr/bin/env python3
"""nfrel - directed software relationships from any Nextflow DSL2 pipeline (static analysis).

  python nfrel.py --repo /path/to/pipeline --out /path/to/output [--software-map map.yaml] [--previews DIR_WITH_*_dag.html] [--curation decisions.csv]

Steps: static channel-provenance analysis -> process/software tables (profile=generic) -> reference/ tables + validation + manifest.
Needs Python >= 3.10, pyyaml, networkx.  No Nextflow, no data download, no pipeline execution (preview DAGs are optional).
"""
import argparse, glob, os, shutil, subprocess, sys

H = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(os.path.dirname(H), 'scripts')
ap = argparse.ArgumentParser()
ap.add_argument('--repo', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--software-map'); ap.add_argument('--previews'); ap.add_argument('--curation'); ap.add_argument('--entry', default='main.nf')
a = ap.parse_args()
repo, out = os.path.abspath(a.repo), os.path.abspath(a.out)
if not os.path.exists(os.path.join(repo, a.entry)): sys.exit(a.entry + ' not found in ' + repo)
for d in ('data/raw', 'data/processed', 'data/graphs'): os.makedirs(os.path.join(out, d), exist_ok=True)
if a.previews:
    for f in glob.glob(os.path.join(a.previews, '*_dag.html')): shutil.copy(f, os.path.join(out, 'data', 'raw'))


def run(*cmd):
    print('>', ' '.join(os.path.basename(c) if os.path.exists(c) else c for c in cmd), flush=True)
    subprocess.run(cmd, check=True)


py = sys.executable
import re
_main = open(os.path.join(repo, a.entry), encoding='utf-8', errors='replace').read()
if not re.search(r'^\s*workflow\s*\{', _main, re.M) and re.search(r'^[ \t]*process[ \t]+\w+[ \t]*\{', _main, re.M):
    print('old-style (DSL1) pipeline: using dsl1_analyzer.py')       # no unnamed workflow block: processes are wired with `from` / `into`
    run(py, '-I', os.path.join(S, 'dsl1_analyzer.py'), '--root', repo, '--out', os.path.join(out, 'data', 'processed'), '--entry', a.entry)
else:
    run(py, '-I', os.path.join(S, 'nf_static_analyzer.py'), '--root', repo, '--out', os.path.join(out, 'data', 'processed'))
import json
g = json.load(open(os.path.join(out, 'data', 'processed', 'static_graph.json')))
if not g['edges']:     # e.g. pipelines made of independent processes: a valid result, nothing to tabulate
    os.makedirs(os.path.join(out, 'reference'), exist_ok=True)
    json.dump({'no_edges': True, 'process_instances': sum(1 for i in g['instances'] if i['kind'] == 'process'), 'counts': {'process_edges': {}, 'software_pairs': {}}, 'unreviewed_modules': []}, open(os.path.join(out, 'reference', 'manifest.json'), 'w'))
    json.dump([], open(os.path.join(out, 'reference', 'validation.json'), 'w'))
    print('NO_EDGES: %d process instances but no data flows between them' % sum(1 for i in g['instances'] if i['kind'] == 'process')); sys.exit(0)
run(py, os.path.join(S, 'build_datasets.py'), '--repo', repo, '--out', out, '--profile', 'generic', *(['--software-map', os.path.abspath(a.software_map)] if a.software_map else []))
sys.exit(subprocess.call([py, os.path.join(H, 'generic_reference.py'), '--out', out, '--repo', repo, *(['--curation', os.path.abspath(a.curation)] if a.curation else [])]))
