#!/usr/bin/env python3
"""merge_pairs.py - ONE table of directed software pairs from many pipelines, with a trust level per pair and a count of how many pipelines contain it.

  python merge_pairs.py --results RESULTS_DIR [--rnaseq-reference software_relationships_all.csv] [--out OUT_DIR] [--aliases aliases.csv]

RESULTS_DIR = the folder written by `catalogue_run.py run` (one sub-folder per pipeline, each with reference/software_relationships.csv).
The nf-core/rnaseq 3.27.0 reference (curated, verified) is added as the pipeline `rnaseq_3.27.0_reference`; the auto-generated rnaseq__* folders are then skipped
so rnaseq is not counted twice.

Writes:
  pairs_merged_long.csv    one row per (pipeline, pair): names, category, trust level, number of process edges
  pairs_merged_unique.csv  one row per distinct directed pair: in how many pipelines it appears (positive / negative), which, best trust level
  pairs_merged_summary.md  the most frequent pairs (analysis tools only)

Software names are normalised for matching only (lower case, text in brackets removed, non-letters removed: 'SAMtools' = 'samtools', 'Trim Galore' = 'trimgalore').
Names from non-rnaseq pipelines are auto-guessed; the same tool under different spellings will still be counted separately. `--aliases` (CSV: from,to) merges them.
"""
import argparse, collections, csv, os, re, sys

TRUST = [  # (code, rank, meaning)
    ('verified_pair', 1, 'Gold: verified for this exact pair against the source code (rnaseq only)'),
    ('verified_family_rule', 2, 'Silver: verified by a family rule (rnaseq only)'),
    ('algorithmic_curated_names', 3, 'edge found by static analysis; software names curated by hand (rnaseq only)'),
    ('algorithmic_unreviewed_names', 4, 'edge found by static analysis; software names auto-guessed and NOT reviewed'),
    ('gate_metadata', 5, 'dependency through a gate / metadata, not a data payload'),
    ('negative_verified', 6, 'verified: A cannot feed B'),
    ('negative_unverified', 7, 'graph says A cannot feed B; not individually verified'),
]
RANK = {c: r for c, r, _ in TRUST}
POSITIVE = {'verified_pair', 'verified_family_rule', 'algorithmic_curated_names', 'algorithmic_unreviewed_names'}
NEGATIVE = {'negative_verified', 'negative_unverified'}
UTILITY = {'multiqc', 'gunzip', 'gzip', 'cat', 'untar', 'tar', 'xz', 'unzip', 'bzip2', 'pigz', 'gawk', 'sed', 'python', 'rbase', 'coreutils', 'wget', 'curl', 'custom', 'gzipgunzip', 'untarunzip'}


BTID = {}   # name key -> bio.tools ID (filled from --tool-ids)
PARENT = {}   # name key -> parent tool key, only for names that are a tool plus an operation (star_align -> star)
ANYID = set()   # name keys that have ANY identifier: bio.tools ID, bioconda package, DOI / publication, other ID


def rawkey(name, aliases):
    n = re.sub(r'\(.*?\)', '', name or '').lower()
    k = re.sub(r'[^a-z0-9]', '', n) or re.sub(r'[^a-z0-9]', '', (name or '').lower())
    k = aliases.get(k, k)
    return PARENT.get(k, k)


def key(name, aliases):
    n = re.sub(r'\(.*?\)', '', name or '').lower()
    k = re.sub(r'[^a-z0-9]', '', n) or re.sub(r'[^a-z0-9]', '', (name or '').lower())
    k = aliases.get(k, k); k = PARENT.get(k, k)
    return ('bt:' + BTID[k].lower()) if k in BTID else k


def trust_of(category, curated):
    if category == 'Gold': return 'verified_pair'
    if category == 'Silver': return 'verified_family_rule'
    if category == 'Algorithmic_supported': return 'algorithmic_curated_names' if curated else 'algorithmic_unreviewed_names'
    if category == 'Dependency_gate_metadata': return 'gate_metadata'
    if category == 'Negative_verified': return 'negative_verified'
    if category.startswith('Negative'): return 'negative_unverified'
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--results', required=True); ap.add_argument('--rnaseq-reference'); ap.add_argument('--out'); ap.add_argument('--aliases'); ap.add_argument('--only-with-ids', choices=['biotools', 'any'], help='also write *_with_ids.csv files that keep only pairs where BOTH tools have a bio.tools ID (biotools) or at least one identifier of any kind (any); needs --tool-ids'); ap.add_argument('--tool-ids', help='tool_identifiers.csv from tool_ids.py: tools with the same bio.tools ID are merged and the ID is added to the output')
    a = ap.parse_args()
    out = a.out or a.results; os.makedirs(out, exist_ok=True)
    aliases = {}
    if a.aliases:
        for r in csv.DictReader(open(a.aliases, encoding='utf-8')): aliases[re.sub(r'[^a-z0-9]', '', r['from'].lower())] = re.sub(r'[^a-z0-9]', '', r['to'].lower())
    if a.tool_ids and os.path.exists(a.tool_ids):
        for r in csv.DictReader(open(a.tool_ids, encoding='utf-8')):
            if r['biotools_id']: BTID[r['tool_key']] = r['biotools_id']
            if r.get('parent_confidence') == 'operation-suffix' and r.get('parent_key'): PARENT[r['tool_key']] = r['parent_key']
            if any(r.get(c) for c in ('biotools_id', 'bioconda_package', 'doi', 'publications', 'other_ids')): ANYID.add(r['tool_key'])
        print('tool IDs loaded:', len(BTID))
    long_rows = []

    def add(pipeline, src, dst, category, curated, n_edges, selfloop):
        t = trust_of(category, curated)
        if not t or str(selfloop) == 'True': return
        ks, kd = key(src, aliases), key(dst, aliases)
        if ks == kd: return
        long_rows.append({'pipeline': pipeline, 'source_software': src, 'target_software': dst, 'source_key': ks, 'target_key': kd, 'source_biotools_id': ks[3:] if ks.startswith('bt:') else '', 'target_biotools_id': kd[3:] if kd.startswith('bt:') else '', 'source_has_any_id': ks.startswith('bt:') or rawkey(src, aliases) in ANYID, 'target_has_any_id': kd.startswith('bt:') or rawkey(dst, aliases) in ANYID, 'category': category, 'trust': t, 'trust_rank': RANK[t],
                          'n_process_edges': n_edges, 'names_reviewed': curated, 'involves_utility_or_reporting': ks.replace('bt:', '') in UTILITY or kd.replace('bt:', '') in UTILITY})

    have_ref = bool(a.rnaseq_reference and os.path.exists(a.rnaseq_reference))
    if have_ref:
        for r in csv.DictReader(open(a.rnaseq_reference, encoding='utf-8')):
            add('rnaseq_3.27.0_reference', r['source_software'], r['target_software'], r['category'], True, r.get('n_process_edges', ''), r['is_self_loop'])
    elif a.rnaseq_reference: print('WARNING: rnaseq reference not found:', a.rnaseq_reference, file=sys.stderr)
    n_pipes = 0
    for p in sorted(os.listdir(a.results)):
        f = os.path.join(a.results, p, 'reference', 'software_relationships.csv')
        if not os.path.exists(f): continue
        if have_ref and p.split('__')[0] == 'rnaseq': continue
        n_pipes += 1
        for r in csv.DictReader(open(f, encoding='utf-8')):
            add(p, r['source_software'], r['target_software'], r['category'], False, r.get('n_process_edges', ''), r['is_self_loop'])
    cols = list(long_rows[0].keys()) if long_rows else ['pipeline']
    with open(os.path.join(out, 'pairs_merged_long.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator='\n'); w.writeheader(); w.writerows(sorted(long_rows, key=lambda r: (r['source_key'], r['target_key'], r['trust_rank'], r['pipeline'])))

    groups = collections.defaultdict(list)
    for r in long_rows: groups[(r['source_key'], r['target_key'])].append(r)
    names = collections.defaultdict(collections.Counter)
    for r in long_rows: names[r['source_key']][r['source_software']] += 1; names[r['target_key']][r['target_software']] += 1
    disp = lambda k: names[k].most_common(1)[0][0]
    uniq = []
    for (ks, kd), rs in groups.items():
        pos = sorted({r['pipeline'] for r in rs if r['trust'] in POSITIVE}); neg = sorted({r['pipeline'] for r in rs if r['trust'] in NEGATIVE})
        rev = sorted({r['pipeline'] for r in groups.get((kd, ks), []) if r['trust'] in POSITIVE})
        best = min(rs, key=lambda r: r['trust_rank'])['trust']
        edges = sum(int(r['n_process_edges'] or 0) for r in rs if r['trust'] in POSITIVE)
        uniq.append({'source_software': disp(ks), 'target_software': disp(kd), 'source_key': ks, 'target_key': kd, 'source_biotools_id': ks[3:] if ks.startswith('bt:') else '', 'target_biotools_id': kd[3:] if kd.startswith('bt:') else '', 'source_has_any_id': rs[0]['source_has_any_id'], 'target_has_any_id': rs[0]['target_has_any_id'], 'n_pipelines_positive': len(pos), 'n_pipelines_negative': len(neg),
                     'n_process_edges_positive': edges, 'best_trust': best, 'best_trust_rank': RANK[best], 'categories': ';'.join(sorted({r['category'] for r in rs})),
                     'reverse_direction_pipelines': len(rev), 'involves_utility_or_reporting': ks.replace('bt:', '') in UTILITY or kd.replace('bt:', '') in UTILITY,
                     'in_verified_reference': any(r['pipeline'] == 'rnaseq_3.27.0_reference' and r['trust'] in ('verified_pair', 'verified_family_rule') for r in rs),
                     'pipelines_positive': ';'.join(pos), 'pipelines_negative': ';'.join(neg)})
    uniq.sort(key=lambda r: (-r['n_pipelines_positive'], r['best_trust_rank'], r['source_key'], r['target_key']))
    with open(os.path.join(out, 'pairs_merged_unique.csv'), 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(uniq[0].keys()) if uniq else ['x'], lineterminator='\n'); w.writeheader(); w.writerows(uniq)

    if a.only_with_ids:
        if not BTID and not ANYID: sys.exit('--only-with-ids needs --tool-ids (run: python catalogue_run.py ids --lookup first)')
        if a.only_with_ids == 'biotools': keep = lambda r: r['source_biotools_id'] and r['target_biotools_id']
        else: keep = lambda r: r['source_has_any_id'] and r['target_has_any_id']
        for name, rows_, fields in (('pairs_merged_unique_with_ids.csv', [u for u in uniq if keep(u)], uniq), ('pairs_merged_long_with_ids.csv', [r for r in long_rows if keep(r)], long_rows)):
            with open(os.path.join(out, name), 'w', newline='', encoding='utf-8') as fh:
                w = csv.DictWriter(fh, fieldnames=list(fields[0].keys()), lineterminator='\n'); w.writeheader(); w.writerows(rows_)
            print(f'{name}: {len(rows_)} of {len(fields)} rows kept (both tools have {"a bio.tools ID" if a.only_with_ids == "biotools" else "at least one identifier"})')
    posu = [u for u in uniq if u['n_pipelines_positive']]
    core = [u for u in posu if not u['involves_utility_or_reporting']]
    multi = [u for u in posu if u['n_pipelines_positive'] >= 2]
    lines = ['# Merged software pairs', '', f"- pipelines merged: {n_pipes} generated" + (' + the verified rnaseq 3.27.0 reference' if have_ref else ''),
             f"- distinct directed positive pairs: {len(posu)} ({len(core)} without utilities/MultiQC)", f"- positive pairs found in 2+ pipelines: {len(multi)}",
             f"- pairs by best trust level: {dict(collections.Counter(u['best_trust'] for u in uniq))}", '', '## Trust levels', '']
    lines += [f'- `{c}` (rank {r}): {m}' for c, r, m in TRUST]
    lines += ['', '## Most frequent pairs (analysis tools only; number of pipelines, best trust level)', '', '| source | target | pipelines | edges | best trust |', '|---|---|---|---|---|']
    for u in core[:40]: lines.append(f"| {u['source_software']} | {u['target_software']} | {u['n_pipelines_positive']} | {u['n_process_edges_positive']} | {u['best_trust']} |")
    open(os.path.join(out, 'pairs_merged_summary.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    print(f"{n_pipes} pipelines merged{' + rnaseq reference' if have_ref else ''}: {len(long_rows)} rows, {len(uniq)} distinct pairs, {len(multi)} positive pairs in 2+ pipelines")
    print('most frequent (analysis tools only):')
    for u in core[:15]: print(f"  {u['n_pipelines_positive']:4d} pipelines  {u['source_software']} -> {u['target_software']}  [{u['best_trust']}]")
    print('written:', os.path.join(out, 'pairs_merged_unique.csv'), '|', os.path.join(out, 'pairs_merged_long.csv'), '|', os.path.join(out, 'pairs_merged_summary.md'))


main()
