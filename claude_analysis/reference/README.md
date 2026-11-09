# nf-core/rnaseq 3.27.0 – directed software-relationship reference dataset (frozen)

A reference set of **directed software relationships** extracted from the nf-core/rnaseq workflow code, with positive controls, negative controls and unresolved cases, each backed by process-level evidence and source file:line references.

**Definition.** Software A → B means: data produced by a process that runs A is consumed, as an input channel of a process that runs B. Not inferred from source order, diagram proximity, shared workflow membership, co-occurrence or shared inputs; no transitive closure.

| | |
|---|---|
| Pipeline | nf-core/rnaseq **3.27.0**, commit `a1fcdddd3b826fe46eb46f0479f2ff8a7815af05` (see `MANIFEST.json`) |
| Analysis | local, static (Nextflow source + `nextflow -preview` DAGs); **no workflow was executed** |
| Original nf-core files | unchanged |
| Validation | `VALIDATION_SUMMARY.md` (machine-readable: `validation.json`) |
| Integrity | `SHA256SUMS`, `MANIFEST.json` |

## Which file do I use?

Software level (`software_level/`, one row per ordered software pair):

| file | records | meaning |
|---|---|---|
| `gold_positive_controls.csv` | 29 | source-code-verified, both ends named tools. **Use as ground truth.** |
| `silver_positive_controls.csv` | 22 | source-code-verified real data flow, but an end is a generic utility / local script (tar, gzip, sed, nf-core custom Python scripts) or only part of the payload is used |
| `negative_controls_verified.csv` | 19 | source-code-verified: not a data exchange (2 extractor false positives, 17 read-in-source absences) |
| `negative_candidates_unverified.csv` | 127 | algorithmically identified negatives (no path in the extracted graph, shared input, reverse of a verified flow, rule-based artifacts). **Not verified one by one.** |
| `unresolved_gate_metadata.csv` | 37 | the only extracted edges are gates or metadata (e.g. percent-mapped filter, inferred strandedness); whether that counts as data is a definition choice |
| `algorithmic_supported_pairs.csv` | 282 | produced by the extraction and not rejected, **not individually adjudicated** (includes 14 self-loops and 31 reporting-only pairs). Not controls. |
| `software_relationships_all.csv` / `.parquet` | 516 | all of the above, column `category` |

Process level (`process_level/`, one row per process-instance edge; 1,234 edges):

| `validation_category` | records | meaning |
|---|---|---|
| `source_verified_positive` | 115 | supporting edges of the Gold/Silver pairs (call site and input slot read in source) |
| `source_verified_negative` | 5 | verified extractor artifacts / infeasible paths |
| `algorithmic_supported` | 814 | extracted, not rejected, not individually read |
| `algorithmic_negative_candidate` | 172 | rejected by the payload check (78 edges) or key-only synchronisation (94 edges) |
| `unresolved` | 128 | gate / metadata edges |

`process_relationships_all.csv` (+ `.parquet`) holds all rows; the five other CSVs are subsets. Software rows list their `process_edge_ids`, so every software pair can be traced to its edges, processes, operations and `file:line`.

## Quick start (Python)

```python
import pandas as pd
sw = pd.read_csv("claude_analysis/reference/software_level/software_relationships_all.csv")
gold = sw[sw.category == "Gold"]
neg  = sw[sw.category == "Negative_verified"]
pe   = pd.read_csv("claude_analysis/reference/process_level/process_relationships_all.csv")
edges_of_pair = pe[pe.edge_id.isin(gold.iloc[0].process_edge_ids.split(";"))]
```

## Reproduce from a clean checkout

```bash
git clone --branch claude/directed-software-analysis-3.27.0 https://github.com/kbobryshava/rnaseq.git
cd rnaseq
pip install -r claude_analysis/requirements.txt          # Python >= 3.10 (3.13 used)
bash claude_analysis/scripts/reproduce_all.sh             # ~1 min, pure Python
cd claude_analysis/reference && sha256sum -c SHA256SUMS   # byte-identical CSVs/reports
```
Re-generating the preview DAGs (`--with-previews`) additionally needs Java 17 and Nextflow (they were produced with Nextflow 26.10.5 in WSL); the committed DAGs in `data/raw/` are the recorded inputs (hashes in `MANIFEST.json`).

## Read this before using it as a benchmark

* Gold/Silver mean **verified by reading the source for the stated parameters**, not observed running. Many pairs are conditional (`required_params`): Parabricks, Sentieon, UMI, kallisto, `--additional_fasta`, Kraken/Bracken.
* **Software identity ≠ operation performed.** Always read `source_operations` / `target_operations`. Example: *RSEM → kallisto* is `rsem-prepare-reference` used only to extract the transcriptome FASTA that `kallisto index` consumes; it has nothing to do with RSEM quantification.
* Software nodes collapse several processes (SAMtools: 9 operations; "nf-core custom script (Python)": several distinct scripts). Software-level graphs contain cycles that do not exist at process level (the process graph is acyclic).
* The positive set is **not complete** (e.g. STAR → Salmon via the transcriptome BAM is real but only `algorithmic_supported`). It is a precision-oriented control set, not a recall estimate.
* Unverified negatives assert absence of a path in the *extracted* graph.
* One reviewer (an AI assistant working from the source); no independent human second review yet. See `METHODOLOGY.md` §8.
