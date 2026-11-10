#!/usr/bin/env python3
"""compare_ids.py - how many tools had a bio.tools ID before and after matching. Reads two csv files, runs in a second, changes nothing.

  python compare_ids.py                                   # in the results folder: compares tool_identifiers.before_jsonl.csv with tool_identifiers.csv
  python compare_ids.py BEFORE.csv AFTER.csv              # or any two tool_identifiers tables
  python compare_ids.py AFTER.csv                         # one table: 'before' = tools whose ID did not come from the bio.tools dump (id_source not 'biotools-jsonl-*')

Also prints which tools gained an ID and how (evidence), and a count weighted by n_pipelines (a tool used in 10 pipelines counts 10).
"""
import collections, csv, os, sys

args = sys.argv[1:]
if not args:
    args = ['tool_identifiers.before_jsonl.csv', 'tool_identifiers.csv'] if os.path.exists('tool_identifiers.before_jsonl.csv') else ['tool_identifiers.csv']
rd = lambda p: {r['tool_key']: r for r in csv.DictReader(open(p, encoding='utf-8'))}
if len(args) == 1:
    after = rd(args[0]); before = {k: (r if not (r.get('id_source') or '').startswith('biotools-jsonl') else dict(r, biotools_id='')) for k, r in after.items()}
else:
    before, after = rd(args[0]), rd(args[1])
has = lambda r: bool((r or {}).get('biotools_id'))
npipe = lambda r: int((r or {}).get('n_pipelines') or 0)
keys = sorted(set(before) | set(after))
tot = len(keys)
b = [k for k in keys if has(before.get(k))]; a_ = [k for k in keys if has(after.get(k))]
gained = [k for k in keys if has(after.get(k)) and not has(before.get(k))]
print(f'tools: {tot}')
print(f'{"":34s} {"tools":>7s} {"share":>7s} {"tool-uses":>10s}')
for label, ks in (('with a bio.tools ID BEFORE', b), ('with a bio.tools ID AFTER', a_), ('gained', gained), ('still without an ID', [k for k in keys if not has(after.get(k))])):
    print(f'{label:34s} {len(ks):7d} {len(ks) / max(1, tot):7.1%} {sum(npipe(after.get(k) or before.get(k)) for k in ks):10d}')
print('\nID source before -> after')
print('  before:', dict(collections.Counter((before.get(k) or {}).get('id_source') or 'none' for k in b).most_common()))
print('  after: ', dict(collections.Counter((after.get(k) or {}).get('id_source') or 'none' for k in a_).most_common()))
print('\ngained by evidence:', dict(collections.Counter((after[k].get('match_evidence') or after[k].get('id_source') or '?') for k in gained).most_common()))
print('\nthe 15 gained tools used in the most pipelines:')
for k in sorted(gained, key=lambda k: -npipe(after[k]))[:15]:
    r = after[k]; print(f'  {npipe(r):4d} pipelines  {r["tool_name"][:28]:28s} -> {r["biotools_id"]:24s} [{r.get("match_evidence") or r.get("id_source")}]')
lost = [k for k in keys if has(before.get(k)) and not has(after.get(k))]
if lost: print('\nWARNING: tools that HAD an ID before and have none now:', lost[:10])
