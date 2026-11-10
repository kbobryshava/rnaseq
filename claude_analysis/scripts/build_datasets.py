#!/usr/bin/env python3
"""Turn static_graph.json (+ preview DAGs) into the final datasets.

Outputs (data/processed, data/graphs):
  process_instances.csv, process_edges.csv, process_edges_evidence.jsonl,
  process_software_map.csv, canonical_software.csv, software_nodes.csv,
  software_edges.csv, manual_review.csv, dag_vs_static.json, executed_matrix.csv
  graphs/process_graph.graphml, graphs/software_graph.graphml, graphs/full_graph.json
Run:  python build_datasets.py --repo <repo root> --out <claude_analysis dir>
"""
import argparse, csv, glob, json, os, re, sys, collections
import yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_dag import parse as parse_dag
from nf_static_analyzer import cond_atoms
import payload_checks
from payload_checks import payload_verdict, REJECT_VERDICTS

# --------------------------------------------------------------------------
# Curated canonical software table.  key -> (canonical name, role, note)
# roles: analysis | qc | reporting | utility | reference-prep | quantification
# --------------------------------------------------------------------------
CANON = {
 'star': ('STAR', 'analysis'), 'samtools': ('SAMtools', 'utility'), 'salmon': ('Salmon', 'quantification'),
 'fastqc': ('FastQC', 'qc'), 'trimgalore': ('Trim Galore', 'analysis'), 'fastp': ('fastp', 'analysis'),
 'hisat2': ('HISAT2', 'analysis'), 'bowtie2': ('Bowtie 2', 'analysis'), 'bbmap': ('BBMap (BBSplit)', 'analysis'),
 'sortmerna': ('SortMeRNA', 'analysis'), 'ribodetector': ('RiboDetector', 'analysis'), 'kallisto': ('kallisto', 'quantification'),
 'kraken2': ('Kraken 2', 'analysis'), 'bracken': ('Bracken', 'analysis'), 'sylph': ('Sylph', 'analysis'),
 'sylphtax': ('sylph-tax', 'analysis'), 'rsem': ('RSEM', 'quantification'), 'picard': ('Picard', 'analysis'),
 'stringtie': ('StringTie', 'analysis'), 'rseqc': ('RSeQC', 'qc'), 'rustqc': ('RustQC', 'qc'), 'qualimap': ('Qualimap', 'qc'),
 'dupradar': ('dupRadar', 'qc'), 'preseq': ('Preseq', 'qc'), 'featurecounts': ('featureCounts (Subread)', 'quantification'),
 'bedtools': ('BEDTools', 'analysis'), 'ucsc_bedclip': ('UCSC bedClip', 'analysis'), 'ucsc_bedgraphtobigwig': ('UCSC bedGraphToBigWig', 'analysis'),
 'umi_tools': ('UMI-tools', 'analysis'), 'umicollapse': ('UMICollapse', 'analysis'), 'multiqc': ('MultiQC', 'reporting'),
 'gffread': ('GffRead', 'reference-prep'), 'seqkit': ('SeqKit', 'utility'), 'fq': ('fq', 'qc'), 'eautils_gtf2bed': ('ea-utils gtf2bed', 'reference-prep'),
 'tximeta': ('tximeta', 'quantification'), 'summarizedexperiment': ('SummarizedExperiment', 'quantification'), 'deseq2': ('DESeq2', 'qc'),
 'parabricks': ('NVIDIA Parabricks', 'analysis'), 'sentieon': ('Sentieon', 'analysis'), 'gunzip': ('gzip (gunzip)', 'utility'),
 'cat': ('cat (GNU coreutils)', 'utility'), 'untar': ('GNU tar', 'utility'), 'sed': ('sed', 'utility'), 'gawk': ('gawk', 'utility'),
 'local_python': ('nf-core custom script (Python)', 'utility'), 'local_r': ('nf-core custom script (R)', 'utility'),
 'sentieon_star': ('Sentieon STAR', 'analysis'), 'sentieon_rsem': ('Sentieon RSEM', 'quantification'),
 'parabricks_star': ('NVIDIA Parabricks rna_fq2bam (STAR-based)', 'analysis'),
}
ALTERNATIVE_OF = {'sentieon_star': 'STAR', 'sentieon_rsem': 'RSEM', 'parabricks_star': 'STAR'}

# module (process definition name) -> primary software keys.  Curated after reading each
# module's main.nf, environment.yml, meta.yml and topic version tuples (see methodology report).
PRIMARY = {
 'DESEQ2_QC': ['deseq2'], 'PREPROCESS_TRANSCRIPTS_FASTA_GENCODE': ['sed'], 'STAR_GENOMEPARAMS_UPGRADE': ['gawk'],
 'BBMAP_BBSPLIT': ['bbmap'], 'BEDTOOLS_GENOMECOV': ['bedtools'], 'BOWTIE2_ALIGN': ['bowtie2'], 'BOWTIE2_BUILD': ['bowtie2'],
 'BRACKEN_BRACKEN': ['bracken'], 'CAT_FASTQ': ['cat'], 'CUSTOM_CATADDITIONALFASTA': ['local_python'], 'CUSTOM_GTFFILTER': ['local_python'],
 'CUSTOM_MULTIQCCUSTOMBIOTYPE': ['local_python'], 'CUSTOM_RSEMMERGECOUNTS': ['sed'], 'CUSTOM_TX2GENE': ['local_python'],
 'DUPRADAR': ['dupradar'], 'EAUTILS_GTF2BED': ['eautils_gtf2bed'], 'FASTP': ['fastp'], 'FASTQC': ['fastqc'], 'FQ_LINT': ['fq'],
 'FQ_SUBSAMPLE': ['fq'], 'GFFREAD': ['gffread'], 'GUNZIP': ['gunzip'], 'HISAT2_ALIGN': ['hisat2'], 'HISAT2_BUILD': ['hisat2'],
 'HISAT2_EXTRACTSPLICESITES': ['hisat2'], 'KALLISTO_INDEX': ['kallisto'], 'KALLISTO_QUANT': ['kallisto'], 'KRAKEN2_KRAKEN2': ['kraken2'],
 'MULTIQC': ['multiqc'], 'PARABRICKS_RNAFQ2BAM': ['parabricks_star'], 'PICARD_MARKDUPLICATES': ['picard'], 'PRESEQ_LCEXTRAP': ['preseq'],
 'QUALIMAP_RNASEQ': ['qualimap'], 'RIBODETECTOR': ['ribodetector'], 'RSEM_CALCULATEEXPRESSION': ['rsem'], 'RSEM_PREPAREREFERENCE': ['rsem'],
 'RSEQC_BAMSTAT': ['rseqc'], 'RSEQC_INFEREXPERIMENT': ['rseqc'], 'RSEQC_INNERDISTANCE': ['rseqc'], 'RSEQC_JUNCTIONANNOTATION': ['rseqc'],
 'RSEQC_JUNCTIONSATURATION': ['rseqc'], 'RSEQC_READDISTRIBUTION': ['rseqc'], 'RSEQC_READDUPLICATION': ['rseqc'], 'RSEQC_TIN': ['rseqc'],
 'RUSTQC': ['rustqc'], 'SALMON_INDEX': ['salmon'], 'SALMON_QUANT': ['salmon'], 'SAMTOOLS_FAIDX': ['samtools'], 'SAMTOOLS_FASTQ': ['samtools'],
 'SAMTOOLS_FLAGSTAT': ['samtools'], 'SAMTOOLS_IDXSTATS': ['samtools'], 'SAMTOOLS_INDEX': ['samtools'], 'SAMTOOLS_SORT': ['samtools'],
 'SAMTOOLS_STATS': ['samtools'], 'SAMTOOLS_VIEW': ['samtools'], 'SENTIEON_RSEMCALCULATEEXPRESSION': ['sentieon_rsem'],
 'SENTIEON_RSEMPREPAREREFERENCE': ['sentieon_rsem'], 'SENTIEON_STARALIGN': ['sentieon_star'], 'SEQKIT_REPLACE': ['seqkit'], 'SEQKIT_STATS': ['seqkit'],
 'SORTMERNA': ['sortmerna'], 'STAR_ALIGN': ['star'], 'STAR_GENOMEGENERATE': ['star'], 'STRINGTIE_MERGE': ['stringtie'],
 'STRINGTIE_STRINGTIE': ['stringtie'], 'SUBREAD_FEATURECOUNTS': ['featurecounts'], 'SUMMARIZEDEXPERIMENT_SUMMARIZEDEXPERIMENT': ['summarizedexperiment'],
 'SYLPH_PROFILE': ['sylph'], 'SYLPHTAX_TAXPROF': ['sylphtax'], 'TRIMGALORE': ['trimgalore'], 'TXIMETA_TXIMPORT': ['tximeta'],
 'UCSC_BEDCLIP': ['ucsc_bedclip'], 'UCSC_BEDGRAPHTOBIGWIG': ['ucsc_bedgraphtobigwig'], 'UMICOLLAPSE': ['umicollapse'],
 'UMITOOLS_DEDUP': ['umi_tools'], 'UMITOOLS_EXTRACT': ['umi_tools'], 'UMITOOLS_PREPAREFORRSEM': ['umi_tools'], 'UNTAR': ['untar'],
}

RNASEQ_RULES = {
    'callsite_infeasible': [{'dst_suffix': 'QUANTIFY_BAM_SALMON:KALLISTO_QUANT', 'reason': 'workflows/rnaseq/main.nf:461 QUANTIFY_BAM_SALMON is called with the literal "salmon"; its kallisto branch cannot run'}],
    'forbidden_flag_pairs': [{'a': 'use_parabricks_star', 'b': 'use_sentieon_star', 'reason': 'pipeline validation forbids --use_parabricks_star with --use_sentieon_star (subworkflows/local/utils_nfcore_rnaseq_pipeline/main.nf:323-325)'}],
    'multimap_note': 'workflows/rnaseq/main.nf:495-512 multiMap separates the bam and index branches; the analyzer unions them'}


def module_meta(repo, module_file):
    d = os.path.join(repo, os.path.dirname(module_file))
    tools, env = [], []
    try:
        m = yaml.safe_load(open(os.path.join(d, 'meta.yml'), encoding='utf-8')) or {}
        for t in m.get('tools') or []:
            tools += list(t.keys()) if isinstance(t, dict) else [str(t)]
    except Exception: pass
    try:
        y = yaml.safe_load(open(os.path.join(d, 'environment.yml'), encoding='utf-8')) or {}
        env = [re.sub(r'^.*::', '', x).split('=')[0] for x in y.get('dependencies', []) if isinstance(x, str)]
    except Exception: pass
    return tools, env

def topic_tools(outputs):
    res = []
    for o in outputs:
        if o['topic']:
            m = re.search(r"val\(\s*['\"]([^'\"]+)['\"]\s*\)\s*,\s*eval", o['decl'])
            if m: res.append(m.group(1))
    return res

def csvw(path, rows, cols):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader()
        for r in rows: w.writerow(r)

def dag_instances_and_edges(dag):
    """returns (instances, direct process->process edges via operator/channel nodes only, hub-free edges, hub node ids)"""
    inst = {}
    for n in dag['nodes']:
        if n['kind'] == 'process':
            inst[n['id']] = (n['scope'] + ':' + n['label']) if n['scope'] else n['label']
    adj = collections.defaultdict(list); radj = collections.defaultdict(list)
    for e in dag['edges']: adj[e['src']].append(e['dst']); radj[e['dst']].append(e['src'])
    def reach(start, graph, skip=()):
        seen = set(); stack = list(graph[start]); found = set()
        while stack:
            v = stack.pop()
            if v in seen or v in skip: continue
            seen.add(v)
            if v in inst: found.add(v)
            else: stack.extend(graph[v])
        return found
    def edges(skip=()):
        return {(inst[p], inst[q]) for p in inst for q in reach(p, adj, skip) if p not in skip}
    hubs = set()
    for n in dag['nodes']:
        if n['id'] in inst: continue
        if len(reach(n['id'], radj)) >= 2 and len(reach(n['id'], adj)) >= 2: hubs.add(n['id'])
    return set(inst.values()), edges(), edges(hubs), hubs

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--repo', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--profile', default='rnaseq', choices=['rnaseq', 'generic'], help='rnaseq = curated nf-core/rnaseq 3.27.0 software map and rules; generic = nothing pre-curated (software is auto-guessed and flagged UNREVIEWED)')
    ap.add_argument('--software-map', help='YAML overlay: primary: {MODULE: [keys]}, canon: {key: [name, role]}, alternative_of: {key: name}, callsite_infeasible: [...], forbidden_flag_pairs: [...]')
    a = ap.parse_args()
    RULES = dict(RNASEQ_RULES) if a.profile == 'rnaseq' else {'callsite_infeasible': [], 'forbidden_flag_pairs': [], 'multimap_note': payload_checks.MULTIMAP_NOTE}
    if a.profile == 'generic': CANON.clear(); PRIMARY.clear(); ALTERNATIVE_OF.clear()
    if a.software_map:
        ov = yaml.safe_load(open(a.software_map, encoding='utf-8')) or {}
        PRIMARY.update({k: list(v) for k, v in (ov.get('primary') or {}).items()}); CANON.update({k: tuple(v) for k, v in (ov.get('canon') or {}).items()})
        ALTERNATIVE_OF.update(ov.get('alternative_of') or {})
        for k in ('callsite_infeasible', 'forbidden_flag_pairs'): RULES[k] = RULES[k] + list(ov.get(k) or [])
    payload_checks.CALLSITE_INFEASIBLE = RULES['callsite_infeasible']; payload_checks.MULTIMAP_NOTE = RULES['multimap_note']
    out = a.out; proc = os.path.join(out, 'data', 'processed'); gr = os.path.join(out, 'data', 'graphs'); raw = os.path.join(out, 'data', 'raw')
    G = json.load(open(os.path.join(proc, 'static_graph.json')))
    insts = {i['path']: i for i in G['instances']}

    # ---- executed-in-config matrix from preview DAGs
    dagsets, dagedges, dagfree, daghubs, skipped = {}, {}, {}, {}, []
    for f in sorted(glob.glob(os.path.join(raw, '*_dag.html'))):
        label = os.path.basename(f)[:-9]
        try: d = parse_dag(f)
        except Exception: skipped.append(label); continue
        if not any(n['kind'] == 'process' for n in d['nodes']): skipped.append(label); continue   # failed run -> empty DAG
        json.dump(d, open(os.path.join(gr, f'{label}_dag_raw.json'), 'w'), indent=1)
        dagsets[label], dagedges[label], dagfree[label], daghubs[label] = dag_instances_and_edges(d)
    configs = sorted(dagsets)
    unknown_in_dag = {c: sorted(s - set(insts)) for c, s in dagsets.items()}

    # ---- process -> software mapping
    pmap, canon_used = [], {}
    for p, i in insts.items():
        if i['kind'] != 'process': continue
        tools, env = module_meta(a.repo, i['module_file'])
        tt = topic_tools(i['outputs'])
        prim = PRIMARY.get(i['module'])
        method = 'curated'
        if not prim:
            method = 'auto-from-environment-yml (UNREVIEWED)'
            helpers = {'htslib', 'coreutils', 'grep', 'gzip', 'lbzip2', 'sed', 'tar', 'pigz', 'python', 'r-base'}
            prim = [e for e in env if e not in helpers][:1] or tools[:1] or [i['module'].lower()]   # last resort: the module name itself
            for k in prim: CANON.setdefault(k, (k, 'unknown'))
        names = [CANON[k][0] for k in prim]
        for k in prim: canon_used[k] = CANON[k]
        sec = sorted(set(re.sub(r'-', '_', e) for e in env) - set(prim))
        notes = []
        if i['module'].startswith('RSEM') and 'rseqc' in tools: notes.append("meta.yml lists tool 'rseqc' (upstream metadata error); curated to RSEM")
        if i['module'] == 'RUSTQC': notes.append('RustQC (rustqc rna) is a distinct Rust re-implementation of RSeQC/dupRadar/featureCounts/Preseq/Qualimap-style QC, not RSeQC')
        pmap.append({'process_instance': p, 'process_module': i['module'], 'module_file': i['module_file'], 'module_line': i['module_line'],
                     'primary_software_keys': ';'.join(prim), 'primary_software': ';'.join(names),
                     'roles': ';'.join(CANON[k][1] for k in prim), 'alternative_of': ';'.join(ALTERNATIVE_OF.get(k, '') for k in prim).strip(';'),
                     'meta_yml_tools': ';'.join(tools), 'environment_yml_deps': ';'.join(env), 'topic_version_tools': ';'.join(tt),
                     'multi_tool_process': len(prim) > 1, 'mapping_method': method, 'notes': ' | '.join(n for n in notes if n)})
    pm = {r['process_instance']: r for r in pmap}
    csvw(os.path.join(proc, 'process_software_map.csv'), pmap, list(pmap[0].keys()))
    csvw(os.path.join(proc, 'canonical_software.csv'),
         [{'key': k, 'canonical_name': v[0], 'role': v[1], 'alternative_of': ALTERNATIVE_OF.get(k, '')} for k, v in sorted(canon_used.items())],
         ['key', 'canonical_name', 'role', 'alternative_of'])

    # ---- process edges with classification
    METADATA_EMITS = {'lib_format_counts', 'json_info', 'lint'}   # inferred strandedness / lint verdicts travel in meta or act as gates
    GATING_EMITS = re.compile(r'^(log|lint|stats|flagstat|idxstats|json|html|zip|tsv|txt|summary|report|metrics)', re.I)
    edges, evid, review = [], [], []
    for e in G['edges']:
        s, d = e['src_instance'], e['dst_instance']
        if s not in insts or d not in insts: continue
        ops = set(e['operators']); flags = list(e['flags'])
        dst_mod = insts[d]['module']
        if dst_mod == 'MULTIQC': cls = 'reporting-aggregation'
        elif any(f.startswith('key-only') for f in flags): cls = 'key-only-synchronization'
        elif (e['src_emit'] or '') in METADATA_EMITS: cls = 'metadata-dependency'
        elif GATING_EMITS.match(e['src_emit'] or '') and (ops & {'join', 'mix', 'combine', 'filter'}): cls = 'gating-or-metadata'
        elif ops & {'mix', 'join', 'combine', 'merge', 'cross', 'concat'}: cls = 'merged-channel'
        else: cls = 'direct'
        alt = 'alternative-branch-in-channel-path' in flags
        # confidence_v1: ORIGINAL rule, kept unchanged for comparison. Defect: any alternative-branch flag demoted a direct edge to medium
        if cls == 'direct' and not alt: conf = 'high'
        elif cls in ('direct', 'merged-channel', 'reporting-aggregation'): conf = 'medium'
        else: conf = 'low'
        # confidence_v2: corrected rule. Exclusive if/else branches are recorded as conditions and are not payload ambiguity; edges that the
        # payload check proves to be extractor artifacts (dropped tuple element, multiMap split, constant call argument) or that the pipeline
        # itself forbids (--use_parabricks_star with --use_sentieon_star, utils_nfcore_rnaseq_pipeline/main.nf:323-325) are 'rejected'.
        pv, pr = 'not-checked', ''   # payload check is defined for direct and merged-channel edges only
        if cls in ('direct', 'merged-channel'): pv, pr, _pf, _cf = payload_verdict({'src_emit': e['src_emit'] or '', 'src_output_decl': e['src_output_decl'], 'dst_input_decl': e['dst_input_decl'], 'dst_module': dst_mod,
                                            'dst_instance': d, 'channel_trail': e['channel_trail'], 'consumer_call': e['consumer_call'], 'src_module': insts[s]['module']}, a.repo)
        if pv in REJECT_VERDICTS: conf2, why2 = 'rejected', 'payload check: ' + pv
        elif cls in ('key-only-synchronization', 'metadata-dependency', 'gating-or-metadata'): conf2, why2 = 'low', 'no payload consumed (synchronisation / gate / metadata)'
        elif cls == 'direct': conf2, why2 = 'high', 'direct single-source path' + ('; exclusive alternative branches recorded as conditions' if alt else '')
        else: conf2, why2 = 'medium', cls + ' (payload check: ' + pv + ')'
        atoms = sorted({f'{k} {o} {v}' for c in (e['conditions_consumer'] + e['path_branch_conditions'] + e['conditions_producer']) for k, o, v in cond_atoms(c)})
        for fp in RULES['forbidden_flag_pairs']:
            if f"{fp['a']} truthy True" in atoms and f"{fp['b']} truthy True" in atoms: conf2, why2 = 'rejected', fp['reason']
        crosses = any(st['var'].startswith('emit:') for st in e['channel_trail'])
        ex = [c for c in configs if s in dagsets[c] and d in dagsets[c]]
        conf_by_dag = [c for c in ex if (s, d) in dagfree[c]]
        tier = 'A-dag-confirmed' if conf_by_dag else ('B-static-only' if cls in ('direct', 'merged-channel', 'reporting-aggregation') else 'C-review')
        row = {'edge_id': f'E{len(edges)+1:05d}', 'src_instance': s, 'src_module': insts[s]['module'], 'src_emit': e['src_emit'],
               'dst_instance': d, 'dst_module': dst_mod, 'dst_input_index': e['dst_input_index'], 'edge_class': cls, 'confidence_v1': conf, 'confidence_v2': conf2, 'confidence_v2_reason': why2, 'payload_check': pv, 'payload_check_detail': pr, 'evidence_tier': tier,
               'src_software': pm[s]['primary_software'], 'dst_software': pm[d]['primary_software'],
               'required_param_assumptions': ' & '.join(atoms), 'conditional': bool(e['conditions_consumer'] or e['conditions_producer'] or alt),
               'crosses_subworkflow_interface': crosses, 'operators': ';'.join(e['operators']),
               'consumer_call': e['consumer_call'], 'producer_call': e['producer_call'],
               'both_endpoints_in_configs': ';'.join(ex), 'confirmed_by_hubfree_dag_in': ';'.join(conf_by_dag)}
        edges.append(row)
        evid.append({**row, 'src_output_decl': e['src_output_decl'], 'dst_input_decl': e['dst_input_decl'],
                     'conditions_consumer': e['conditions_consumer'], 'conditions_producer': e['conditions_producer'],
                     'path_branch_conditions': e['path_branch_conditions'], 'channel_trail': e['channel_trail'], 'flags': flags,
                     'src_module_file': f"{insts[s]['module_file']}:{insts[s]['module_line']}", 'dst_module_file': f"{insts[d]['module_file']}:{insts[d]['module_line']}"})
        if conf2 == 'low':
            review.append({'edge_id': row['edge_id'], 'reason': cls + ': synchronisation/metadata dependency, payload not (fully) consumed; exclude from positive control unless verified', 'src': s, 'emit': e['src_emit'], 'dst': d, 'call': e['consumer_call']})
    cols = list(edges[0].keys())
    csvw(os.path.join(proc, 'process_edges.csv'), edges, cols)
    with open(os.path.join(proc, 'process_edges_evidence.jsonl'), 'w') as f:
        for r in evid: f.write(json.dumps(r) + '\n')

    # unique process pair table (collapsing emits)
    pairs = collections.OrderedDict()
    for r in edges:
        k = (r['src_instance'], r['dst_instance'])
        q = pairs.setdefault(k, {'src_instance': k[0], 'dst_instance': k[1], 'emits': set(), 'classes': set(), 'confidences': set(), 'edge_ids': []})
        q['emits'].add(r['src_emit']); q['classes'].add(r['edge_class']); q['confidences'].add(r['confidence_v2']); q['edge_ids'].append(r['edge_id'])
    rank = {'high': 3, 'medium': 2, 'low': 1, 'rejected': 0}
    pair_rows = [{'src_instance': q['src_instance'], 'dst_instance': q['dst_instance'], 'emits': ';'.join(sorted(q['emits'])),
                  'classes': ';'.join(sorted(q['classes'])), 'best_confidence': max(q['confidences'], key=rank.get), 'n_edges': len(q['edge_ids'])} for q in pairs.values()]
    csvw(os.path.join(proc, 'process_pairs.csv'), pair_rows, list(pair_rows[0].keys()))

    # ---- process instances table
    irows = []
    for p, i in insts.items():
        r = {'instance': p, 'kind': i['kind'], 'module': i['module'], 'module_file': f"{i['module_file']}:{i['module_line']}",
             'call_site': f"{i['call_file']}:{i['call_line']}", 'conditions': ' && '.join(i['conds']),
             'primary_software': pm.get(p, {}).get('primary_software', ''),
             'executed_in': ';'.join(c for c in configs if p in dagsets[c])}
        irows.append(r)
    csvw(os.path.join(proc, 'process_instances.csv'), irows, list(irows[0].keys()))
    csvw(os.path.join(proc, 'executed_matrix.csv'),
         [{'instance': p, **{c: int(p in dagsets[c]) for c in configs}} for p, i in insts.items() if i['kind'] == 'process'], ['instance'] + configs)

    # ---- software-level graph (collapse AFTER keeping process identities)
    sw = {}
    for r in edges:
        for sk in pm[r['src_instance']]['primary_software_keys'].split(';'):
            for dk in pm[r['dst_instance']]['primary_software_keys'].split(';'):
                q = sw.setdefault((sk, dk), {'src': CANON[sk][0], 'dst': CANON[dk][0], 'src_key': sk, 'dst_key': dk, 'n': 0, 'cls': collections.Counter(),
                                              'conf': collections.Counter(), 'ex': set(), 'p': [], 'cond': 0})
                q['n'] += 1; q['cls'][r['edge_class']] += 1; q['conf'][r['confidence_v2']] += 1
                q['cond'] += int(r['conditional'])
                if len(q['p']) < 6: q['p'].append(r['edge_id'])
                for c in r['both_endpoints_in_configs'].split(';'):
                    if c: q['ex'].add(c)
    srows = []
    for (sk, dk), q in sorted(sw.items()):
        srows.append({'src_software': q['src'], 'dst_software': q['dst'], 'self_loop': sk == dk, 'n_supporting_process_edges': q['n'],
                      'classes': ';'.join(f'{k}:{v}' for k, v in sorted(q['cls'].items())), 'confidence_counts': ';'.join(f'{k}:{v}' for k, v in sorted(q['conf'].items())),
                      'best_confidence': max(q['conf'], key=rank.get), 'only_reporting': set(q['cls']) == {'reporting-aggregation'},
                      'conditional_fraction': round(q['cond'] / q['n'], 2), 'observed_in_preview_configs': ';'.join(sorted(q['ex'])),
                      'example_edge_ids': ';'.join(q['p']), 'src_role': CANON[sk][1], 'dst_role': CANON[dk][1]})
    csvw(os.path.join(proc, 'software_edges.csv'), srows, list(srows[0].keys()))
    csvw(os.path.join(proc, 'software_nodes.csv'),
         [{'key': k, 'canonical_name': v[0], 'role': v[1], 'alternative_of': ALTERNATIVE_OF.get(k, ''),
           'n_process_instances': sum(1 for r in pmap if k in r['primary_software_keys'].split(';'))} for k, v in sorted(canon_used.items())],
         ['key', 'canonical_name', 'role', 'alternative_of', 'n_process_instances'])

    # ---- validation of static vs DAG
    cmp = {}
    static_pairs = set(pairs)
    for c in configs:
        sp = {k for k in static_pairs if k[0] in dagsets[c] and k[1] in dagsets[c]}
        dg = dagedges[c]; dgf = dagfree[c]
        cmp[c] = {'dag_process_nodes': len(dagsets[c]), 'dag_instances_not_in_static': unknown_in_dag[c][:20], 'dag_process_edges': len(dg),
                  'static_pairs_with_both_endpoints_in_dag': len(sp), 'common': len(sp & dg), 'dag_only': len(dg - sp), 'static_only': len(sp - dg),
                  'dag_hubs_n': len(daghubs[c]), 'dag_edges_hubfree': len(dgf), 'dag_edges_requiring_hub': len(dg - dgf),
                  'static_pairs_confirmed_by_hubfree_dag': len(sp & dgf), 'dag_only_hubfree': len((dgf) - sp),
                  'dag_only_examples': sorted(f'{x[0]} -> {x[1]}' for x in (dg - sp))[:15], 'static_only_examples': sorted(f'{x[0]} -> {x[1]}' for x in (sp - dg))[:15]}
    cmp['_skipped_empty_or_failed_dags'] = skipped
    json.dump(cmp, open(os.path.join(proc, 'dag_vs_static.json'), 'w'), indent=1)
    csvw(os.path.join(proc, 'manual_review.csv'), review, ['edge_id', 'reason', 'src', 'emit', 'dst', 'call'])

    # ---- graphs
    import networkx as nx
    PG = nx.MultiDiGraph()
    for p, i in insts.items():
        if i['kind'] == 'process': PG.add_node(p, module=i['module'], software=pm[p]['primary_software'], conditional=bool(i['conds']))
    for r in edges: PG.add_edge(r['src_instance'], r['dst_instance'], key=r['edge_id'], emit=r['src_emit'], edge_class=r['edge_class'], confidence=r['confidence_v2'])
    nx.write_graphml(PG, os.path.join(gr, 'process_graph.graphml'))
    SG = nx.DiGraph()
    for k, v in canon_used.items(): SG.add_node(v[0], role=v[1])
    for r in srows: SG.add_edge(r['src_software'], r['dst_software'], n=r['n_supporting_process_edges'], confidence=r['best_confidence'], self_loop=r['self_loop'])
    nx.write_graphml(SG, os.path.join(gr, 'software_graph.graphml'))
    nonloop = nx.DiGraph([(u, v) for u, v in SG.edges if u != v])
    stats = {'process_instances': PG.number_of_nodes(), 'process_edges(emit-level)': PG.number_of_edges(), 'process_pairs': len(pairs),
             'software_nodes': SG.number_of_nodes(), 'software_edges_total': SG.number_of_edges(), 'software_self_loops': sum(1 for u, v in SG.edges if u == v),
             'static_process_graph_sccs>1': [sorted(c) for c in nx.strongly_connected_components(nx.DiGraph(PG)) if len(c) > 1],
             'software_graph_sccs>1': [sorted(c) for c in nx.strongly_connected_components(nonloop) if len(c) > 1],
             'edge_class_counts': dict(collections.Counter(r['edge_class'] for r in edges)),
             'confidence_counts': dict(collections.Counter(r['confidence_v2'] for r in edges))}
    json.dump(stats, open(os.path.join(proc, 'summary_stats.json'), 'w'), indent=1)
    json.dump({'process_nodes': [{'id': p, **{k: v for k, v in PG.nodes[p].items()}} for p in PG.nodes], 'process_edges': evid,
               'software_nodes': [{'id': n, **SG.nodes[n]} for n in SG.nodes], 'software_edges': srows},
              open(os.path.join(gr, 'full_graph.json'), 'w'))
    print(json.dumps({k: v for k, v in stats.items() if not k.endswith('sccs>1')}, indent=1))
    print('process SCCs:', len(stats['static_process_graph_sccs>1']), ' software SCCs:', stats['software_graph_sccs>1'])

if __name__ == '__main__': main()
