#!/usr/bin/env python3
"""biotools_match.py - find bio.tools IDs, offline, for the tools that still have none, using a local dump of bio.tools (JSON lines).

  python biotools_match.py --tools tool_identifiers.csv --jsonl biotools_raw.jsonl [--out DIR] [--no-name-only]

Input : tool_identifiers.csv from tool_ids.py, and a bio.tools dump with one tool record per line (fields as in the bio.tools API:
        biotoolsID, name, homepage, publication[{doi,pmid,pmcid}], otherID[{value,type}], link[{url}], documentation[{url}]).
        A line may also be {"list": [...]} or wrap the record under some key; records are found by their `biotoolsID` field.
Every identifier and link we have for the tool is compared with the record:
  doi     DOIs of the tool (meta.yml DOI, publications, other IDs)   vs  publication[].doi, DOIs in otherID, DOIs inside urls
  pmid    PubMed IDs of the tool's publications                       vs  publication[].pmid
  pmcid   PMC IDs                                                     vs  publication[].pmcid
  rrid    RRIDs of the tool (other IDs)                               vs  otherID entries
  url     homepage / documentation of the tool, normalised            vs  homepage, documentation[].url, link[].url   (a bare hosting site such as github.com never counts)
  name    tool key, name variants and bioconda package name           vs  record name and biotoolsID
Strength, strongest first: [doi, pmid, pmcid, rrid]  >  url  >  name.  The evidence label lists everything that agreed, e.g. `doi+url+name`.
Selection: among the records with strong evidence, the one whose name also agrees wins; if only one record has strong evidence it wins even when
the names differ (a DOI beats a name); several records and no name tie-break = `ambiguous` (not accepted, listed in the report). If there is no
strong evidence the same rule is applied to url evidence, and only then to a unique exact name.
Writes (OUT defaults to the folder of --tools): tool_identifiers.csv updated in place (backup tool_identifiers.before_jsonl.csv), biotools_match_report.csv.
Nothing is downloaded.
"""
import argparse, collections, csv, json, os, re, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tool_ids import key, resolve_parents, NO_NAME_LOOKUP, GENERIC, strip_pkg_prefix

DOI_RX = re.compile(r'10\.\d{4,9}/[^\s"<>,;]+', re.I)
STRONG = ('doi', 'pmid', 'pmcid', 'rrid')
ORDER = ('doi', 'pmid', 'pmcid', 'rrid', 'url', 'name')


GENERIC_HOSTS = {'github.com', 'gitlab.com', 'bitbucket.org', 'sourceforge.net', 'bioconductor.org', 'cran.r-project.org', 'r-project.org', 'pypi.org', 'anaconda.org', 'bioconda.github.io', 'hub.docker.com', 'docker.com', 'zenodo.org', 'figshare.com', 'ncbi.nlm.nih.gov', 'ebi.ac.uk', 'galaxyproject.org', 'usegalaxy.org', 'nf-co.re', 'doi.org', 'google.com', 'sites.google.com', 'github.io', 'readthedocs.io', 'readthedocs.org'}


def norm_doi(x):
    x = (x or '').strip().lower()
    x = re.sub(r'^(https?://(dx\.)?doi\.org/|doi:\s*)', '', x)
    m = DOI_RX.search(x)
    return m.group(0).rstrip('.)]}') if m else ''


def norm_url(u):
    """host + path, lower case, without scheme / www / trailing slash / .git / index page / query; '' for a bare host"""
    u = (u or '').strip().lower()
    if not u: return ''
    u = re.sub(r'^[a-z]+://', '', u)
    u = re.sub(r'^www\.', '', u)
    u = re.split(r'[?#]', u)[0].rstrip('/')
    u = re.sub(r'(/index\.(html?|php))$', '', u)
    u = re.sub(r'\.git$', '', u)
    if '/' not in u and u in GENERIC_HOSTS: return ''   # a bare hosting site (github.com ...) identifies nothing; a bare tool site (htslib.org) does
    return u


def norm_rrid(x):
    m = re.search(r'scr_\d+', (x or '').lower())
    return m.group(0) if m else ''


def records(obj):
    """yield every dict that has a biotoolsID, wherever it is nested"""
    if isinstance(obj, dict):
        if obj.get('biotoolsID'): yield obj; return
        for v in obj.values(): yield from records(v)
    elif isinstance(obj, list):
        for v in obj: yield from records(v)


def record_ids(rec):
    """-> {kind: set(values)} for doi / pmid / pmcid / rrid / url"""
    d = collections.defaultdict(set)
    for p in rec.get('publication') or []:
        if not isinstance(p, dict): continue
        if norm_doi(p.get('doi')): d['doi'].add(norm_doi(p.get('doi')))
        if p.get('pmid'): d['pmid'].add(str(p['pmid']).strip())
        if p.get('pmcid'): d['pmcid'].add(str(p['pmcid']).strip().lower())
    for o in rec.get('otherID') or []:
        if not isinstance(o, dict): continue
        v = str(o.get('value', ''))
        if norm_doi(v): d['doi'].add(norm_doi(v))
        if norm_rrid(v): d['rrid'].add(norm_rrid(v))
    for k in ('link', 'documentation'):
        for x in rec.get(k) or []:
            if isinstance(x, dict):
                if norm_url(x.get('url')): d['url'].add(norm_url(x['url']))
                if norm_doi(x.get('url')): d['doi'].add(norm_doi(x['url']))
    for u in (rec.get('homepage'),):
        if norm_url(u): d['url'].add(norm_url(u))
        if norm_doi(u): d['doi'].add(norm_doi(u))
    return d


def tool_ids_of(row):
    d = collections.defaultdict(set)
    for col in ('doi', 'publications', 'other_ids'):
        for x in re.split(r'[;|]', row.get(col, '') or ''):
            x = x.strip()
            if not x: continue
            if norm_doi(x): d['doi'].add(norm_doi(x))
            if x.lower().startswith('pmid:'): d['pmid'].add(x[5:].strip())
            if x.lower().startswith('pmcid:'): d['pmcid'].add(x[6:].strip().lower())
            if norm_rrid(x): d['rrid'].add(norm_rrid(x))
    for col in ('homepage', 'documentation'):
        for x in re.split(r'[;|\s]+', row.get(col, '') or ''):
            if norm_url(x): d['url'].add(norm_url(x))
    return d


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tools', required=True); ap.add_argument('--jsonl', required=True); ap.add_argument('--out'); ap.add_argument('--no-name-only', action='store_true', help='accept matches that rest on identifiers or links only, never on a name alone')
    a = ap.parse_args()
    out = a.out or os.path.dirname(os.path.abspath(a.tools))
    info = {}; idx = {k: collections.defaultdict(set) for k in STRONG + ('url',)}; by_name = collections.defaultdict(set); n_lines = 0; bad = 0
    with open(a.jsonl, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            n_lines += 1
            try: obj = json.loads(line)
            except Exception: bad += 1; continue
            for rec in records(obj):
                bid = rec['biotoolsID']
                info[bid] = {'name': rec.get('name', ''), 'homepage': rec.get('homepage', '')}
                for kind, vals in record_ids(rec).items():
                    for v in vals: idx[kind][v].add(bid)
                for k in {key(rec.get('name', '')), key(bid)}:
                    if k: by_name[k].add(bid)
    print(f'bio.tools dump: {n_lines} lines ({bad} unreadable), {len(info)} tool records; index sizes: ' + ', '.join(f'{k} {len(v)}' for k, v in idx.items()))
    if not info: sys.exit('no records with a biotoolsID found - is this the right file? first characters: ' + open(a.jsonl, encoding='utf-8', errors='replace').read(200))
    rows = list(csv.DictReader(open(a.tools, encoding='utf-8'))); fields = list(rows[0].keys())
    bk = os.path.join(out, 'tool_identifiers.before_jsonl.csv')
    if not os.path.exists(bk): shutil.copy(a.tools, bk)   # kept from the FIRST run, so a re-run never overwrites the real 'before'
    for c in ('match_evidence', 'match_doi', 'match_candidates'):
        if c not in fields: fields.append(c)
    report = []; counts = collections.Counter()
    for r in rows:
        r.setdefault('match_evidence', ''); r.setdefault('match_doi', ''); r.setdefault('match_candidates', '')
        if r['biotools_id'] or r['tool_key'] in NO_NAME_LOOKUP: continue
        names = {r['tool_key']} | {key(n) for n in (r.get('name_variants') or '').split('|') if n.strip()} | {key(strip_pkg_prefix(n)) for n in (r.get('name_variants') or '').split('|') + [r.get('bioconda_package', '')] if n.strip()} | {key(r.get('bioconda_package', ''))}
        names.discard('')
        mine = tool_ids_of(r)
        cand = collections.defaultdict(lambda: collections.defaultdict(set))   # biotoolsID -> kind -> matched values
        for kind in STRONG + ('url',):
            for v in mine.get(kind, ()):
                for bid in idx[kind].get(v, ()): cand[bid][kind].add(v)
        for bid in set(cand) | set().union(*[by_name.get(k, set()) for k in names]):
            if {key(info[bid]['name']), key(bid)} & names: cand[bid]['name'].add('name')
        def pick(kinds):
            pool = {b: k for b, k in cand.items() if set(k) & set(kinds)}
            if not pool: return None, ''
            named = [b for b, k in pool.items() if 'name' in k]
            if len(named) == 1: return named[0], ''
            if len(named) > 1: return None, 'ambiguous'
            if len(pool) == 1: return next(iter(pool)), ''
            return None, 'ambiguous'
        chosen, amb = pick(STRONG)
        if not chosen and not amb: chosen, amb = pick(('url',))
        generic_only = all(k in GENERIC for k in names)   # a name like `filter` or `merge` alone is never enough
        if not chosen and not amb and not a.no_name_only and not generic_only:
            nm = {b: k for b, k in cand.items() if 'name' in k}
            if len(nm) == 1: chosen = next(iter(nm))
            elif len(nm) > 1: amb = 'ambiguous'
        evidence = ''
        if chosen: evidence = '+'.join(k for k in ORDER if k in cand[chosen])
        elif amb: evidence = 'ambiguous'
        counts[evidence or 'no-match'] += 1
        if chosen:
            r['biotools_id'] = chosen; r['biotools_url'] = 'https://bio.tools/' + chosen; r['id_source'] = 'biotools-jsonl-' + evidence
            r['match_evidence'] = evidence; r['match_doi'] = ';'.join(sorted(cand[chosen].get('doi', set())))
            if not r.get('homepage'): r['homepage'] = info[chosen]['homepage']
        if evidence:
            r['match_candidates'] = ';'.join(sorted(cand))[:300]
            report.append({'tool_key': r['tool_key'], 'tool_name': r['tool_name'], 'evidence': evidence, 'accepted': bool(chosen), 'chosen_biotools_id': chosen or '', 'chosen_name': info[chosen]['name'] if chosen else '',
                           'candidates': ';'.join(f"{b} ({info[b]['name']}: {'+'.join(k for k in ORDER if k in cand[b])})" for b in sorted(cand))[:500], 'tool_ids_and_links': ';'.join(f'{k}={sorted(v)[0]}' for k, v in mine.items() if v), 'name_variants': r.get('name_variants', '')})
    for r in rows:
        for c in ('parent_key', 'parent_biotools_id', 'operation_suffix', 'parent_confidence'): r[c] = ''
    resolve_parents(rows)   # a tool that just got an ID can be the parent of operation-suffixed names (star_align -> star)
    for c in ('parent_key', 'parent_biotools_id', 'operation_suffix', 'parent_confidence'):
        if c not in fields: fields.append(c)
    with open(os.path.join(out, 'tool_identifiers.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction='ignore', lineterminator='\n'); w.writeheader(); w.writerows(rows)
    rf = os.path.join(out, 'biotools_match_report.csv')
    with open(rf, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['tool_key', 'tool_name', 'evidence', 'accepted', 'chosen_biotools_id', 'chosen_name', 'candidates', 'tool_ids_and_links', 'name_variants'], lineterminator='\n'); w.writeheader(); w.writerows(report)
    was = lambda r: bool(r['biotools_id']) and not r['id_source'].startswith('biotools-jsonl')   # had an ID before any dump matching (meta.yml or API lookup)
    npipe = lambda r: int(r.get('n_pipelines') or 0)
    summ = [('tools in the table', len(rows), sum(npipe(r) for r in rows)), ('with a bio.tools ID BEFORE matching', sum(1 for r in rows if was(r)), sum(npipe(r) for r in rows if was(r))),
            ('with a bio.tools ID AFTER matching', sum(1 for r in rows if r['biotools_id']), sum(npipe(r) for r in rows if r['biotools_id'])),
            ('gained by matching', sum(1 for r in rows if r['biotools_id'] and not was(r)), sum(npipe(r) for r in rows if r['biotools_id'] and not was(r))),
            ('still without an ID', sum(1 for r in rows if not r['biotools_id']), sum(npipe(r) for r in rows if not r['biotools_id']))]
    for ev, n in collections.Counter(r['id_source'][len('biotools-jsonl-'):] for r in rows if r['id_source'].startswith('biotools-jsonl-')).most_common(): summ.append(('  gained via ' + ev, n, sum(npipe(r) for r in rows if r['id_source'] == 'biotools-jsonl-' + ev)))
    with open(os.path.join(out, 'biotools_match_summary.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh, lineterminator='\n'); w.writerow(['metric', 'n_tools', 'sum_of_n_pipelines (a tool used in 10 pipelines counts 10)', 'share_of_tools']); [w.writerow([m, n, pw, f'{n / max(1, len(rows)):.1%}']) for m, n, pw in summ]
    print('\nBEFORE vs AFTER matching (tools | tool-uses over pipelines | share of tools)')
    for m, n, pw in summ: print(f'  {m:40s} {n:6d} | {pw:7d} | {n / max(1, len(rows)):6.1%}')
    print('\ntools without an ID before:', sum(counts.values()), '| by evidence:', dict(counts.most_common()))
    print('now with a bio.tools ID:', sum(1 for r in rows if r['biotools_id']), 'of', len(rows))
    print('updated:', os.path.join(out, 'tool_identifiers.csv'), '| report (review `ambiguous` and name-only rows):', rf)


if __name__ == '__main__':
    main()
