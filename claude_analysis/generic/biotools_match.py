#!/usr/bin/env python3
"""biotools_match.py - find bio.tools IDs, offline, for the tools that still have none, using a local dump of bio.tools (JSON lines).

  python biotools_match.py --tools tool_identifiers.csv --jsonl biotools_raw.jsonl [--out DIR] [--no-name-only]

Input : tool_identifiers.csv from tool_ids.py, and a bio.tools dump with one tool record per line (the same fields as the bio.tools API:
        biotoolsID, name, homepage, publication[{doi,pmid,pmcid}], otherID[{value,type}], link[{url}], documentation[{url}]).
        A line may also be {"list": [...]} or wrap the record under some key; the reader finds records by their `biotoolsID` field.
Match evidence, strongest first (a DOI always beats a name):
  doi+name            a DOI of the tool equals a DOI of the record AND the name (or one of the name variants) equals the record name / ID
  doi                 a DOI matches exactly one record and the names disagree or are unknown (the DOI is still stronger than the name)
  doi-ambiguous       a DOI matches several records and the name does not pick one   -> NOT accepted, listed in the report
  name-exact          no DOI evidence; the name key equals the key of exactly one record's name or ID   (weaker)
  name-ambiguous      no DOI evidence; several records have this name key           -> NOT accepted, listed in the report
DOIs are collected from the tool (meta.yml DOI, publications and other IDs of tool_identifiers.csv) and, in the record, from publication[].doi,
otherID entries and the urls in link / documentation / homepage. DOI source strength: publication > otherID > url.
Writes (OUT defaults to the folder of --tools): tool_identifiers.csv updated in place (backup: tool_identifiers.before_jsonl.csv), biotools_match_report.csv.
Nothing is downloaded.
"""
import argparse, collections, csv, json, os, re, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tool_ids import key, resolve_parents, NO_NAME_LOOKUP

DOI_RX = re.compile(r'10\.\d{4,9}/[^\s"<>,;]+', re.I)


def norm_doi(x):
    x = (x or '').strip().lower()
    x = re.sub(r'^(https?://(dx\.)?doi\.org/|doi:\s*)', '', x)
    m = DOI_RX.search(x)
    return m.group(0).rstrip('.)]}') if m else ''


def records(obj):
    """yield every dict that has a biotoolsID, wherever it is nested"""
    if isinstance(obj, dict):
        if obj.get('biotoolsID'): yield obj; return
        for v in obj.values(): yield from records(v)
    elif isinstance(obj, list):
        for v in obj: yield from records(v)


def record_dois(rec):
    out = {}   # doi -> strength (3 publication, 2 otherID, 1 url)
    def put(d, s):
        d = norm_doi(d)
        if d: out[d] = max(out.get(d, 0), s)
    for p in rec.get('publication') or []:
        if isinstance(p, dict): put(p.get('doi'), 3)
    for o in rec.get('otherID') or []:
        if isinstance(o, dict) and (str(o.get('type', '')).lower() == 'doi' or DOI_RX.search(str(o.get('value', '')))): put(o.get('value'), 2)
    for k in ('link', 'documentation'):
        for x in rec.get(k) or []:
            if isinstance(x, dict): put(x.get('url'), 1)
    put(rec.get('homepage'), 1)
    return out


def tool_dois(row):
    ds = set()
    for col in ('doi', 'publications', 'other_ids'):
        for x in re.split(r'[;|]', row.get(col, '') or ''):
            d = norm_doi(x)
            if d: ds.add(d)
    return ds


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tools', required=True); ap.add_argument('--jsonl', required=True); ap.add_argument('--out'); ap.add_argument('--no-name-only', action='store_true', help='accept DOI matches only')
    a = ap.parse_args()
    out = a.out or os.path.dirname(os.path.abspath(a.tools))
    info = {}; by_doi = collections.defaultdict(dict); by_name = collections.defaultdict(set); n_lines = 0; bad = 0
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
                for d, st in record_dois(rec).items(): by_doi[d][bid] = max(by_doi[d].get(bid, 0), st)
                for k in {key(rec.get('name', '')), key(bid)}:
                    if k: by_name[k].add(bid)
    print(f'bio.tools dump: {n_lines} lines ({bad} unreadable), {len(info)} tool records, {len(by_doi)} distinct DOIs')
    if not info: sys.exit('no records with a biotoolsID found - is this the right file? first characters: ' + open(a.jsonl, encoding='utf-8', errors='replace').read(200))
    rows = list(csv.DictReader(open(a.tools, encoding='utf-8'))); fields = list(rows[0].keys())
    shutil.copy(a.tools, os.path.join(out, 'tool_identifiers.before_jsonl.csv'))
    for c in ('match_evidence', 'match_doi', 'match_candidates'):
        if c not in fields: fields.append(c)
    report = []; counts = collections.Counter()
    for r in rows:
        r.setdefault('match_evidence', ''); r.setdefault('match_doi', ''); r.setdefault('match_candidates', '')
        if r['biotools_id'] or r['tool_key'] in NO_NAME_LOOKUP: continue
        names = {r['tool_key']} | {key(n) for n in (r.get('name_variants') or '').split('|') if n.strip()}
        names.discard('')
        dois = tool_dois(r)
        cand = collections.defaultdict(lambda: {'doi': 0, 'name': False, 'dois': set()})
        for d in dois:
            for bid, st in by_doi.get(d, {}).items():
                c = cand[bid]; c['doi'] = max(c['doi'], st); c['dois'].add(d)
        for bid in list(cand):
            cand[bid]['name'] = bool({key(info[bid]['name']), key(bid)} & names)
        evidence, chosen = '', None
        if cand:
            both = [b for b, c in cand.items() if c['name']]
            if len(both) == 1: evidence, chosen = 'doi+name', both[0]
            elif len(both) > 1: evidence = 'doi-ambiguous'
            elif len(cand) == 1: evidence, chosen = 'doi', next(iter(cand))
            else: evidence = 'doi-ambiguous'
        if not chosen and evidence != 'doi-ambiguous' and not a.no_name_only:
            ids = set().union(*[by_name.get(k, set()) for k in names]) if names else set()
            if len(ids) == 1: evidence, chosen = 'name-exact', next(iter(ids))
            elif len(ids) > 1: evidence = 'name-ambiguous'; cand = {b: {'doi': 0, 'name': True, 'dois': set()} for b in ids}
        counts[evidence or 'no-match'] += 1
        if chosen:
            r['biotools_id'] = chosen; r['biotools_url'] = 'https://bio.tools/' + chosen; r['id_source'] = 'biotools-jsonl-' + evidence
            r['match_evidence'] = evidence; r['match_doi'] = ';'.join(sorted(cand[chosen]['dois']))
            if not r.get('homepage'): r['homepage'] = info[chosen]['homepage']
        if evidence:
            r['match_candidates'] = ';'.join(sorted(cand))[:300]
            report.append({'tool_key': r['tool_key'], 'tool_name': r['tool_name'], 'evidence': evidence, 'accepted': bool(chosen), 'chosen_biotools_id': chosen or '', 'chosen_name': info[chosen]['name'] if chosen else '',
                           'candidates': ';'.join(f"{b} ({info[b]['name']})" for b in sorted(cand))[:400], 'tool_dois': ';'.join(sorted(dois)), 'name_variants': r.get('name_variants', '')})
    rows_sorted = rows
    # a tool that just got an ID can be the parent of operation-suffixed names (star_align -> star): recompute
    for r in rows_sorted:
        for c in ('parent_key', 'parent_biotools_id', 'operation_suffix', 'parent_confidence'): r[c] = ''
    resolve_parents(rows_sorted)
    for c in ('parent_key', 'parent_biotools_id', 'operation_suffix', 'parent_confidence'):
        if c not in fields: fields.append(c)
    with open(os.path.join(out, 'tool_identifiers.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction='ignore', lineterminator='\n'); w.writeheader(); w.writerows(rows_sorted)
    rf = os.path.join(out, 'biotools_match_report.csv')
    with open(rf, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['tool_key', 'tool_name', 'evidence', 'accepted', 'chosen_biotools_id', 'chosen_name', 'candidates', 'tool_dois', 'name_variants'], lineterminator='\n'); w.writeheader(); w.writerows(report)
    print('tools without an ID before:', sum(counts.values()), '| by result:', dict(counts))
    print('now with a bio.tools ID:', sum(1 for r in rows_sorted if r['biotools_id']), 'of', len(rows_sorted))
    print('updated:', os.path.join(out, 'tool_identifiers.csv'), '| report (review the non-accepted and name-exact rows):', rf)


if __name__ == '__main__':
    main()
