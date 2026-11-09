#!/usr/bin/env python3
"""Tiny helper: python query_edges.py <graph.json> <src-regex|-> <dst-regex|->"""
import json, re, sys
g = json.load(open(sys.argv[1])); sr = re.compile(sys.argv[2] if sys.argv[2] != '-' else '.'); dr = re.compile(sys.argv[3] if sys.argv[3] != '-' else '.')
for e in g['edges']:
    if sr.search(e['src_instance']) and dr.search(e['dst_instance']):
        print(f"{e['src_instance'].split(':')[-1]}.{e['src_emit']} -> {e['dst_instance'].split(':')[-1]}#{e['dst_input_index']} | {e['dst_instance']} | ops={e['operators']} | {e['flags']} | br={e['path_branch_conditions']}")
