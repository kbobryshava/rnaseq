#!/usr/bin/env python3
"""Compare the hand-drawn nf-core metro map (assets/metro_map.mmd) with the static process-level edges.

The metro map ties stations to process names with `%%metro process: station | TAIL` directives and draws
`a -->|lines| b` connections.  A station-to-station connection is "supported" when at least one instance of
station a has a process-level data edge (any class) to an instance of station b, i.e. the metro map's
connection is a data dependency.  Unsupported connections are layout/presentation order, not data flow.
Usage: python compare_metro.py --repo <repo> --out <claude_analysis dir>
"""
import argparse, csv, json, os, re, collections


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--repo', required=True); ap.add_argument('--out', required=True); a = ap.parse_args()
    mmd = open(os.path.join(a.repo, 'assets', 'metro_map.mmd'), encoding='utf-8').read().splitlines()
    stations = collections.defaultdict(list)
    for ln in mmd:
        m = re.match(r'%%metro process:\s*(\w+)\s*\|\s*(\S+)', ln)
        if m: stations[m.group(1)].append(m.group(2))
    edges = []
    for i, ln in enumerate(mmd, 1):
        m = re.match(r'\s*(\w+)\s*-->\s*(?:\|([^|]*)\|)?\s*(\w+)\s*$', ln)
        if m: edges.append((m.group(1), m.group(3), (m.group(2) or '').strip(), i))
    P = os.path.join(a.out, 'data', 'processed')
    inst = [r['instance'] for r in csv.DictReader(open(os.path.join(P, 'process_instances.csv'), encoding='utf-8'))]
    pe = {(r['src_instance'], r['dst_instance']) for r in csv.DictReader(open(os.path.join(P, 'process_edges.csv'), encoding='utf-8'))}

    def match(st):
        out = set()
        for tail in stations.get(st, []):
            for p in inst:
                if p == 'NFCORE_RNASEQ:RNASEQ:' + tail or p.endswith(':' + tail) or p == tail or p.endswith(tail) and p.split(':')[-1] == tail.split(':')[-1] and tail.split(':')[0] in p:
                    out.add(p)
        return out
    rows = []
    for s, d, lines, ln in edges:
        S, D = match(s), match(d)
        if not S or not D:
            rows.append({'metro_line': ln, 'src_station': s, 'dst_station': d, 'status': 'unmapped-station', 'supporting_edge_example': ''}); continue
        sup = [(x, y) for x in S for y in D if (x, y) in pe]
        rows.append({'metro_line': ln, 'src_station': s, 'dst_station': d, 'status': 'supported' if sup else 'NOT-a-data-edge',
                     'supporting_edge_example': f'{sup[0][0]} -> {sup[0][1]}' if sup else ''})
    cnt = collections.Counter(r['status'] for r in rows)
    with open(os.path.join(P, 'metro_vs_static.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    json.dump(dict(cnt), open(os.path.join(P, 'metro_vs_static_summary.json'), 'w'))
    print(dict(cnt), 'metro connections:', len(rows))
    for r in rows:
        if r['status'] != 'supported': print(r['status'], f"assets/metro_map.mmd:{r['metro_line']}", r['src_station'], '-->', r['dst_station'])


if __name__ == '__main__':
    main()
