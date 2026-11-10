#!/usr/bin/env python3
"""catalogue_run.py - ONE file to analyse a folder of downloaded Nextflow pipelines (e.g. nfcore_catalogue_code) on a JupyterHub / any Linux terminal.

Expected layout:  <catalogue>/<pipeline>/<version>/main.nf   (e.g. nfcore_catalogue_code/abotyper/dev/main.nf)

Steps (run them in this order, from the terminal):
  python catalogue_run.py setup                 # installs pyyaml + networkx, downloads the analysis tools (a few MB) from GitHub
  python catalogue_run.py survey                # looks at the catalogue, writes survey.csv; changes nothing, runs nothing
  python catalogue_run.py run --limit 3         # test on 3 pipelines
  python catalogue_run.py run                   # all runnable pipelines (minutes)
  python catalogue_run.py report                # summary + software pairs that recur across pipelines
  python catalogue_run.py ids --lookup          # collect tool identifiers (bio.tools ID, bioconda package, DOI) -> tool_identifiers.csv
  python catalogue_run.py merge                 # ONE table of all pairs (verified rnaseq + candidates from the other pipelines) with a trust level and the number of pipelines per pair

Options: --catalogue DIR (default: current folder)  --tools DIR (default: ~/nfrel_tools)  --out DIR (default: <catalogue>/../../processed/nfrel_results if it exists, else ./nfrel_results)
Nothing is executed from the pipelines, no data is downloaded except the tools in `setup`. Only text files are read.
"""
import argparse, collections, csv, os, re, subprocess, sys

REPO = 'https://github.com/kbobryshava/rnaseq.git'
BRANCH = 'claude/directed-software-analysis-3.27.0'
UNNAMED = re.compile(r'^\s*workflow\s*\{', re.M)

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('step', nargs='?', choices=['setup', 'survey', 'run', 'report', 'ids', 'merge'])
ap.add_argument('--catalogue', default='.'); ap.add_argument('--tools', default=os.path.expanduser('~/nfrel_tools'))
ap.add_argument('--out'); ap.add_argument('--limit', type=int, default=0); ap.add_argument('--only', default=''); ap.add_argument('--jobs', type=int, default=4)
ap.add_argument('--timeout', type=int, default=900); ap.add_argument('--no-update', action='store_true'); ap.add_argument('--only-with-ids', choices=['biotools', 'any'], help='merge step: also write *_with_ids.csv with only pairs whose two tools both have a bio.tools ID (biotools) or any identifier (any)'); ap.add_argument('--lookup', action='store_true', help='ids step: also ask bio.tools (needs internet)')
a = ap.parse_args()
if not a.step: ap.print_help(); sys.exit(0)
cat = os.path.abspath(a.catalogue)
proc = os.path.join(cat, '..', '..', 'processed')
out = os.path.abspath(a.out or (os.path.join(proc, 'nfrel_results') if os.path.isdir(proc) else 'nfrel_results'))
G = os.path.join(a.tools, 'claude_analysis', 'generic')


def sh(*cmd, **kw):
    print('>', ' '.join(cmd), flush=True)
    return subprocess.run(cmd, **kw)


def libs_ok():
    try: import yaml, networkx; return True
    except ImportError: return False


def setup():
    if not libs_ok():
        sh(sys.executable, '-m', 'pip', 'install', '--user', '--quiet', 'pyyaml', 'networkx')
        print('libraries:', 'OK' if libs_ok() else 'STILL MISSING - run: pip install --user pyyaml networkx')
    else: print('libraries: OK')
    if os.path.isdir(os.path.join(G)) and a.no_update: print('tools: present (not updated)'); return
    if os.path.isdir(os.path.join(a.tools, '.git')):
        sh('git', '-C', a.tools, 'pull', '--ff-only', '--quiet')
        sh('git', '-C', a.tools, 'sparse-checkout', 'add', 'claude_analysis/reference/software_level')   # verified rnaseq reference, used by `merge`
    else:
        sh('git', 'clone', '--quiet', '--filter=blob:none', '--no-checkout', '--depth', '1', '--branch', BRANCH, REPO, a.tools)
        sh('git', '-C', a.tools, 'sparse-checkout', 'set', 'claude_analysis/scripts', 'claude_analysis/generic', 'claude_analysis/reference/software_level')
        sh('git', '-C', a.tools, 'checkout', '--quiet')
    print('tools:', 'OK ' + G if os.path.exists(os.path.join(G, 'nfrel.py')) else 'MISSING - check internet access to github.com')


def pipelines():
    rows = []
    for p in sorted(os.listdir(cat)):
        pd = os.path.join(cat, p)
        if not os.path.isdir(pd) or p.startswith('.'): continue
        subs = sorted(d for d in os.listdir(pd) if os.path.isdir(os.path.join(pd, d)) and not d.startswith('.'))
        for v in subs or ['']:
            d = os.path.join(pd, v) if v else pd
            row = {'pipeline': p, 'version': v, 'path': d, 'has_main_nf': os.path.exists(os.path.join(d, 'main.nf')), 'unnamed_workflow': False, 'dsl1': False, 'n_module_mainnf': 0, 'n_subworkflow_nf': 0,
                   'has_workflows_dir': os.path.isdir(os.path.join(d, 'workflows')), 'has_config': os.path.exists(os.path.join(d, 'nextflow.config')), 'has_git': os.path.isdir(os.path.join(d, '.git')), 'logs': ''}
            if row['has_main_nf']:
                row['unnamed_workflow'] = bool(UNNAMED.search(open(os.path.join(d, 'main.nf'), encoding='utf-8', errors='replace').read()))
            for kind, key in (('modules', 'n_module_mainnf'), ('subworkflows', 'n_subworkflow_nf')):
                for dp, _, fs in os.walk(os.path.join(d, kind)):
                    row[key] += sum(1 for f in fs if f.endswith('.nf'))
            row['logs'] = ';'.join(f for f in os.listdir(d) if f.endswith('.log')) if os.path.isdir(d) else ''
            if not row['has_main_nf']: row['status'] = 'no main.nf' + (' (only a download log)' if row['logs'] else '')
            elif not row['unnamed_workflow']:
                _t = open(os.path.join(d, 'main.nf'), encoding='utf-8', errors='replace').read()
                is_dsl1 = bool(re.search(r'^[ \t]*process[ \t]+\w+[ \t]*\{', _t, re.M) and re.search(r'\binto\b', _t))
                row['status'] = 'runnable' if is_dsl1 else 'main.nf has no unnamed workflow {} block and no processes (different entry)'
                row['dsl1'] = is_dsl1
            elif not (row['has_workflows_dir'] or row['n_module_mainnf'] or row['n_subworkflow_nf']): row['status'] = 'no workflows/modules/subworkflows'
            else: row['status'] = 'runnable'
            rows.append(row)
    return rows


def survey():
    rows = pipelines()
    os.makedirs(out, exist_ok=True)
    f = os.path.join(out, 'survey.csv')
    with open(f, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator='\n'); w.writeheader(); w.writerows(rows)
    c = collections.Counter(r['status'] for r in rows)
    print(f'\ncatalogue: {cat}\n{len(rows)} pipeline folders ({len({r["pipeline"] for r in rows})} distinct pipelines); versions: {dict(collections.Counter(r["version"] for r in rows).most_common(5))}')
    for k, v in c.most_common(): print(f'  {v:4d}  {k}')
    print('modules total:', sum(r['n_module_mainnf'] for r in rows), '| subworkflows total:', sum(r['n_subworkflow_nf'] for r in rows))
    bad = [r for r in rows if r['status'] != 'runnable']
    if bad: print('\nnot runnable (first 15):'); [print('  ', r['pipeline'] + '/' + r['version'], '->', r['status']) for r in bad[:15]]
    print('\nwritten:', f)


def run():
    if not os.path.exists(os.path.join(G, 'batch_nfrel.py')): sys.exit('tools missing - run: python catalogue_run.py setup')
    if not libs_ok(): sys.exit('pyyaml/networkx missing - run: python catalogue_run.py setup')
    cmd = [sys.executable, os.path.join(G, 'batch_nfrel.py'), '--root', cat, '--out', out, '--jobs', str(a.jobs), '--timeout', str(a.timeout)]
    if a.limit: cmd += ['--limit', str(a.limit)]
    if a.only: cmd += ['--only', a.only]
    sys.exit(sh(*cmd).returncode)


def report():
    f = os.path.join(out, 'batch_summary.csv')
    if not os.path.exists(f): sys.exit('no results yet - run: python catalogue_run.py run')
    rows = list(csv.DictReader(open(f, encoding='utf-8')))
    st = collections.Counter(r['status'] for r in rows)
    ok = [r for r in rows if r['status'] == 'OK']
    pairs = collections.defaultdict(lambda: {'pipelines': set(), 'n_edges': 0})
    for r in ok:
        sf = os.path.join(out, r['pipeline'], 'reference', 'software_relationships.csv')
        if not os.path.exists(sf): continue
        for x in csv.DictReader(open(sf, encoding='utf-8')):
            if x['category'] == 'Algorithmic_supported' and x['is_self_loop'] != 'True':
                k = (x['source_software'], x['target_software']); pairs[k]['pipelines'].add(r['pipeline']); pairs[k]['n_edges'] += int(x['n_live_edges'])
    pf = os.path.join(out, 'software_pairs_across_pipelines.csv')
    ranked = sorted(pairs.items(), key=lambda kv: -len(kv[1]['pipelines']))
    WEAK = {'multiqc', 'gunzip', 'gzip', 'cat', 'untar', 'tar', 'xz', 'unzip', 'bzip2', 'pigz', 'gawk', 'sed', 'python', 'r-base', 'coreutils', 'wget', 'curl', 'custom'}
    with open(pf, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh, lineterminator='\n'); w.writerow(['source_software', 'target_software', 'n_pipelines', 'n_edges_total', 'involves_utility_or_reporting', 'example_pipelines'])
        for (s, t), v in ranked: w.writerow([s, t, len(v['pipelines']), v['n_edges'], s in WEAK or t in WEAK, ';'.join(sorted(v['pipelines'])[:5])])
    core = [kv for kv in ranked if kv[0][0] not in WEAK and kv[0][1] not in WEAK]
    print(f'pipelines analysed: {dict(st)}')
    if ok:
        print(f"edges per pipeline: median {sorted(int(r['process_edges']) for r in ok)[len(ok)//2]}, max {max(int(r['process_edges']) for r in ok)}; unreviewed modules median {sorted(int(r['unreviewed_modules']) for r in ok)[len(ok)//2]}")
    bad = [r for r in rows if r['status'] != 'OK']
    if bad: print('\nproblems (first 10):'); [print('  ', r['pipeline'], r['status'], r['error'][:90]) for r in bad[:10]]
    print(f'\n{len(ranked)} distinct software pairs ({len(core)} without utilities/MultiQC). Most common across pipelines (analysis tools only):')
    for (s, t), v in core[:15]: print(f"  {len(v['pipelines']):4d} pipelines   {s} -> {t}")
    print('\nwritten:', pf, '\n        ', f)


def ids():
    cmd = [sys.executable, os.path.join(G, 'tool_ids.py'), '--catalogue', cat, '--results', out, '--out', out] + (['--lookup'] if a.lookup else [])
    sys.exit(sh(*cmd).returncode)


def merge():
    ref = os.path.join(a.tools, 'claude_analysis', 'reference', 'software_level', 'software_relationships_all.csv')
    sys.exit(sh(sys.executable, os.path.join(G, 'merge_pairs.py'), '--results', out, '--rnaseq-reference', ref, *(['--tool-ids', os.path.join(out, 'tool_identifiers.csv')] if os.path.exists(os.path.join(out, 'tool_identifiers.csv')) else []), *(['--only-with-ids', a.only_with_ids] if a.only_with_ids else [])).returncode)


{'setup': setup, 'survey': survey, 'run': run, 'report': report, 'ids': ids, 'merge': merge}[a.step]()
