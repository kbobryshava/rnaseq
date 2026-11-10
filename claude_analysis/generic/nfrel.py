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
run(py, '-I', os.path.join(S, 'nf_static_analyzer.py'), '--root', repo, '--out', os.path.join(out, 'data', 'processed'))
run(py, os.path.join(S, 'build_datasets.py'), '--repo', repo, '--out', out, '--profile', 'generic', *(['--software-map', os.path.abspath(a.software_map)] if a.software_map else []))
sys.exit(subprocess.call([py, os.path.join(H, 'generic_reference.py'), '--out', out, '--repo', repo, *(['--curation', os.path.abspath(a.curation)] if a.curation else [])]))
