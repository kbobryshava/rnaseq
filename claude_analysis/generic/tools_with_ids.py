#!/usr/bin/env python3
"""tools_with_ids.py - one table of every tool that has at least one identifier.

  python tools_with_ids.py [--dir RESULTS_DIR]        (default: current folder; needs tool_identifiers.csv, optionally biotools_match_report.csv)

Writes tools_with_ids.csv:
  tool                       most common spelling of the tool name
  tool_key                   matching key (lower case, letters and digits only)
  biotools_id                bio.tools ID of the tool itself (blank if none)
  biotools_url               https://bio.tools/<id>
  biotools_id_origin         where the ID came from: meta.yml | bio.tools API | bio.tools dump (+ evidence)
  reason_no_biotools_id      only when biotools_id is blank: why (see below)
  biotools_id_via_parent     only for names like star_align: the ID of the parent tool (star) that the merge step uses
  other_ids_available        every other identifier we hold, `kind:value` separated by ' ; ': bioconda, doi, pmid, pmcid, rrid
  n_other_ids                how many of those
  n_pipelines                in how many pipelines the tool is used
A tool is included when it has a bio.tools ID, a bioconda package, a DOI, a PubMed / PMC ID, an RRID or another ID. A homepage alone is a link, not an ID.
"""
import argparse, csv, os, re, sys

ap = argparse.ArgumentParser(); ap.add_argument('--dir', default='.'); a = ap.parse_args()
tf = os.path.join(a.dir, 'tool_identifiers.csv'); rf = os.path.join(a.dir, 'biotools_match_report.csv')
if not os.path.exists(tf): sys.exit('tool_identifiers.csv not found in ' + os.path.abspath(a.dir) + ' - run: python catalogue_run.py ids --lookup')
rows = list(csv.DictReader(open(tf, encoding='utf-8')))
report = {x['tool_key']: x for x in csv.DictReader(open(rf, encoding='utf-8'))} if os.path.exists(rf) else None
UTIL = {'cat', 'gzip', 'gunzip', 'tar', 'untar', 'unzip', 'sed', 'awk', 'gawk', 'grep', 'sort', 'cut', 'head', 'tail', 'echo', 'python', 'rbase', 'r', 'perl', 'bash', 'java', 'custom', 'zcat', 'xz', 'bzip2', 'pigz', 'wget', 'curl', 'ln', 'cp', 'mv', 'rm', 'mkdir', 'touch', 'wc', 'tee', 'join', 'paste'}


def others(r):
    out = []
    if r.get('bioconda_package'): out.append('bioconda:' + r['bioconda_package'])
    for x in re.split(r'[;|]', (r.get('doi', '') or '') + ';' + (r.get('publications', '') or '') + ';' + (r.get('other_ids', '') or '')):
        x = x.strip()
        if not x: continue
        m = re.search(r'10\.\d{4,9}/\S+', x)
        if m: out.append('doi:' + m.group(0).rstrip('.)]}'))
        elif x.lower().startswith(('pmid:', 'pmcid:')): out.append(x.lower())
        elif 'scr_' in x.lower(): out.append('rrid:' + re.search(r'SCR_\d+', x, re.I).group(0).upper())
        elif ':' in x and not x.lower().startswith('doi:'): out.append(x)
    return list(dict.fromkeys(out))


def origin(r):
    s = r.get('id_source', '')
    if s == 'meta.yml': return 'meta.yml (nf-core module metadata)'
    if s.startswith('bio.tools-exact'): return 'bio.tools API (' + s.replace('bio.tools-', '') + ')'
    if s.startswith('biotools-jsonl-'): return 'bio.tools dump (' + s[len('biotools-jsonl-'):] + ')'
    return s


out = []
for r in rows:
    oth = others(r)
    if not (r['biotools_id'] or oth): continue
    reason = ''
    if not r['biotools_id']:
        k = r['tool_key']
        if k in UTIL: reason = 'shell utility, deliberately not looked up on bio.tools (a name match would be a homonym)'
        elif r.get('parent_confidence') == 'operation-suffix': reason = f"name is an operation of the tool '{r['parent_key']}' ({r['operation_suffix']}); the merge uses the parent's ID"
        elif r.get('parent_confidence') == 'first-word-review': reason = f"name starts with the tool '{r['parent_key']}' but '{r['operation_suffix']}' is not a known operation - needs review"
        elif report is None: reason = 'matching against the bio.tools dump has not been run yet (run: python catalogue_run.py match)'
        elif k in report and report[k]['evidence'] == 'ambiguous': reason = 'ambiguous: several bio.tools records fit - ' + report[k]['candidates'][:200]
        elif k in report: reason = 'candidate found but not accepted (' + report[k]['evidence'] + ')'
        else: reason = 'no record in bio.tools matched this tool (searched by DOI, PubMed ID, RRID, link and name)'
    out.append({'tool': r['tool_name'], 'tool_key': r['tool_key'], 'biotools_id': r['biotools_id'], 'biotools_url': r['biotools_url'], 'biotools_id_origin': origin(r) if r['biotools_id'] else '',
                'reason_no_biotools_id': reason, 'biotools_id_via_parent': r.get('parent_biotools_id', '') if (not r['biotools_id'] and r.get('parent_confidence') == 'operation-suffix') else '',
                'other_ids_available': ' ; '.join(oth), 'n_other_ids': len(oth), 'n_pipelines': r.get('n_pipelines', '')})
out.sort(key=lambda x: (x['biotools_id'] == '', -int(x['n_pipelines'] or 0), x['tool_key']))
f = os.path.join(a.dir, 'tools_with_ids.csv')
with open(f, 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys()) if out else ['tool'], lineterminator='\n'); w.writeheader(); w.writerows(out)
nb = sum(1 for x in out if x['biotools_id'])
print(f'{len(out)} tools with at least one identifier of {len(rows)} -> {f}')
print(f'  with a bio.tools ID: {nb} | without one but with another ID: {len(out) - nb}')
import collections
print('  reasons for no bio.tools ID:', dict(collections.Counter((x['reason_no_biotools_id'].split(' - ')[0].split(':')[0][:60]) for x in out if not x['biotools_id']).most_common()))
