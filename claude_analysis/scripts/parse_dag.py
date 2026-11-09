#!/usr/bin/env python3
"""Parse a Nextflow `-with-dag` HTML (Mermaid flowchart) into nodes/edges JSON.

Node kinds (by Mermaid shape, verified against Nextflow 26.10.5 output):
  v1(["NAME"])  -> process
  v1(( ))       -> operator (anonymous circle)
  v1["label"]   -> channel / value source (e.g. channel.of, ch_fasta) or sink
Subgraph titles carry the fully-qualified workflow scope: "scope [LABEL]".
"""
import re, json, sys, pathlib

NODE = re.compile(r'^\s*(v\d+)(\(\[|\(\(|\[|\()\s*"?(.*?)"?\s*(\]\)|\)\)|\]|\))\s*$')
EDGE = re.compile(r'^\s*(v\d+)\s*-->(?:\|"?(.*?)"?\|)?\s*(v\d+)\s*$')
SUB = re.compile(r'^\s*subgraph\s+"(.*)"\s*$')

def parse(path):
    txt = pathlib.Path(path).read_text(encoding="utf-8")
    m = re.search(r'<pre class="mermaid"[^>]*>(.*?)</pre>', txt, re.S)
    body = m.group(1)
    nodes, edges, stack = {}, [], []
    for ln in body.splitlines():
        s = SUB.match(ln)
        if s:
            stack.append(s.group(1).split(" [")[0].strip()); continue
        if ln.strip() == "end":
            stack.pop(); continue
        n = NODE.match(ln)
        if n:
            vid, op, label, _ = n.groups()
            kind = {"([": "process", "((": "operator", "[": "channel", "(": "operator"}[op]
            nodes[vid] = {"id": vid, "kind": kind, "label": label.strip(),
                          "scope": stack[-1] if stack else "", "scope_path": list(stack)}
            continue
        e = EDGE.match(ln)
        if e:
            edges.append({"src": e.group(1), "dst": e.group(3), "channel_label": e.group(2) or ""})
    return {"source_file": str(path), "nodes": list(nodes.values()), "edges": edges}

if __name__ == "__main__":
    g = parse(sys.argv[1])
    pathlib.Path(sys.argv[2]).write_text(json.dumps(g, indent=1))
    k = {}
    for n in g["nodes"]: k[n["kind"]] = k.get(n["kind"], 0) + 1
    print(len(g["nodes"]), "nodes", k, len(g["edges"]), "edges")
