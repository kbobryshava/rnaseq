#!/usr/bin/env python3
"""Run nfrel on every Nextflow pipeline found under a folder and write one summary table.

  python batch_nfrel.py --root DOWNLOADS --out RESULTS [--jobs 4] [--timeout 900] [--list-only]

A folder counts as a pipeline when it has a main.nf that contains an unnamed `workflow {` block AND a modules/ or workflows/ or subworkflows/ folder,
and it is not itself inside another pipeline's modules/ or subworkflows/ folder. Each pipeline gets RESULTS/<name>/ ; the summary is RESULTS/batch_summary.csv.
Failures never stop the batch; the error text is kept in the summary and in RESULTS/<name>/nfrel.log.
"""
import argparse, concurrent.futures as cf, csv, json, os, re, subprocess, sys, time

H = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--root', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--limit', type=int, default=0, help='analyse only the first N pipelines (for a test run)'); ap.add_argument('--only', default='', help='only pipelines whose path contains this text')
ap.add_argument('--jobs', type=int, default=2); ap.add_argument('--timeout', type=int, default=900); ap.add_argument('--list-only', action='store_true')
a = ap.parse_args()
UNNAMED = re.compile(r'^\s*workflow\s*\{', re.M)
SKIP_PARENTS = ('modules', 'subworkflows', 'tests', 'test', '.git', 'work')


def find_pipelines(root):
    found = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in ('.git', 'work', 'node_modules')]
        if 'main.nf' not in fn: continue
        rel = os.path.relpath(dp, root).replace('\\', '/').split('/')
        if any(p in SKIP_PARENTS for p in rel): dn[:] = []; continue
        try: txt = open(os.path.join(dp, 'main.nf'), encoding='utf-8', errors='replace').read()
        except OSError: continue
        if UNNAMED.search(txt) and any(os.path.isdir(os.path.join(dp, d)) for d in ('workflows', 'subworkflows', 'modules')):
            found.append(dp); dn[:] = [d for d in dn if d not in ('modules', 'subworkflows', 'workflows', 'conf', 'tests')]
    return sorted(found)


def run_one(repo):
    name = os.path.relpath(repo, a.root).replace('\\', '/').strip('./').replace('/', '__') or os.path.basename(repo)
    out = os.path.join(a.out, name); os.makedirs(out, exist_ok=True)
    t0 = time.time(); row = {'pipeline': name, 'path': repo, 'status': '', 'seconds': '', 'process_instances': '', 'process_edges': '', 'supported_edges': '', 'software_pairs': '', 'unreviewed_modules': '', 'warnings': '', 'error': ''}
    try:
        r = subprocess.run([sys.executable, os.path.join(H, 'nfrel.py'), '--repo', repo, '--out', out], capture_output=True, text=True, timeout=a.timeout)
        open(os.path.join(out, 'nfrel.log'), 'w', encoding='utf-8').write(r.stdout + '\n' + r.stderr)
        if r.returncode != 0:
            row['status'] = 'FAILED'; row['error'] = (r.stderr.strip().splitlines() or r.stdout.strip().splitlines() or ['?'])[-1][:300]
        else:
            m = json.load(open(os.path.join(out, 'reference', 'manifest.json'))); v = json.load(open(os.path.join(out, 'reference', 'validation.json')))
            pe = m['counts']['process_edges']; sp = m['counts']['software_pairs']
            g = json.load(open(os.path.join(out, 'data', 'processed', 'static_graph.json')))
            row.update(status='OK', process_instances=sum(1 for i in g['instances'] if i['kind'] == 'process'), process_edges=sum(pe.values()), supported_edges=pe.get('algorithmic_supported', 0),
                       software_pairs=sum(sp.values()), unreviewed_modules=len(m['unreviewed_modules']), warnings=sum(1 for x in v if x['status'] == 'WARN'))
            row['error'] = ('unresolved statements: %d' % len(g['unresolved'])) if g['unresolved'] else ''
    except subprocess.TimeoutExpired: row['status'] = 'TIMEOUT'
    except Exception as ex: row['status'] = 'ERROR'; row['error'] = str(ex)[:300]
    row['seconds'] = round(time.time() - t0, 1)
    return row


pipes = find_pipelines(a.root)
if a.only: pipes = [p for p in pipes if a.only in p]
if a.limit: pipes = pipes[:a.limit]
print(len(pipes), 'pipelines found under', a.root)
if a.list_only:
    print('\n'.join(pipes)); sys.exit(0)
os.makedirs(a.out, exist_ok=True); rows = []
with cf.ThreadPoolExecutor(max_workers=a.jobs) as ex:
    for i, row in enumerate(ex.map(run_one, pipes), 1):
        rows.append(row); print(f"[{i}/{len(pipes)}] {row['status']:8} {row['pipeline']}  edges={row['process_edges']} {row['error'][:80]}", flush=True)
cols = list(rows[0].keys()) if rows else ['pipeline']
with open(os.path.join(a.out, 'batch_summary.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=cols, lineterminator='\n'); w.writeheader(); w.writerows(rows)
print('summary:', os.path.join(a.out, 'batch_summary.csv'), '|', {s: sum(1 for r in rows if r['status'] == s) for s in sorted({r['status'] for r in rows})})
