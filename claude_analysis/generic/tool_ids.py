#!/usr/bin/env python3
"""tool_ids.py - collect every identifier we can find for the software tools in a catalogue of Nextflow pipelines.

  python tool_ids.py --catalogue DIR [--results RESULTS_DIR] [--lookup] [--out DIR]

Sources, in this order:
  1. every modules/**/meta.yml under DIR: tool name, `identifier: biotools:<id>`, homepage, documentation, DOI
  2. every modules/**/environment.yml: the bioconda package of the tool
  3. RESULTS_DIR/<pipeline>/reference/software_relationships.csv: software names that have no meta.yml (old-style pipelines, guessed names) so they can be looked up too
  4. with --lookup (needs internet): the bio.tools API. A tool WITHOUT an ID from meta.yml gets one only on an EXACT name match
     (name or biotoolsID equals the tool name after lower-casing and removing non-letters). Records also return other IDs (RRID ...) and publications (DOI / PMID).

Writes OUT/tool_identifiers.csv (one row per tool) and OUT/biotools_cache.json (API answers, reused on re-runs).
Nothing is executed; only text files are read.
"""
import argparse, collections, concurrent.futures as cf, csv, json, os, re, sys, time, urllib.parse, urllib.request

try: import yaml
except ImportError: sys.exit('pyyaml missing - run: python catalogue_run.py setup')

HELPERS = {'htslib', 'coreutils', 'grep', 'gzip', 'lbzip2', 'sed', 'tar', 'pigz', 'python', 'r-base', 'bzip2', 'xz', 'pip', 'conda', 'bash', 'gawk', 'perl', 'findutils', 'zlib'}


def key(name):
    n = re.sub(r'\(.*?\)', '', name or '').lower()
    return re.sub(r'[^a-z0-9]', '', n) or re.sub(r'[^a-z0-9]', '', (name or '').lower())


# shell utilities and reporting wrappers: a name match on bio.tools would be a homonym (e.g. `cat` is not the CAT taxonomy tool), so they are never looked up by name
NO_NAME_LOOKUP = {'cat', 'gzip', 'gunzip', 'tar', 'untar', 'unzip', 'sed', 'awk', 'gawk', 'grep', 'sort', 'cut', 'head', 'tail', 'echo', 'python', 'rbase', 'r', 'perl', 'bash', 'java', 'custom', 'print', 'def', 'zcat', 'xz', 'bzip2', 'pigz', 'wget', 'curl', 'ln', 'cp', 'mv', 'rm', 'mkdir', 'touch', 'cd', 'wc', 'tee', 'join', 'paste'}


# words that name an OPERATION of a tool, not another tool: `star_align`, `samtools_sort`, `bwa_index` are STAR / SAMtools / BWA doing that step
OPS = set('align alignment aligner index indexing build genomegenerate generate sort view merge stats flagstat idxstats quant quantification count counts run call calling mem extract dedup markduplicates mark duplicates trim trimming filter convert fastq bam sam cram vcf prepare reference calculate expression profile pileup coverage depth report summary make fai faidx bgzip tabix stat metrics lint check collapse annotate detect predict classify assemble assembly map mapping split cat'.split())


def pick(counter):
    return counter.most_common(1)[0][0] if counter else ''


def scan(cat):
    tools = {}
    def rec(k, name):
        return tools.setdefault(k, {'names': collections.Counter(), 'ids': collections.Counter(), 'homepage': collections.Counter(), 'doc': collections.Counter(), 'doi': collections.Counter(),
                                    'conda': collections.Counter(), 'modules': set(), 'pipelines': set()})
    for dp, dn, fn in os.walk(cat):
        dn[:] = [d for d in dn if d not in ('.git', 'tests', 'work')]
        rel = os.path.relpath(dp, cat).replace('\\', '/'); pipe = rel.split('/')[0]
        if 'meta.yml' in fn and '/modules/' in '/' + rel + '/':
            try: m = yaml.safe_load(open(os.path.join(dp, 'meta.yml'), encoding='utf-8')) or {}
            except Exception: continue
            tl = m.get('tools') or []
            if not isinstance(tl, list): continue
            envp = []
            if 'environment.yml' in fn:
                try: envp = [re.sub(r'^.*::', '', x).split('=')[0] for x in (yaml.safe_load(open(os.path.join(dp, 'environment.yml'), encoding='utf-8')) or {}).get('dependencies', []) if isinstance(x, str)]
                except Exception: envp = []
            for t in tl:
                if not isinstance(t, dict): continue
                for name, d in t.items():
                    d = d if isinstance(d, dict) else {}
                    k = key(name)
                    if not k: continue
                    r = rec(k, name); r['names'][str(name)] += 1; r['modules'].add(rel); r['pipelines'].add(pipe)
                    ident = d.get('identifier'); ident = ' '.join(map(str, ident)) if isinstance(ident, list) else str(ident or '')
                    for part in re.findall(r'biotools:([\w.\-]+)', ident): r['ids'][part] += 1
                    if d.get('homepage'): r['homepage'][str(d['homepage']).strip()] += 1
                    if d.get('documentation'): r['doc'][str(d['documentation']).strip()] += 1
                    doi = d.get('doi'); doi = ' '.join(map(str, doi)) if isinstance(doi, list) else str(doi or '')
                    for dd in re.findall(r'10\.\d{4,9}/[^\s,;]+', doi): r['doi'][dd.rstrip('.')] += 1
                    for pkg in envp:
                        if key(pkg) == k and pkg not in HELPERS: r['conda'][pkg] += 1
    return tools


def add_results_names(tools, results):
    n = 0
    for p in sorted(os.listdir(results)):
        f = os.path.join(results, p, 'reference', 'software_relationships.csv')
        if not os.path.exists(f): continue
        for row in csv.DictReader(open(f, encoding='utf-8')):
            for nm in (row['source_software'], row['target_software']):
                k = key(nm)
                if not k: continue
                if k not in tools:
                    tools[k] = {'names': collections.Counter(), 'ids': collections.Counter(), 'homepage': collections.Counter(), 'doc': collections.Counter(), 'doi': collections.Counter(),
                                'conda': collections.Counter(), 'modules': set(), 'pipelines': set()}; n += 1
                tools[k]['names'][nm] += 1; tools[k]['pipelines'].add(p.split('__')[0])
    return n


def api(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'nfrel-tool-ids'})
            with urllib.request.urlopen(req, timeout=25) as r: return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
        except Exception: pass
        time.sleep(1.5 * (i + 1))
    return 'ERROR'


def lookup(k, name, known_id, cache):
    ck = known_id or ('name:' + k)
    if ck in cache: return cache[ck]
    rec = None; how = ''
    if known_id:
        rec = api('https://bio.tools/api/tool/' + urllib.parse.quote(known_id) + '/?format=json'); how = 'meta.yml'
    else:
        if k in NO_NAME_LOOKUP: cache[ck] = {'found': False}; return cache[ck]
        base = re.sub(r'\(.*?\)', '', name).strip().lower()
        for cand in dict.fromkeys([base.replace(' ', '_'), base.replace(' ', '-'), base.replace('_', '-'), base.replace('-', '_'), base.replace(' ', ''), k]):
            if not cand: continue
            r = api('https://bio.tools/api/tool/' + urllib.parse.quote(cand) + '/?format=json')
            if isinstance(r, dict) and r.get('biotoolsID') and key(r['biotoolsID']) == k: rec = r; how = 'bio.tools-exact-id'; break
        if rec is None:
            r = api('https://bio.tools/api/tool/?q=' + urllib.parse.quote(name) + '&format=json')
            if isinstance(r, dict):
                for it in r.get('list', []):
                    if key(it.get('name', '')) == k or key(it.get('biotoolsID', '')) == k: rec = it; how = 'bio.tools-exact-name'; break
    out = {'found': False}
    if isinstance(rec, dict) and rec.get('biotoolsID'):
        pubs = []
        for pb in rec.get('publication') or []:
            if pb.get('doi'): pubs.append('doi:' + str(pb['doi']))
            if pb.get('pmid'): pubs.append('pmid:' + str(pb['pmid']))
        others = ['%s:%s' % (o.get('type', ''), o.get('value', '')) for o in rec.get('otherID') or []]
        out = {'found': True, 'id': rec['biotoolsID'], 'name': rec.get('name', ''), 'how': how, 'homepage': rec.get('homepage', ''), 'other_ids': others, 'publications': list(dict.fromkeys(pubs))}
    cache[ck] = out
    return out


def resolve_parents(rows):
    """names that are a known tool plus an operation (star_align -> star) get parent_key / parent_biotools_id / operation_suffix / parent_confidence"""
    with_id = {r['tool_key']: r['biotools_id'] for r in rows if r['biotools_id'] and r['tool_key'] not in NO_NAME_LOOKUP and len(r['tool_key']) >= 3}
    for r in rows:
        r.update({'parent_key': '', 'parent_biotools_id': '', 'operation_suffix': '', 'parent_confidence': ''})
        if r['biotools_id']: continue
        toks = [t for t in re.split(r'[_\-\s]+', re.sub(r'\(.*?\)', '', r['tool_name']).lower()) if t]
        if len(toks) < 2: continue
        par = key(toks[0])
        if par in with_id and par != r['tool_key']:
            rest = toks[1:]
            r.update({'parent_key': par, 'parent_biotools_id': with_id[par], 'operation_suffix': ' '.join(rest), 'parent_confidence': 'operation-suffix' if all(t in OPS or t.isdigit() for t in rest) else 'first-word-review'})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--catalogue', required=True); ap.add_argument('--results'); ap.add_argument('--out', default='.'); ap.add_argument('--lookup', action='store_true'); ap.add_argument('--jobs', type=int, default=4)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tools = scan(a.catalogue); n_meta = len(tools)
    extra = add_results_names(tools, a.results) if a.results and os.path.isdir(a.results) else 0
    print(f'{n_meta} tools from meta.yml; {extra} more software names from the results')
    cpath = os.path.join(a.out, 'biotools_cache.json')
    cache = json.load(open(cpath, encoding='utf-8')) if os.path.exists(cpath) else {}
    info = {}
    if a.lookup:
        todo = [(k, pick(t['names']), pick(t['ids'])) for k, t in sorted(tools.items())]
        print(f'bio.tools lookup for {len(todo)} tools (cached: {sum(1 for k, n, i in todo if (i or "name:" + k) in cache)}) ...', flush=True)
        with cf.ThreadPoolExecutor(max_workers=a.jobs) as ex:
            for i, ((k, nm, idd), res) in enumerate(zip(todo, ex.map(lambda x: lookup(x[0], x[1], x[2], cache), todo)), 1):
                info[k] = res
                if i % 100 == 0: print(f'  {i}/{len(todo)}', flush=True); json.dump(cache, open(cpath, 'w', encoding='utf-8'))
        json.dump(cache, open(cpath, 'w', encoding='utf-8'), indent=0)
    rows = []
    for k, t in sorted(tools.items()):
        res = info.get(k, {}); meta_id = pick(t['ids'])
        bid = meta_id or (res.get('id', '') if res.get('found') else '')
        src = 'meta.yml' if meta_id else (res.get('how', '') if res.get('found') else ('none' if a.lookup else 'none (run with --lookup)'))
        rows.append({'tool_key': k, 'tool_name': pick(t['names']), 'biotools_id': bid, 'biotools_url': ('https://bio.tools/' + bid) if bid else '', 'id_source': src,
                     'bioconda_package': pick(t['conda']), 'doi': ';'.join(d for d, _ in t['doi'].most_common(3)), 'homepage': pick(t['homepage']) or res.get('homepage', ''),
                     'documentation': pick(t['doc']), 'other_ids': ';'.join(res.get('other_ids', [])), 'publications': ';'.join(res.get('publications', [])),
                     'n_modules': len(t['modules']), 'n_pipelines': len(t['pipelines']), 'name_variants': ' | '.join(n for n, _ in t['names'].most_common(4))})
    resolve_parents(rows)
    rows.sort(key=lambda r: (-r['n_pipelines'], r['tool_key']))
    f = os.path.join(a.out, 'tool_identifiers.csv')
    with open(f, 'w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ['tool_key'], lineterminator='\n'); w.writeheader(); w.writerows(rows)
    c = collections.Counter(r['id_source'] for r in rows)
    print(f'{len(rows)} tools -> {f}\nwith a bio.tools ID: {sum(1 for r in rows if r["biotools_id"])} | by source: {dict(c)}')
    print('names resolved to a parent tool (e.g. star_align -> star):', sum(1 for r in rows if r['parent_confidence'] == 'operation-suffix'), '| first-word matches to review:', sum(1 for r in rows if r['parent_confidence'] == 'first-word-review'))
    print('with a bioconda package:', sum(1 for r in rows if r['bioconda_package']), '| with a DOI:', sum(1 for r in rows if r['doi'] or r['publications']))


if __name__ == '__main__':
    main()
